#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Kai CMO Harness — Installer
# ============================================================================
# Installs Kai marketing slash commands and KaiCalls design guidance into Claude Code.
# Works on macOS, Linux, and Windows (Git Bash / WSL).
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/cgallic/kai-cmo-harness/main/install.sh | bash
#   — or —
#   git clone ... && ./install.sh
# ============================================================================

VERSION="1.0.0"
REPO="https://github.com/cgallic/kai-cmo-harness.git"
SKILLS_DIR="${HOME}/.claude/skills"

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
printf "${BOLD}${CYAN}  Kai CMO Harness — Installer${RESET}\n"
printf "${DIM}  Marketing team in your terminal. v${VERSION}${RESET}\n\n"

# ── Step 1: Check prerequisites ──────────────────────────────────────────────
printf "${BOLD}  Checking prerequisites...${RESET}\n"

# Git
if ! command -v git &>/dev/null; then
    fail "git is not installed. Install git first: https://git-scm.com"
fi
info "git found"

# Claude Code skills directory
if [[ ! -d "${HOME}/.claude" ]]; then
    warn "~/.claude directory not found — creating it"
    mkdir -p "${HOME}/.claude"
fi

if [[ ! -d "$SKILLS_DIR" ]]; then
    warn "~/.claude/skills directory not found — creating it"
    mkdir -p "$SKILLS_DIR"
fi
info "Claude Code skills directory ready (${SKILLS_DIR})"

# ── Step 2: Download ─────────────────────────────────────────────────────────
printf "\n${BOLD}  Downloading Kai...${RESET}\n"

# Create a temp directory that works on all platforms
TMPDIR_KAI=$(mktemp -d 2>/dev/null || mktemp -d -t 'kai-install')
trap 'rm -rf "$TMPDIR_KAI"' EXIT

if ! git clone --depth 1 --quiet "$REPO" "$TMPDIR_KAI" 2>/dev/null; then
    fail "Failed to clone repository. Check your internet connection and try again."
fi
info "Downloaded from GitHub"

# ── Step 3: Install skills ───────────────────────────────────────────────────
printf "\n${BOLD}  Installing skills...${RESET}\n"

SKILL_COUNT=0
SKIPPED=0

skill_dirs=(
    "$TMPDIR_KAI"/harness/skills/kai
    "$TMPDIR_KAI"/harness/skills/kai-*
    "$TMPDIR_KAI"/harness/skills/kaicalls-design
)

for skill_dir in "${skill_dirs[@]}"; do
    if [[ ! -d "$skill_dir" ]]; then
        continue
    fi

    skill_name=$(basename "$skill_dir")
    target="${SKILLS_DIR}/${skill_name}"

    if [[ -d "$target" ]]; then
        # Overwrite existing — user is updating
        rm -rf "$target"
        SKIPPED=$((SKIPPED + 1))
    fi

    cp -r "$skill_dir" "$target"
    SKILL_COUNT=$((SKILL_COUNT + 1))
done

if [[ "$SKILL_COUNT" -eq 0 ]]; then
    fail "No skills found in the repository. Something went wrong."
fi

if [[ "$SKIPPED" -gt 0 ]]; then
    info "Updated ${SKILL_COUNT} skills (${SKIPPED} replaced)"
else
    info "Installed ${SKILL_COUNT} skills"
fi

# ── Step 4: Verify ───────────────────────────────────────────────────────────
printf "\n${BOLD}  Verifying installation...${RESET}\n"

if [[ -f "${SKILLS_DIR}/kai/SKILL.md" ]]; then
    info "/kai command ready"
else
    fail "Verification failed — /kai skill not found at ${SKILLS_DIR}/kai/SKILL.md"
fi

if [[ -f "${SKILLS_DIR}/kai-email-system/SKILL.md" ]]; then
    info "/kai-email-system command ready"
else
    warn "/kai-email-system not found — some skills may be missing"
fi

if [[ -f "${SKILLS_DIR}/kai-start/SKILL.md" ]]; then
    info "/kai-start onboarding ready"
else
    warn "/kai-start not found (optional — you can use /kai directly)"
fi

if [[ -f "${SKILLS_DIR}/kaicalls-design/SKILL.md" ]] && [[ -f "${SKILLS_DIR}/kaicalls-design/references/full-color-tokens.md" ]] && [[ -f "${SKILLS_DIR}/kaicalls-design/references/component-examples.md" ]]; then
    info "kaicalls-design references ready"
else
    fail "Verification failed — kaicalls-design reference files were not installed"
fi

# ── Done ─────────────────────────────────────────────────────────────────────
printf "\n"
printf "${GREEN}${BOLD}  Installed!${RESET} ${SKILL_COUNT} marketing commands ready.\n\n"

printf "  ${BOLD}Get started:${RESET}\n"
printf "    1. Open Claude Code in any project\n"
printf "    2. Type ${CYAN}/kai-start${RESET} for guided setup (creates MARKETING.md)\n"
printf "    3. Or type ${CYAN}/kai${RESET} to see all commands\n\n"

printf "  ${BOLD}First 3 commands to try:${RESET}\n"
printf "    ${CYAN}/kai-audit${RESET}         — Full marketing health check (60 seconds)\n"
printf "    ${CYAN}/kai-email-system${RESET}  — Write every email your product needs\n"
printf "    ${CYAN}/kai-growth-plan${RESET}   — Marketing plan for your stage\n\n"

printf "  ${DIM}GitHub: https://github.com/cgallic/kai-cmo-harness${RESET}\n"
printf "  ${DIM}Docs:   https://meetkai.xyz${RESET}\n\n"
