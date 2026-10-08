from django.conf import settings
from django.db import transaction
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from web3 import Web3
from .models import Wallet

DERIVATION_PREFIX = "m/44'/60'/0'/0"


def _seed_bytes():
    if not settings.WALLET_MNEMONIC:
        raise RuntimeError('WALLET_MNEMONIC is not configured.')
    return Bip39SeedGenerator(settings.WALLET_MNEMONIC).Generate(settings.WALLET_PASSPHRASE)


def derive_wallet(index: int):
    seed = _seed_bytes()
    ctx = Bip44.FromSeed(seed, Bip44Coins.ETH)
    child = ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
    address = Web3.to_checksum_address(child.PublicKey().ToAddress())
    private_key = child.PrivateKey().Raw().ToBytes()
    return address, private_key


def central_wallet():
    address, private_key = derive_wallet(settings.CENTRAL_WALLET_INDEX)
    return {'address': address, 'private_key': private_key, 'derivation_index': settings.CENTRAL_WALLET_INDEX}


@transaction.atomic
def ensure_wallet_for_user(user):
    wallet = Wallet.objects.filter(user=user).first()
    if wallet:
        return wallet
    # SQLite's write lock plus the unique derivation index makes accidental duplicates fail closed.
    max_index = Wallet.objects.order_by('-derivation_index').values_list('derivation_index', flat=True).first()
    next_index = max(settings.CENTRAL_WALLET_INDEX + 1, (max_index + 1 if max_index is not None else 1))
    address, _ = derive_wallet(next_index)
    return Wallet.objects.create(user=user, derivation_index=next_index, address=address)


def private_key_for_wallet(wallet):
    return derive_wallet(wallet.derivation_index)[1]
