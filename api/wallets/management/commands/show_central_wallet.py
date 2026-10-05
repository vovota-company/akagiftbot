from django.core.management.base import BaseCommand
from api.wallets.services import central_wallet

class Command(BaseCommand):
    help = 'Show the derived central wallet. Private key is hidden unless --show-private-key is explicitly supplied.'

    def add_arguments(self, parser):
        parser.add_argument('--show-private-key', action='store_true')

    def handle(self, *args, **options):
        wallet = central_wallet()
        self.stdout.write(f"address={wallet['address']}")
        self.stdout.write("derivation_path=m/44'/60'/0'/0/" + str(wallet['derivation_index']))
        if options['show_private_key']:
            self.stdout.write('private_key=0x' + wallet['private_key'].hex())
        else:
            self.stdout.write(self.style.WARNING('private_key=hidden (use --show-private-key only in a controlled secure terminal)'))
