import os

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from core_admin.models import Admin


class Command(BaseCommand):
    help = "Create/update the custom core_admin.Admin user from env vars (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            help="Admin email (defaults to ADMIN_EMAIL env var)",
        )
        parser.add_argument(
            "--password",
            help="Admin password (defaults to ADMIN_PASSWORD env var)",
        )
        parser.add_argument(
            "--update-password",
            action="store_true",
            help="If set, updates password even if admin already exists.",
        )

    def handle(self, *args, **options):
        email = (options.get("email") or os.getenv("ADMIN_EMAIL") or "").strip()
        password = options.get("password") or os.getenv("ADMIN_PASSWORD") or ""
        update_password = bool(options.get("update_password"))

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Skipping admin bootstrap: ADMIN_EMAIL/ADMIN_PASSWORD not provided."
                )
            )
            return

        admin, created = Admin.objects.get_or_create(
            email=email,
            defaults={"password": make_password(password), "is_active": True},
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created admin: {email}"))
            return

        if update_password:
            admin.password = make_password(password)
            admin.is_active = True
            admin.save(update_fields=["password", "is_active", "updated_at"])
            self.stdout.write(self.style.SUCCESS(f"Updated admin password: {email}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Admin already exists: {email}"))
