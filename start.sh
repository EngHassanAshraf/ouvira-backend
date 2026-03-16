#!/bin/bash
set -e
cd /app/backend
python manage.py migrate_schemas --shared
gunicorn config.wsgi:application --config gunicorn.conf.py
