#!/bin/sh
# Download GeoLite2-City database — always exits 0 (never blocks startup)

GEOIP_DIR="${1:-/app/backend/geoip}"
mkdir -p "$GEOIP_DIR"

if [ -z "$MAXMIND_LICENSE_KEY" ]; then
    echo "MAXMIND_LICENSE_KEY not set — skipping GeoIP download."
    exit 0
fi

TMPFILE="/tmp/geoip_$$.tar.gz"
URL="https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz"

echo "Downloading GeoLite2-City..."
curl -Ls --fail "$URL" -o "$TMPFILE"
CURL_EXIT=$?

if [ $CURL_EXIT -ne 0 ]; then
    echo "WARNING: GeoIP download failed (curl exit $CURL_EXIT) — continuing without it."
    rm -f "$TMPFILE"
    exit 0
fi

# Check it's actually gzip (first 2 bytes = 0x1f 0x8b)
MAGIC=$(od -A n -t x1 -N 2 "$TMPFILE" 2>/dev/null | tr -d ' ')
if [ "$MAGIC" != "1f8b" ]; then
    echo "WARNING: Downloaded file is not gzip (got: $MAGIC) — MaxMind likely returned an error page."
    rm -f "$TMPFILE"
    exit 0
fi

tar -xz --strip-components=1 -C "$GEOIP_DIR" --wildcards "*.mmdb" -f "$TMPFILE"
TAR_EXIT=$?

rm -f "$TMPFILE"

if [ $TAR_EXIT -ne 0 ]; then
    echo "WARNING: GeoIP extraction failed — continuing without it."
    exit 0
fi

echo "GeoLite2-City downloaded successfully to $GEOIP_DIR."
exit 0
