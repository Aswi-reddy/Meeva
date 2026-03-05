from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import PasswordResetOTP


class Command(BaseCommand):
    help = "Delete expired PasswordResetOTP rows (hygiene task)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many rows would be deleted without deleting.",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        qs = PasswordResetOTP.objects.filter(expires_at__lt=now)
        count = qs.count()

        if options.get("dry_run"):
            self.stdout.write(self.style.SUCCESS(f"Expired OTPs to delete: {count}"))
            return

        deleted, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted expired OTPs: {deleted}"))
