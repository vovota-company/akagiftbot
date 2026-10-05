from django.core.management.base import BaseCommand
from django.conf import settings
from bip_utils import Bip39MnemonicValidator
from api.wallets.services import central_wallet

class Command(BaseCommand):
    help = 'Validate the configured BIP-39 mnemonic and print the central address.'

    def handle(self, *args, **options):
        if not settings.WALLET_MNEMONIC:
            raise SystemExit('WALLET_MNEMONIC is not configured.')
        if not Bip39MnemonicValidator().IsValid(settings.WALLET_MNEMONIC):
            raise SystemExit('WALLET_MNEMONIC is not a valid BIP-39 mnemonic.')
        wallet = central_wallet()
        self.stdout.write(self.style.SUCCESS('Wallet configuration is valid.'))
        self.stdout.write(f"central_address={wallet['address']}")
