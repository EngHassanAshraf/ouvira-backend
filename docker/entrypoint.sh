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
    python manage.py migrate --check 2>/dev/null || {
        echo "ERROR: Migration state is inconsistent!"
        echo "Please run migrations before starting the server."
        exit 1
    }
}

# Run migrations if enabled
if [ "$RUN_MIGRATIONS" = "true" ]; then
    log "Running database migrations..."
    
    # Check database connectivity first
    check_db
    
    # Run migrations
    python manage.py migrate --noinput
    
    # Validate migrations completed successfully
    validate_migrations
    
    log "Migrations completed successfully."
else
    log "Skipping migrations (RUN_MIGRATIONS is not 'true')."
    # Still check for pending migrations as a warning
    check_migrations
fi

# Collect static files if in production and COLLECT_STATIC is true
if [ "$COLLECT_STATIC" = "true" ]; then
    log "Collecting static files..."
    python manage.py collectstatic --noinput --clear
fi

log "Starting application..."
echo ""

# Execute the main command
exec "$@"