#!/usr/bin/env bash
# ===================================================
#   Kai Marketing OS - One-Click Dashboard Deployer
# ===================================================
echo "==================================================="
echo "  Kai Marketing OS - One-Click Dashboard Deployer"
echo "==================================================="
if ! command -v python3 &> /dev/null; then
    # Try standard 'python'
    if ! command -v python &> /dev/null; then
        echo "Error: Python 3 is not installed."
        exit 1
    else
        python scripts/deploy.py
    fi
else
    python3 scripts/deploy.py
fi
