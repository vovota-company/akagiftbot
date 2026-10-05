import logging
from decimal import Decimal
from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone
from web3 import Web3
from web3._utils.events import get_event_data
from web3.exceptions import TransactionNotFound
from api.wallets.models import Wallet
from api.wallets.services import central_wallet, private_key_for_wallet
from .models import BlockchainState, Transaction, LedgerEntry

logger = logging.getLogger('api')

ERC20_ABI = [
    {'anonymous': False, 'inputs': [
        {'indexed': True, 'name': 'from', 'type': 'address'},
        {'indexed': True, 'name': 'to', 'type': 'address'},
        {'indexed': False, 'name': 'value', 'type': 'uint256'}], 'name': 'Transfer', 'type': 'event'},
    {'inputs': [], 'name': 'decimals', 'outputs': [{'name': '', 'type': 'uint8'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [{'name': 'account', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [{'name': 'to', 'type': 'address'}, {'name': 'value', 'type': 'uint256'}], 'name': 'transfer', 'outputs': [{'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'},
]


def web3_client():
    if not settings.BSC_RPC_URL:
        raise RuntimeError('BSC_RPC_URL is not configured.')
    w3 = Web3(Web3.HTTPProvider(settings.BSC_RPC_URL, request_kwargs={'timeout': 30}))
    if not w3.is_connected():
        raise RuntimeError('Unable to connect to BSC RPC.')
    return w3


def usdt_contract(w3):
    return w3.eth.contract(address=Web3.to_checksum_address(settings.USDT_CONTRACT_ADDRESS), abi=ERC20_ABI)


def _state():
    state, _ = BlockchainState.objects.get_or_create(network='bsc')
    return state


def scan_transfers_once():
    w3 = web3_client()
    current = w3.eth.block_number
    state = _state()
    start = state.last_scanned_block + 1
    if start > current:
        return 0
    end = min(start + settings.BLOCK_SCAN_BATCH - 1, current)
    wallets = {w.address.lower(): w for w in Wallet.objects.select_related('user').filter(status=Wallet.STATUS_ACTIVE)}
    if not wallets:
        state.last_scanned_block = end
        state.save(update_fields=['last_scanned_block','updated_at'])
        return 0
    topic0 = Web3.keccak(text='Transfer(address,address,uint256)').hex()
    logs = w3.eth.get_logs({'fromBlock': start, 'toBlock': end, 'address': Web3.to_checksum_address(settings.USDT_CONTRACT_ADDRESS), 'topics': [topic0]})
    found = 0
    for raw in logs:
        # indexed topics: from, to; data: value
        if len(raw['topics']) < 3:
            continue
        to_address = Web3.to_checksum_address('0x' + raw['topics'][2].hex()[-40:])
        wallet = wallets.get(to_address.lower())
        if not wallet:
            continue
        value = int.from_bytes(raw['data'], 'big') if isinstance(raw['data'], bytes) else int(raw['data'], 16)
        amount = Decimal(value) / (Decimal(10) ** settings.USDT_DECIMALS)
        tx_hash = raw['transactionHash'].hex()
        log_index = int(raw['logIndex'])
        with db_transaction.atomic():
            obj, created = Transaction.objects.get_or_create(
                tx_hash=tx_hash,
                log_index=log_index,
                type=Transaction.TYPE_DEPOSIT,
                defaults={
                    'user': wallet.user,
                    'wallet': wallet,
                    'amount': amount,
                    'network': 'bsc',
                    'asset': 'USDT',
                    'block_number': int(raw['blockNumber']),
                    'confirmations': 0,
                    'status': Transaction.STATUS_DETECTED,
                },
            )
            if created:
                found += 1
                logger.info('Detected deposit %s for %s amount=%s', tx_hash, wallet.user.email, amount)
    state.last_scanned_block = end
    state.save(update_fields=['last_scanned_block','updated_at'])
    return found


def update_confirmations_and_collect():
    w3 = web3_client()
    head = w3.eth.block_number
    required = settings.CONFIRMATIONS_REQUIRED
    pending = Transaction.objects.filter(type=Transaction.TYPE_DEPOSIT).exclude(status=Transaction.STATUS_COLLECTED)
    for tx in pending:
        confirmations = max(0, head - tx.block_number + 1)
        if confirmations < required:
            if tx.confirmations != confirmations:
                tx.confirmations = confirmations
                tx.save(update_fields=['confirmations','updated_at'])
            continue
        if tx.status == Transaction.STATUS_DETECTED:
            tx.status = Transaction.STATUS_CONFIRMED
            tx.confirmations = confirmations
            tx.save(update_fields=['status','confirmations','updated_at'])
        if tx.status in (Transaction.STATUS_CONFIRMED, Transaction.STATUS_PROCESSING):
            collect_deposit(tx)


def _build_signed_tx(w3, account, tx_params):
    signed = w3.eth.account.sign_transaction(tx_params, account.key)
    return w3.eth.send_raw_transaction(signed.raw_transaction)


def _ensure_bnb_gas(w3, user_address):
    balance = w3.eth.get_balance(user_address)
    min_wei = w3.to_wei(Decimal(str(settings.MIN_USER_BNB)), 'ether')
    if balance >= min_wei:
        return None
    if not settings.AUTO_GAS_TOPUP:
        raise RuntimeError('User wallet has insufficient BNB gas and AUTO_GAS_TOPUP is disabled.')
    central = central_wallet()
    central_balance = w3.eth.get_balance(central['address'])
    amount = w3.to_wei(Decimal(str(settings.GAS_TOPUP_BNB)), 'ether')
    if central_balance < amount:
        raise RuntimeError('Central wallet has insufficient BNB for gas top-up.')
    nonce = w3.eth.get_transaction_count(central['address'], 'pending')
    tx = {
        'chainId': settings.BSC_CHAIN_ID,
        'nonce': nonce,
        'to': Web3.to_checksum_address(user_address),
        'value': amount,
        'gas': 21000,
        'gasPrice': w3.eth.gas_price,
    }
    signed = w3.eth.account.sign_transaction(tx, private_key=central['private_key'])
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt.status != 1:
        raise RuntimeError('BNB gas top-up transaction failed.')
    logger.info('Gas top-up sent %s -> %s', tx_hash.hex(), user_address)
    return tx_hash.hex()


def collect_deposit(deposit):
    w3 = web3_client()
    wallet = deposit.wallet
    try:
        with db_transaction.atomic():
            locked = Transaction.objects.select_for_update().get(pk=deposit.pk)
            if locked.status == Transaction.STATUS_COLLECTED:
                return locked
            locked.status = Transaction.STATUS_PROCESSING
            locked.save(update_fields=['status','updated_at'])

        gas_hash = _ensure_bnb_gas(w3, wallet.address)
        if gas_hash:
            Transaction.objects.get_or_create(
                tx_hash=gas_hash,
                log_index=0,
                type=Transaction.TYPE_GAS_TOPUP,
                defaults={'user': wallet.user, 'wallet': wallet, 'asset': 'BNB', 'network': 'bsc', 'amount': Decimal(str(settings.GAS_TOPUP_BNB)), 'block_number': w3.eth.block_number, 'status': Transaction.STATUS_CONFIRMED},
            )

        contract = usdt_contract(w3)
        balance_raw = contract.functions.balanceOf(wallet.address).call()
        if balance_raw <= 0:
            raise RuntimeError('No USDT balance remains in the user wallet.')
        central = central_wallet()
        nonce = w3.eth.get_transaction_count(wallet.address, 'pending')
        gas_price = w3.eth.gas_price
        gas_estimate = contract.functions.transfer(central['address'], balance_raw).estimate_gas({'from': wallet.address})
        tx = contract.functions.transfer(central['address'], balance_raw).build_transaction({
            'chainId': settings.BSC_CHAIN_ID,
            'nonce': nonce,
            'gas': int(gas_estimate * 1.2),
            'gasPrice': gas_price,
        })
        signed = w3.eth.account.sign_transaction(tx, private_key_for_wallet(wallet))
        sweep_hash = w3.eth.send_raw_transaction(signed.raw_transaction).hex()
        with db_transaction.atomic():
            locked = Transaction.objects.select_for_update().get(pk=deposit.pk)
            locked.status = Transaction.STATUS_COLLECTED
            locked.collected_tx_hash = sweep_hash
            locked.error_message = ''
            locked.save(update_fields=['status','collected_tx_hash','error_message','updated_at'])
            LedgerEntry.objects.get_or_create(transaction=locked, account='user_deposit', user=wallet.user, direction='credit', defaults={'asset':'USDT','amount':locked.amount})
            LedgerEntry.objects.get_or_create(transaction=locked, account='central_wallet_pending', user=wallet.user, direction='debit', defaults={'asset':'USDT','amount':locked.amount})
            Transaction.objects.get_or_create(
                tx_hash=sweep_hash,
                log_index=0,
                type=Transaction.TYPE_SWEEP,
                defaults={'user': wallet.user, 'wallet': wallet, 'asset':'USDT', 'network':'bsc', 'amount':Decimal(balance_raw)/(Decimal(10)**settings.USDT_DECIMALS), 'block_number':w3.eth.block_number, 'status':Transaction.STATUS_CONFIRMED},
            )
        logger.info('Collected deposit %s with sweep %s', deposit.tx_hash, sweep_hash)
        return deposit
    except Exception as exc:
        logger.exception('Collection failed for %s', deposit.tx_hash)
        Transaction.objects.filter(pk=deposit.pk).update(status=Transaction.STATUS_FAILED, error_message=str(exc)[:2000])
        return deposit
