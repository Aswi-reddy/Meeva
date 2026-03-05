import os
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create/update a Django superuser from env vars (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            help="Superuser username (defaults to DJANGO_SUPERUSER_USERNAME env var)",
        )
        parser.add_argument(
            "--email",
            help="Superuser email (defaults to DJANGO_SUPERUSER_EMAIL env var)",
        )
        parser.add_argument(
            "--password",
            help="Superuser password (defaults to DJANGO_SUPERUSER_PASSWORD env var)",
        )
        parser.add_argument(
            "--update-password",
            action="store_true",
            help="If set, updates password even if user already exists.",
        )

    def handle(self, *args, **options):
        username = (options.get("username") or os.getenv("DJANGO_SUPERUSER_USERNAME") or "").strip()
        email = (options.get("email") or os.getenv("DJANGO_SUPERUSER_EMAIL") or "").strip().lower()
        password = options.get("password") or os.getenv("DJANGO_SUPERUSER_PASSWORD") or ""
        update_password = bool(options.get("update_password"))

        if not username:
            if email:
                base = email.split("@", 1)[0]
                base = re.sub(r"[^a-zA-Z0-9_\-\.]+", "", base) or "meeva"
                username = f"{base}_admin"
            else:
                username = "meeva_superadmin"

        if not password:
            self.stdout.write(
                self.style.WARNING(
                    "Skipping superuser bootstrap: DJANGO_SUPERUSER_PASSWORD not provided."
                )
            )
            return

        User = get_user_model()

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f"Created Django superuser: {username}"))
            return

        # Ensure flags are correct even if user pre-existed.
        updates = []
        if email and getattr(user, "email", "") != email:
            user.email = email
            updates.append("email")
        if not user.is_active:
            user.is_active = True
            updates.append("is_active")
        if not user.is_staff:
            user.is_staff = True
            updates.append("is_staff")
        if not user.is_superuser:
            user.is_superuser = True
            updates.append("is_superuser")

        if update_password:
            user.set_password(password)
            updates.append("password")

        if updates:
            user.save(update_fields=updates)

        self.stdout.write(self.style.SUCCESS(f"Django superuser already exists: {username}"))
