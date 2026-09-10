#!/bin/bash
set -euo pipefail
export CLICOLOR=0
export CLICOLOR_FORCE=0

# Usage
usage() {
    echo "Usage: $(basename "$0")"
    echo ""
    echo "Generates a SigNoz service-account API token for Terraform and writes it to terraform/terraform.tfvars."
    echo "On a fresh instance it also registers the first admin."
    echo ""
    echo "Environment (or .env):"
    echo "  SIGNOZ_ENDPOINT        Root URL of SigNoz (default http://localhost:8080)"
    echo "  SIGNOZ_ADMIN_NAME      Admin display name (default Admin)"
    echo "  SIGNOZ_ADMIN_EMAIL     Admin email        (default admin@email.com)"
    echo "  SIGNOZ_ADMIN_PASSWORD  Admin password     (default Password123!)"
    echo "  SIGNOZ_SA_NAME         Service account    (default terraform)"
    echo "  SIGNOZ_SA_KEY_NAME     Key name           (default terraform)"
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
if ! command -v jq >/dev/null; then
    die "jq is required"
fi
cd "$(dirname "$0")"

# Load credentials
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi
ENDPOINT="${SIGNOZ_ENDPOINT:-http://localhost:8080}"
ADMIN_NAME="${SIGNOZ_ADMIN_NAME:-Admin}"
ADMIN_EMAIL="${SIGNOZ_ADMIN_EMAIL:-admin@email.com}"
ADMIN_PASSWORD="${SIGNOZ_ADMIN_PASSWORD:-Password123!}"
SA_NAME="${SIGNOZ_SA_NAME:-terraform}"
SA_KEY_NAME="${SIGNOZ_SA_KEY_NAME:-terraform}"

# Check connectivity
if ! curl -sf "$ENDPOINT/api/v1/health" >/dev/null 2>&1; then
    die "Cannot reach signoz at '$ENDPOINT', is it running?"
fi

# Call the signoz api
api() {
    local method="$1" path="$2" body="${3:-}" token="${4:-}"
    local args=(-sS -X "$method" "$ENDPOINT$path" -H "Content-Type: application/json")
    if [ -n "$token" ]; then
        args+=(-H "Authorization: Bearer $token")
    fi
    if [ -n "$body" ]; then
        args+=(-d "$body")
    fi
    curl "${args[@]}"
}

# Register the admin user
REGISTER_RESPONSE=$(api POST /api/v1/register "$(jq -nc --arg n "$ADMIN_NAME" --arg e "$ADMIN_EMAIL" --arg p "$ADMIN_PASSWORD" '{name:$n,orgName:"",email:$e,password:$p}')" 2>/dev/null || true)

# Resolve the admin's org
ADMIN_ORG_ID=$(api GET "/api/v2/sessions/context?email=$(jq -rn --arg s "$ADMIN_EMAIL" '$s|@uri')&ref=$(jq -rn --arg s "$ENDPOINT" '$s|@uri')" | jq -r '.data.orgs[0].id')
if [ -z "$ADMIN_ORG_ID" ] || [ "$ADMIN_ORG_ID" = "null" ]; then
    REGISTER_ERROR=$(echo "$REGISTER_RESPONSE" | jq -r '.error.message // empty' 2>/dev/null || true)
    die "Could not resolve an org for '$ADMIN_EMAIL', the admin was not registered${REGISTER_ERROR:+ ($REGISTER_ERROR)}"
fi

# Log in as the admin
ADMIN_TOKEN=$(api POST /api/v2/sessions/email_password "$(jq -nc --arg e "$ADMIN_EMAIL" --arg p "$ADMIN_PASSWORD" --arg o "$ADMIN_ORG_ID" '{email:$e,password:$p,orgId:$o}')" | jq -r '.data.accessToken')
if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "null" ]; then
    die "Login failed, check the admin password"
fi

# Get or create the service account
SA_ID=$(api GET /api/v1/service_accounts "" "$ADMIN_TOKEN" | jq -r --arg n "$SA_NAME" 'first(.data[]? | select(.name==$n) | .id) // empty')
if [ -z "$SA_ID" ]; then
    SA_ID=$(api POST /api/v1/service_accounts "$(jq -nc --arg n "$SA_NAME" '{name:$n}')" "$ADMIN_TOKEN" | jq -r '.data.id')
    log "Created service account '$SA_NAME'"
else
    log "Reusing service account '$SA_NAME'"
fi

# Ensure the admin role is attached to the service account
SA_HAS_ADMIN_ROLE=$(api GET "/api/v1/service_accounts/$SA_ID/roles" "" "$ADMIN_TOKEN" | jq -r 'any(.data[]?; (.displayName // .name // "" | ascii_downcase | contains("admin")))')
if [ "$SA_HAS_ADMIN_ROLE" != "true" ]; then
    ADMIN_ROLE_ID=$(api GET /api/v1/roles "" "$ADMIN_TOKEN" | jq -r 'first(.data[]? | select((.displayName // .name // "" | ascii_downcase) | contains("admin")) | .id) // empty')
    if [ -z "$ADMIN_ROLE_ID" ]; then
        die "No admin role found to attach"
    fi
    api POST /api/v1/service_account_roles "$(jq -nc --arg s "$SA_ID" --arg r "$ADMIN_ROLE_ID" '{serviceAccountId:$s,roleId:$r}')" "$ADMIN_TOKEN" >/dev/null
    log "Attached admin role"
else
    log "Admin role already attached"
fi

# Generate a key (revoke any existing key with the same name first)
EXISTING_KEY_ID=$(api GET "/api/v1/service_accounts/$SA_ID/keys" "" "$ADMIN_TOKEN" | jq -r --arg n "$SA_KEY_NAME" 'first(.data[]? | select(.name==$n) | .id) // empty')
if [ -n "$EXISTING_KEY_ID" ]; then
    api DELETE "/api/v1/service_accounts/$SA_ID/keys/$EXISTING_KEY_ID" "" "$ADMIN_TOKEN" >/dev/null
    log "Revoked existing key '$SA_KEY_NAME'"
fi
KEY_RESPONSE=$(api POST "/api/v1/service_accounts/$SA_ID/keys" "$(jq -nc --arg n "$SA_KEY_NAME" '{name:$n,expiresAt:0}')" "$ADMIN_TOKEN")
SA_KEY=$(echo "$KEY_RESPONSE" | jq -r '.data.key // empty')
if [ -z "$SA_KEY" ]; then
    KEY_ERROR=$(echo "$KEY_RESPONSE" | jq -r '.error.message // empty')
    die "Key creation failed${KEY_ERROR:+ ($KEY_ERROR)}"
fi

# Write the key to terraform.tfvars
printf '# Generated by bootstrap.sh\nsignoz_access_token = "%s"\n' "$SA_KEY" >terraform/terraform.tfvars
log "Wrote terraform/terraform.tfvars"
