# --------- STAGE 1: Builder ---------
FROM python:3.10-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential libpq-dev git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /wheels
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# --------- STAGE 2: Runner ---------
FROM python:3.10-slim AS runner
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Install runtime libraries (postgresql-client for tools, libpq5 for psycopg2 runtime)
RUN apt-get update && apt-get install -y \
    postgresql-client libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system appgroup && adduser --system --group appuser

WORKDIR /app

# Copy compiled wheels and install them
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*.whl

# Copy backend application source
COPY ./backend .

# Copy entrypoint and GeoIP helper
COPY ./docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY ./docker/download_geoip.sh /usr/local/bin/download_geoip.sh

# Download GeoLite2-City at build time into an immutable layer immune to volume mounts
# This step is optional - the application will gracefully handle missing GeoIP database
ARG MAXMIND_LICENSE_KEY
RUN chmod +x /usr/local/bin/download_geoip.sh && \
    /usr/local/bin/download_geoip.sh /var/opt/geoip

# Collect static files at build time so WhiteNoise has them regardless of how
# the container is started (Railway startCommand bypasses the entrypoint).
# SECRET_KEY is a dummy value — collectstatic does not need a real one.
RUN SECRET_KEY=build-time-placeholder \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    ALLOWED_HOSTS=localhost \
    DB_HOST=localhost DB_PORT=5432 \
    POSTGRES_DB=placeholder POSTGRES_USER=placeholder POSTGRES_PASSWORD=placeholder \
    python manage.py collectstatic --noinput --clear 2>&1 || true

# Fix permissions
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/download_geoip.sh && \
    mkdir -p /app/geoip && \
    chown -R appuser:appgroup /app /var/opt/geoip

# Drop to non-root user
USER appuser

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
