# --------- STAGE 1: Builder ---------
FROM python:3.10-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential libpq-dev git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /wheels
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

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

# Copy entrypoint
COPY ./docker/entrypoint.sh /usr/local/bin/entrypoint.sh

# Download GeoLite2-City at build time into an immutable layer immune to volume mounts
# This step is optional - the application will gracefully handle missing GeoIP database
ARG MAXMIND_LICENSE_KEY
RUN mkdir -p /var/opt/geoip && \
    if [ -n "$MAXMIND_LICENSE_KEY" ]; then \
    echo "Downloading GeoLite2-City..." && \
    (curl -Ls --fail "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz" \
    | tar -xz --strip-components=1 -C /var/opt/geoip --wildcards "*.mmdb") \
    && echo "GeoLite2-City downloaded successfully." \
    || echo "WARNING: GeoLite2-City download failed. GeoIP will use fallback behavior. Check MAXMIND_LICENSE_KEY."; \
    else \
    echo "MAXMIND_LICENSE_KEY not set. GeoIP will gracefully fallback."; \
    fi

# Fix permissions
RUN chmod +x /usr/local/bin/entrypoint.sh && \
    mkdir -p /app/geoip && \
    chown -R appuser:appgroup /app /var/opt/geoip

# Drop to non-root user
USER appuser

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
