#!/bin/bash
echo "==> Starting boot script..."
cd meeva || exit 1

echo "==> Gathering static files..."
python manage.py collectstatic --noinput

echo "==> Running migrations (if this hangs, your Database is unreachable!)..."
python manage.py migrate

echo "==> Checking superuser..."
python create_superuser.py

echo "==> Starting Gunicorn on port $PORT..."
gunicorn meeva.wsgi:application --bind 0.0.0.0:$PORT
