import time
from django.conf import settings
from django.core.management.base import BaseCommand
from api.deposits.services import scan_transfers_once, update_confirmations_and_collect

class Command(BaseCommand):
    help = 'Poll BSC USDT Transfer logs, confirm deposits, and sweep them to the central wallet.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting BSC deposit monitor'))
        while True:
            try:
                found = scan_transfers_once()
                update_confirmations_and_collect()
                if found:
                    self.stdout.write(f'Detected {found} deposit(s).')
            except KeyboardInterrupt:
                self.stdout.write('Stopping deposit monitor.')
                break
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'Monitor error: {exc}'))
            time.sleep(settings.POLL_SECONDS)
