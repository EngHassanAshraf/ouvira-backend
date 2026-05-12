#!/bin/sh
set -e

echo "=== Ouvira Backend Entrypoint ==="
echo "Environment: ${DJANGO_ENV:-production}"
echo "Run Migrations: ${RUN_MIGRATIONS:-false}"
echo ""

# Set Django settings module if not already set
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.production}

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check database connectivity
check_db() {
    log "Checking database connectivity..."
    python -c "
import os
import sys
import time

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${DJANGO_SETTINGS_MODULE}')

# Setup Django
import django
django.setup()

from django.db import connections
from django.db.utils import OperationalError

max_retries = 5
for i in range(max_retries):
    try:
        connections['default'].cursor()
        print('Database connection established.')
        sys.exit(0)
    except OperationalError as e:
        print(f'Attempt {i+1}/{max_retries}: Database not ready, waiting...')
        time.sleep(2)

print('ERROR: Could not connect to database after {} attempts'.format(max_retries))
sys.exit(1)
"
}

# Function to check pending migrations
check_migrations() {
    log "Checking for pending migrations..."
    python manage.py showmigrations --plan 2>/dev/null | grep -q "^\s*\[ \]" && {
        echo "WARNING: Pending migrations detected!"
        python manage.py showmigrations --plan 2>/dev/null | grep "^\s*\[ \]"
    } || echo "No pending migrations."
}

# Function to validate migration state
validate_migrations() {
    log "Validating migration state..."
    echo "Migration validation skipped for multi-tenant setup."
}

# Run migrations — always run on startup
log "Running database migrations..."
check_db
python manage.py migrate_schemas --shared
validate_migrations
log "Migrations completed successfully."

# Collect static files — always run so WhiteNoise has the staticfiles dir
log "Collecting static files..."
python manage.py collectstatic --noinput --clear

log "Starting application..."
echo ""

# Execute the main command
exec "$@"