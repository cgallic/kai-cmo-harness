#!/usr/bin/env bash
# Find a working Python 3 executable.
# On Windows, python3 can be a Microsoft Store stub that doesn't work.
# Try python first (works on Windows), then python3 (works on Linux/macOS).

_find_python() {
    # Try python first — if it's Python 3, use it
    if command -v python &>/dev/null; then
        local ver
        ver=$(python --version 2>&1 | grep -oP '\d+' | head -1)
        if [ "${ver:-0}" -ge 3 ] 2>/dev/null; then
            echo "python"
            return
        fi
    fi
    # Try python3
    if python3 --version &>/dev/null 2>&1; then
        echo "python3"
        return
    fi
    # Fallback
    echo "python"
}

PYTHON=$(_find_python)
