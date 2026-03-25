#!/usr/bin/env bash
# kai-marketing preamble — shared by all SKILL.md files.
# Source this at the start of every skill to set up the environment.
#
# Sets: KAI_ROOT, KAI_DIR, KAI_VERSION
# Creates: ~/.kai-marketing/ directories if missing

KAI_ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")")/.." && pwd)"
KAI_DIR="${HOME}/.kai-marketing"
KAI_VERSION=$(cat "${KAI_ROOT}/VERSION" 2>/dev/null || echo "unknown")

# Ensure state directories exist
mkdir -p "$KAI_DIR"/{briefs,drafts,gates,reports,pending,analytics,sessions}

# Add bin/ to PATH so skills can call kai-* tools
export PATH="${KAI_ROOT}/bin:${PATH}"
export PYTHONPATH="${KAI_ROOT}:${PYTHONPATH:-}"

echo "kai-marketing v${KAI_VERSION}"
