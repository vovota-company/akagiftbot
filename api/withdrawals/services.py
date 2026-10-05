from decimal import Decimal

from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone
from web3 import Web3

from api.deposits.models import LedgerEntry
from api.deposits.services import web3_client, usdt_contract
from api.wallets.services import central_wallet

from .models import Withdrawal


def user_available_balance(user):
    """
    Calculate the user's available USDT balance.

    Deposits are credited to the user ledger.
    Pending/processing withdrawals are reserved and therefore excluded
    from the available balance.
    """

    credits = (
        LedgerEntry.objects
        .filter(
            user=user,
            asset="USDT",
            direction="credit",
            account="user_deposit",
        )
        .values_list("amount", flat=True)
    )

    total_credits = sum(
        (Decimal(str(amount)) for amount in credits),
        Decimal("0"),
    )

    completed_withdrawals = (
        Withdrawal.objects
        .filter(
            user=user,
            asset=Withdrawal.ASSET_USDT,
            status=Withdrawal.STATUS_COMPLETED,
        )
        .values_list("amount", flat=True)
    )

    total_withdrawals = sum(
        (Decimal(str(amount)) for amount in completed_withdrawals),
        Decimal("0"),
    )

    pending_withdrawals = (
        Withdrawal.objects
        .filter(
            user=user,
            asset=Withdrawal.ASSET_USDT,
            status__in=[
                Withdrawal.STATUS_PENDING,
                Withdrawal.STATUS_PROCESSING,
            ],
        )
        .values_list("amount", flat=True)
    )

    total_pending = sum(
        (Decimal(str(amount)) for amount in pending_withdrawals),
        Decimal("0"),
    )

    available = (
        total_credits
        - total_withdrawals
        - total_pending
    )

    return max(available, Decimal("0")), total_pending


def create_withdrawal(user, amount, destination_address, idempotency_key):
    """
    Create a withdrawal request.

    The withdrawal is reserved by its pending status. The blockchain
    transfer is then performed from the central wallet.
    """

    existing = Withdrawal.objects.filter(
        idempotency_key=idempotency_key
    ).first()

    if existing:
        if existing.user_id != user.id:
            raise ValueError(
                "This idempotency key belongs to another user."
            )

        return existing

    amount = Decimal(str(amount))

    with db_transaction.atomic():
        available, _ = user_available_balance(user)

        if amount > available:
            raise ValueError(
                f"Insufficient USDT balance. "
                f"Available: {available}"
            )

        withdrawal = Withdrawal.objects.create(
            user=user,
            asset=Withdrawal.ASSET_USDT,
            network=Withdrawal.NETWORK_BSC,
            amount=amount,
            destination_address=Web3.to_checksum_address(
                destination_address
            ),
            idempotency_key=idempotency_key,
            status=Withdrawal.STATUS_PENDING,
        )

    return withdrawal


def execute_withdrawal(withdrawal):
    """
    Send USDT from the central wallet to the external wallet.
    """

    with db_transaction.atomic():
        locked = (
            Withdrawal.objects
            .select_for_update()
            .get(pk=withdrawal.pk)
        )

        if locked.status == Withdrawal.STATUS_COMPLETED:
            return locked

        if locked.status == Withdrawal.STATUS_PROCESSING:
            return locked

        locked.status = Withdrawal.STATUS_PROCESSING
        locked.error_message = ""
        locked.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )

    try:
        w3 = web3_client()
        contract = usdt_contract(w3)
        central = central_wallet()

        amount_raw = int(
            Decimal(str(locked.amount))
            * (Decimal(10) ** settings.USDT_DECIMALS)
        )

        central_balance = contract.functions.balanceOf(
            central["address"]
        ).call()

        if central_balance < amount_raw:
            raise RuntimeError(
                "Central wallet has insufficient USDT balance."
            )

        nonce = w3.eth.get_transaction_count(
            central["address"],
            "pending",
        )

        gas_price = w3.eth.gas_price

        gas_estimate = contract.functions.transfer(
            locked.destination_address,
            amount_raw,
        ).estimate_gas(
            {
                "from": central["address"],
            }
        )

        tx = contract.functions.transfer(
            locked.destination_address,
            amount_raw,
        ).build_transaction(
            {
                "chainId": settings.BSC_CHAIN_ID,
                "nonce": nonce,
                "gas": int(gas_estimate * 1.2),
                "gasPrice": gas_price,
            }
        )

        signed = w3.eth.account.sign_transaction(
            tx,
            private_key=central["private_key"],
        )

        tx_hash = w3.eth.send_raw_transaction(
            signed.raw_transaction
        ).hex()

        receipt = w3.eth.wait_for_transaction_receipt(
            tx_hash,
            timeout=180,
        )

        if receipt.status != 1:
            raise RuntimeError(
                "USDT withdrawal transaction failed on-chain."
            )

        with db_transaction.atomic():
            locked = (
                Withdrawal.objects
                .select_for_update()
                .get(pk=locked.pk)
            )

            locked.status = Withdrawal.STATUS_COMPLETED
            locked.tx_hash = tx_hash
            locked.completed_at = timezone.now()
            locked.error_message = ""

            locked.save(
                update_fields=[
                    "status",
                    "tx_hash",
                    "completed_at",
                    "error_message",
                    "updated_at",
                ]
            )

            LedgerEntry.objects.create(
                transaction_id=None,
                user=locked.user,
                account="user_withdrawal",
                asset="USDT",
                amount=locked.amount,
                direction="debit",
            )

        return locked

    except Exception as exc:
        Withdrawal.objects.filter(
            pk=locked.pk
        ).update(
            status=Withdrawal.STATUS_FAILED,
            error_message=str(exc)[:2000],
        )

        raise
