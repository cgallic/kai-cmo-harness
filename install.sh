#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Kai CMO Harness — Installer
# ============================================================================
# Installs the Kai marketing skills AND the knowledge base they run on
# (frameworks, checklists, channel guides, policy references, quality gates)
# into Claude Code. Works on macOS, Linux, and Windows (Git Bash / WSL).
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/cgallic/kai-cmo-harness/main/install.sh | bash
#   — or —
#   git clone https://github.com/cgallic/kai-cmo-harness.git && bash kai-cmo-harness/install.sh
#
# Inside Claude Code? You don't need this script at all:
#   /plugin marketplace add cgallic/kai-cmo-harness
#   /plugin install kai@kai-marketing-os
# ============================================================================

VERSION="2.0.0"
REPO="https://github.com/cgallic/kai-cmo-harness.git"
SKILLS_DIR="${HOME}/.claude/skills"
KAI_ROOT="${HOME}/.claude/kai"

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

info()  { printf "${GREEN}  ✓${RESET} %s\n" "$1"; }
warn()  { printf "${YELLOW}  !${RESET} %s\n" "$1"; }
fail()  { printf "${RED}  ✗${RESET} %s\n" "$1" >&2; exit 1; }

# ── Banner ────────────────────────────────────────────────────────────────────
printf "\n"
printf "${BOLD}${CYAN}  Kai Marketing OS — Installer${RESET}\n"
printf "${DIM}  Marketing team in your terminal. v${VERSION}${RESET}\n\n"

# ── Step 1: Check prerequisites ──────────────────────────────────────────────
printf "${BOLD}  Checking prerequisites...${RESET}\n"

if ! command -v git &>/dev/null; then
    fail "git is not installed. Install git first: https://git-scm.com"
fi
info "git found"

mkdir -p "$SKILLS_DIR"
info "Claude Code skills directory ready (${SKILLS_DIR})"

# ── Step 2: Download ─────────────────────────────────────────────────────────
printf "\n${BOLD}  Downloading Kai...${RESET}\n"

# If we're running from inside a checkout, use it; otherwise clone fresh.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-.}")" 2>/dev/null && pwd || true)"
if [[ -n "$SCRIPT_DIR" && -d "${SCRIPT_DIR}/harness/skills" && -d "${SCRIPT_DIR}/knowledge" ]]; then
    SRC="$SCRIPT_DIR"
    info "Using local checkout (${SRC})"
else
    TMPDIR_KAI=$(mktemp -d 2>/dev/null || mktemp -d -t 'kai-install')
    trap 'rm -rf "$TMPDIR_KAI"' EXIT
    if ! git clone --depth 1 --quiet "$REPO" "$TMPDIR_KAI" 2>/dev/null; then
        fail "Failed to clone repository. Check your internet connection and try again."
    fi
    SRC="$TMPDIR_KAI"
    info "Downloaded from GitHub"
fi

# ── Step 3: Install the knowledge base ───────────────────────────────────────
# Skills reference frameworks, checklists, policy references, contracts, and
# quality-gate scripts. Without these, most skills run hollow. They live in
# ~/.claude/kai so every project can use them.
printf "\n${BOLD}  Installing knowledge base...${RESET}\n"

rm -rf "$KAI_ROOT"
mkdir -p "$KAI_ROOT/harness" "$KAI_ROOT/scripts"

cp -r "$SRC/knowledge"               "$KAI_ROOT/knowledge"
cp -r "$SRC/harness/references"      "$KAI_ROOT/harness/references"
cp -r "$SRC/harness/skill-contracts" "$KAI_ROOT/harness/skill-contracts"
cp    "$SRC/harness/brief-schema.md" "$KAI_ROOT/harness/brief-schema.md"
# eco_core.py finds its install root by walking up for harness/eco-floors.yaml.
# Omitting it makes every eco_gate call raise "ECO floor registry not found",
# which silently breaks /kai-goal on install.sh installs.
cp    "$SRC/harness/eco-floors.yaml" "$KAI_ROOT/harness/eco-floors.yaml"
cp -r "$SRC/scripts/quality_gates"   "$KAI_ROOT/scripts/quality_gates"
cp -r "$SRC/scripts/reddit_monitor"  "$KAI_ROOT/scripts/reddit_monitor"

info "Knowledge base installed (${KAI_ROOT})"
info "$(find "$KAI_ROOT/knowledge" -name '*.md' | wc -l | tr -d ' ') knowledge docs, $(ls "$KAI_ROOT/harness/skill-contracts" | wc -l | tr -d ' ') skill contracts, $(ls "$KAI_ROOT/harness/references" | wc -l | tr -d ' ') policy references"

# ── Step 4: Install skills ───────────────────────────────────────────────────
printf "\n${BOLD}  Installing skills...${RESET}\n"

SKILL_COUNT=0
UPDATED=0

for skill_dir in "$SRC"/harness/skills/kai "$SRC"/harness/skills/kai-* "$SRC"/harness/skills/kaicalls-design; do
    [[ -d "$skill_dir" ]] || continue

    skill_name=$(basename "$skill_dir")
    target="${SKILLS_DIR}/${skill_name}"

    if [[ -d "$target" ]]; then
        rm -rf "$target"
        UPDATED=$((UPDATED + 1))
    fi

    cp -r "$skill_dir" "$target"
    SKILL_COUNT=$((SKILL_COUNT + 1))
done

if [[ "$SKILL_COUNT" -eq 0 ]]; then
    fail "No skills found in the repository. Something went wrong."
fi

if [[ "$UPDATED" -gt 0 ]]; then
    info "Updated ${SKILL_COUNT} skills (${UPDATED} replaced)"
else
    info "Installed ${SKILL_COUNT} skills"
fi

# ── Step 5: Verify ───────────────────────────────────────────────────────────
printf "\n${BOLD}  Verifying installation...${RESET}\n"

[[ -f "${SKILLS_DIR}/kai/SKILL.md" ]] \
    && info "/kai router ready" \
    || fail "Verification failed — /kai skill not found at ${SKILLS_DIR}/kai/SKILL.md"

[[ -f "${SKILLS_DIR}/kai-start/SKILL.md" ]] \
    && info "/kai-start onboarding ready" \
    || fail "Verification failed — /kai-start not found"

[[ -f "${KAI_ROOT}/knowledge/_index.md" ]] \
    && info "knowledge base reachable" \
    || fail "Verification failed — knowledge base missing at ${KAI_ROOT}/knowledge"

[[ -f "${KAI_ROOT}/scripts/quality_gates/banned_word_check.py" ]] \
    && info "quality gates ready" \
    || fail "Verification failed — quality gates missing"

[[ -f "${KAI_ROOT}/scripts/reddit_monitor/intelligence/cli.py" ]] \
    && info "Reddit Intelligence module ready" \
    || fail "Verification failed — Reddit Intelligence module missing"

# Optional extras: warn, never block the install.
[[ -f "${SKILLS_DIR}/kaicalls-design/SKILL.md" ]] \
    && info "kaicalls-design ready (optional)" \
    || warn "kaicalls-design not installed (optional — Kai works without it)"

# ── Done ─────────────────────────────────────────────────────────────────────
printf "\n"
printf "${GREEN}${BOLD}  Installed!${RESET} ${SKILL_COUNT} marketing commands + knowledge base ready.\n\n"

printf "  ${BOLD}Get started (2 minutes):${RESET}\n"
printf "    1. ${CYAN}cd your-product${RESET} and open Claude Code\n"
printf "    2. Type ${CYAN}/kai-start${RESET} — Kai reads your repo, plays back what your\n"
printf "       product is, and writes MARKETING.md. You'll only do this once.\n\n"

printf "  ${BOLD}Then try:${RESET}\n"
printf "    ${CYAN}/kai-growth-plan${RESET}   — marketing plan for your stage (~2 min)\n"
printf "    ${CYAN}/kai-email-system${RESET}  — write every email your product needs\n"
printf "    ${CYAN}/kai-landing-page${RESET}  — rewrite your page with proof + CRO hypotheses\n\n"

printf "  ${DIM}Prefer plugins? Inside Claude Code:${RESET}\n"
printf "  ${DIM}  /plugin marketplace add cgallic/kai-cmo-harness${RESET}\n"
printf "  ${DIM}  /plugin install kai@kai-marketing-os${RESET}\n\n"

printf "  ${DIM}GitHub: https://github.com/cgallic/kai-cmo-harness${RESET}\n"
printf "  ${DIM}Docs:   https://meetkai.xyz${RESET}\n\n"
