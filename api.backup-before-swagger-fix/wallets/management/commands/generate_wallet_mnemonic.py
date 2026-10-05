from django.core.management.base import BaseCommand
from bip_utils import Bip39MnemonicGenerator, Bip39WordsNum

class Command(BaseCommand):
    help = 'Generate a fresh 12-word BIP-39 mnemonic for WALLET_MNEMONIC.'

    def handle(self, *args, **options):
        mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
        self.stdout.write(str(mnemonic))
        self.stdout.write(self.style.WARNING('Store this secret securely. Anyone with it controls all derived wallets.'))
