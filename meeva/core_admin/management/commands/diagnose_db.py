import os
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Print active Django database connection details (password redacted)."

    def handle(self, *args, **options):
        settings_dict = connection.settings_dict

        def safe_get(key: str) -> str:
            value = settings_dict.get(key)
            if value in (None, ""):
                return "(empty)"
            return str(value)

        self.stdout.write("Active database connection")
        self.stdout.write(f"- DATABASE_URL set: {'yes' if os.getenv('DATABASE_URL') else 'no'}")
        self.stdout.write(f"- Vendor: {connection.vendor}")
        self.stdout.write(f"- ENGINE: {safe_get('ENGINE')}")
        self.stdout.write(f"- NAME: {safe_get('NAME')}")
        self.stdout.write(f"- USER: {safe_get('USER')}")
        self.stdout.write(f"- HOST: {safe_get('HOST')}")
        self.stdout.write(f"- PORT: {safe_get('PORT')}")
        self.stdout.write("- PASSWORD: [REDACTED]")

        options_dict = settings_dict.get("OPTIONS") or {}
        if options_dict:
            self.stdout.write(f"- OPTIONS: {options_dict}")
