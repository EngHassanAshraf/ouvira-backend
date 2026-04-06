#!/bin/sh
set -e

if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running Migrations..."
    python manage.py migrate --noinput
fi

exec "$@"