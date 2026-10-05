from django.core.management.base import BaseCommand

from api.assets.services import rebuild_referral_stats


class Command(BaseCommand):
    help = "Rebuild referral statistics and user levels."

    def handle(self, *args, **options):
        rebuild_referral_stats()

        self.stdout.write(
            self.style.SUCCESS(
                "Referral tree rebuilt successfully."
            )
        )
