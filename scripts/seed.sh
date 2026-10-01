#!/bin/bash
set -euo pipefail
export CLICOLOR=0
export CLICOLOR_FORCE=0

# Usage
usage() {
    echo "Usage: $(basename "$0") [count]"
    echo ""
    echo "Seeds the web api with sample requests, exercising the full pipeline."
    echo ""
    echo "Environment (or .env):"
    echo "  SEED_COUNT             Number of requests  (default 20)"
    echo "  SEED_BASE_URL          Root URL of the web (default http://localhost:3000)"
    exit 1
}
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
fi

die() {
    echo "ERROR: $*" >&2
    exit 1
}

log() {
    echo "INFO: $*"
}

# Check dependencies
if ! command -v curl >/dev/null; then
    die "curl is required"
fi
if ! command -v jq >/dev/null; then
    die "jq is required"
fi

# Load configuration
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi
COUNT="${1:-${SEED_COUNT:-20}}"
BASE_URL="${SEED_BASE_URL:-http://localhost:3000}"
if ! [[ "$COUNT" =~ ^[0-9]+$ ]]; then
    die "count must be a positive integer, got '$COUNT'"
fi

# Check connectivity
if ! curl -sf "$BASE_URL/api/health" >/dev/null 2>&1; then
    die "Cannot reach the web api at '$BASE_URL', is it running?"
fi

# Submit a request
submit() {
    local text="$1"
    curl -sS -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/submit" -H "Content-Type: application/json" -d "$(jq -nc --arg t "$text" '{text:$t}')"
}

# Seed the requests
log "Seeding $COUNT requests to '$BASE_URL/api/submit'..."
for i in $(seq 1 "$COUNT"); do
    STATUS=$(submit "Seed Request $i")
    log "Created request $i -> $STATUS"
done
log "Seeded $COUNT requests"
