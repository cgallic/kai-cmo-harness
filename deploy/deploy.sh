#!/usr/bin/env bash
# ============================================================================
# CMO Harness — Production Deploy Script
# ============================================================================
# Usage: bash deploy.sh [--skip-install]
#
# Runs: git pull → pip install → restart services → health check → auto-rollback
# ============================================================================

set -euo pipefail

PRODUCT="cmo-harness"
SERVICE="cmo-agent"
ANALYTICS_DIR="/opt/cmo-analytics"
WORKSPACE_DIR="${HOME}/.openclaw/workspace"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[DEPLOY]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

# Save current commit for rollback
PREV_COMMIT=$(git rev-parse HEAD)
log "Current commit: ${PREV_COMMIT:0:8}"

# Pull latest
log "Pulling latest changes..."
git pull --ff-only || fail "git pull failed — resolve conflicts manually"

NEW_COMMIT=$(git rev-parse HEAD)
if [ "$PREV_COMMIT" = "$NEW_COMMIT" ]; then
    log "Already up to date. Nothing to deploy."
    exit 0
fi
log "New commit: ${NEW_COMMIT:0:8}"

# Install dependencies
if [ "${1:-}" != "--skip-install" ]; then
    log "Installing Python dependencies..."
    cd "$ANALYTICS_DIR"
    source venv/bin/activate
    pip install -q -r requirements.txt
fi

# Render templates (if config.yaml exists)
if [ -f "$ANALYTICS_DIR/config.yaml" ]; then
    log "Rendering workspace templates..."
    python "$ANALYTICS_DIR/render_templates.py" --config "$ANALYTICS_DIR/config.yaml" --output-dir "$WORKSPACE_DIR"
fi

# Restart service
if systemctl is-active --quiet "$SERVICE" 2>/dev/null; then
    log "Restarting $SERVICE..."
    systemctl restart "$SERVICE"
    sleep 3

    # Health check
    if systemctl is-active --quiet "$SERVICE"; then
        log "Service $SERVICE is running."
    else
        warn "Service $SERVICE failed to start. Rolling back..."
        git checkout "$PREV_COMMIT"
        systemctl restart "$SERVICE"
        fail "Rolled back to ${PREV_COMMIT:0:8}. Check logs: journalctl -u $SERVICE -n 50"
    fi
else
    warn "Service $SERVICE not found or not running. Skipping restart."
fi

log "Deploy complete: ${PREV_COMMIT:0:8} → ${NEW_COMMIT:0:8}"
