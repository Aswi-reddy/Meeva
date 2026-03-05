#!/usr/bin/env bash
set -euo pipefail

cd meeva

# Safe to run on every deploy/start; applies new migrations (including index migrations).
python manage.py migrate --noinput

exec gunicorn meeva.wsgi:application --bind 0.0.0.0:${PORT:-8000}
