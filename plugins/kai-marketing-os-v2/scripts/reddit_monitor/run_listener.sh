#!/bin/bash
# Reddit listener wrapper — emits an ALERTS_JSON line for cron/pipelines.
# Usage: bash run_listener.sh <profile-name>

set -e

PROFILE="${1:-}"
if [ -z "$PROFILE" ]; then
    echo "usage: $0 <profile-name>" >&2
    exit 2
fi

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Activate venv if present (sibling, parent, or repo root)
for v in "$DIR/venv/bin/activate" "$DIR/../venv/bin/activate" "$DIR/../../venv/bin/activate"; do
    if [ -f "$v" ]; then
        source "$v"
        break
    fi
done

OUTPUT=$(python reddit_listener.py --profile "$PROFILE" 2>&1)

ALERTS=$(echo "$OUTPUT" | grep "ALERTS_JSON:" | sed 's/ALERTS_JSON://')

if [ -n "$ALERTS" ] && [ "$ALERTS" != "[]" ]; then
    echo "$ALERTS"
else
    echo "NO_ALERTS"
fi
