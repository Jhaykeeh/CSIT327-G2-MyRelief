#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Running database migrations"
python manage.py makemigrations
python manage.py migrate --noinput

echo "==> Creating superuser if environment variables are set"
python manage.py create_admin || echo "Skipping superuser creation (no environment variables set)"

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Build complete"