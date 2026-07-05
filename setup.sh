#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Kai CMO Harness — Setup Wizard
# ============================================================================
# Interactive setup for the Kai CMO Marketing Intelligence Harness.
# Supports two paths:
#   (A) Claude Code only — copies knowledge + harness into a target project
#   (B) Full OpenClaw setup — generates config, .env, venv, workspace files
#
# Requirements: Python 3.12+, pip
# Platforms:    Linux, macOS
# ============================================================================

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# ── Globals ─────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.yaml"
ENV_FILE="${SCRIPT_DIR}/.env"
VENV_DIR="${SCRIPT_DIR}/.venv"

# ── Helpers ─────────────────────────────────────────────────────────────────
info()    { printf "${GREEN}[OK]${RESET}    %s\n" "$1"; }
warn()    { printf "${YELLOW}[WARN]${RESET}  %s\n" "$1"; }
error()   { printf "${RED}[ERROR]${RESET} %s\n" "$1" >&2; }
fatal()   { error "$1"; exit 1; }
prompt()  { printf "${YELLOW}?${RESET} %s " "$1"; }
header()  { printf "\n${BOLD}${CYAN}── Step %s ──${RESET}\n\n" "$1"; }
divider() { printf "${DIM}%s${RESET}\n" "────────────────────────────────────────────────────────"; }

# Prompt with default: ask "Question" "default"
ask() {
    local question="$1"
    local default="${2:-}"
    if [[ -n "$default" ]]; then
        prompt "${question} [${default}]:"
    else
        prompt "${question}:"
    fi
    read -r REPLY
    REPLY="${REPLY:-$default}"
}

# Yes/no prompt: confirm "Question" "y" (default)
confirm() {
    local question="$1"
    local default="${2:-y}"
    local hint
    if [[ "$default" == "y" ]]; then
        hint="Y/n"
    else
        hint="y/N"
    fi
    prompt "${question} [${hint}]:"
    read -r REPLY
    REPLY="${REPLY:-$default}"
    [[ "$REPLY" =~ ^[Yy] ]]
}

# ── Ctrl+C handler ──────────────────────────────────────────────────────────
cleanup() {
    printf "\n\n${YELLOW}Setup interrupted.${RESET} No changes have been written.\n"
    exit 130
}
trap cleanup INT TERM

# ── Banner ──────────────────────────────────────────────────────────────────
banner() {
    printf "\n"
    printf "${BOLD}${CYAN}"
    printf "  ╔═══════════════════════════════════════════════╗\n"
    printf "  ║                                               ║\n"
    printf "  ║     Kai CMO Harness — Setup Wizard            ║\n"
    printf "  ║     Marketing Intelligence for AI Agents      ║\n"
    printf "  ║                                               ║\n"
    printf "  ╚═══════════════════════════════════════════════╝\n"
    printf "${RESET}\n"
    printf "  ${DIM}Source: ${SCRIPT_DIR}${RESET}\n\n"
    divider
}

# ============================================================================
# Step 1: Prerequisites
# ============================================================================
check_prerequisites() {
    header "1/2 — Checking Prerequisites"

    local failed=0

    # Python 3.12+
    if command -v python3 &>/dev/null; then
        local py_version
        py_version="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
        local py_major py_minor
        py_major="$(echo "$py_version" | cut -d. -f1)"
        py_minor="$(echo "$py_version" | cut -d. -f2)"
        if [[ "$py_major" -ge 3 ]] && [[ "$py_minor" -ge 12 ]]; then
            info "Python ${py_version} found"
        else
            error "Python ${py_version} found — need 3.12+"
            failed=1
        fi
    else
        error "Python 3 not found — install Python 3.12+"
        failed=1
    fi

    # pip
    if python3 -m pip --version &>/dev/null; then
        info "pip found"
    else
        error "pip not found — install python3-pip"
        failed=1
    fi

    # jinja2
    if python3 -c "import jinja2" &>/dev/null 2>&1; then
        info "jinja2 installed"
    else
        warn "jinja2 not installed (will install during setup)"
    fi

    # pyyaml
    if python3 -c "import yaml" &>/dev/null 2>&1; then
        info "pyyaml installed"
    else
        warn "pyyaml not installed (will install during setup)"
    fi

    if [[ "$failed" -ne 0 ]]; then
        printf "\n"
        fatal "Prerequisites not met. Install the missing tools and re-run."
    fi

    printf "\n"
    info "All prerequisites satisfied."
}

# ============================================================================
# Step 2: Choose Path
# ============================================================================
choose_path() {
    header "2/2 — Choose Setup Path"

    printf "  ${BOLD}(A)${RESET} Claude Code only\n"
    printf "      Copies CLAUDE.md + knowledge/ + harness/ + scripts/quality_gates/\n"
    printf "      into an existing project. Your Claude Code agent gets marketing\n"
    printf "      intelligence immediately — no server required.\n\n"

    printf "  ${BOLD}(B)${RESET} Full OpenClaw setup\n"
    printf "      Interactive wizard: configure products, Discord channels, LLM provider,\n"
    printf "      generate config.yaml + .env, create venv, render workspace templates.\n"
    printf "      For running the autonomous marketing agent on a VPS.\n\n"

    ask "Choose path (A or B)" "A"
    SETUP_PATH="${REPLY^^}"

    if [[ "$SETUP_PATH" != "A" ]] && [[ "$SETUP_PATH" != "B" ]]; then
        fatal "Invalid choice: ${REPLY}. Enter A or B."
    fi
}

# ============================================================================
# Path A: Claude Code Only
# ============================================================================
path_claude_code() {
    printf "\n"
    divider
    printf "\n${BOLD}Claude Code Setup${RESET}\n\n"

    ask "Target project directory (absolute path)" ""
    local target_dir="$REPLY"

    if [[ -z "$target_dir" ]]; then
        fatal "Target directory is required."
    fi

    # Expand ~ if present
    target_dir="${target_dir/#\~/$HOME}"

    if [[ ! -d "$target_dir" ]]; then
        if confirm "Directory does not exist. Create it?" "y"; then
            mkdir -p "$target_dir"
            info "Created ${target_dir}"
        else
            fatal "Target directory does not exist."
        fi
    fi

    printf "\n  Copying files to ${BOLD}${target_dir}${RESET} ...\n\n"

    # CLAUDE.md — only copy if not present, to avoid clobbering user's own
    if [[ -f "${SCRIPT_DIR}/knowledge/_index.md" ]]; then
        # Build a marketing CLAUDE.md section to append or create
        local claude_target="${target_dir}/CLAUDE.md"
        if [[ -f "$claude_target" ]]; then
            warn "CLAUDE.md already exists — skipping (will not overwrite)"
        else
            # Create a minimal CLAUDE.md pointing to the knowledge base
            cat > "$claude_target" <<'CLAUDE_EOF'
# CLAUDE.md

## Marketing Intelligence

This project includes the Kai CMO marketing knowledge base. Use it for
content creation, SEO, ads, and strategy work.

| Path | Purpose |
|------|---------|
| `knowledge/_index.md` | Start here — framework lookup table |
| `knowledge/_quick-reference.md` | One-page cheat sheet |
| `knowledge/channels/` | Channel-specific guides (blog, email, ads, TikTok) |
| `knowledge/frameworks/` | Core frameworks (Algorithmic Authorship, Perception Engineering, AEO) |
| `knowledge/personas/` | 8 audience personas with pain points and hooks |
| `knowledge/checklists/` | Validation checklists for every content type |
| `harness/` | Skill contracts and architecture docs |
| `scripts/quality_gates/` | Four U's scoring, banned words, SEO lint |

### Quick Usage

1. Check `knowledge/_index.md` to find the right framework
2. Load the framework file as context
3. Write content applying the framework rules
4. Validate with the matching checklist from `knowledge/checklists/`
CLAUDE_EOF
            info "Created CLAUDE.md"
        fi
    fi

    # knowledge/
    if [[ -d "${SCRIPT_DIR}/knowledge" ]]; then
        mkdir -p "${target_dir}/knowledge"
        cp -r "${SCRIPT_DIR}/knowledge/." "${target_dir}/knowledge/"
        local knowledge_count
        knowledge_count="$(find "${target_dir}/knowledge" -type f | wc -l | tr -d ' ')"
        info "Copied knowledge/ (${knowledge_count} files)"
    else
        warn "knowledge/ directory not found in source — skipping"
    fi

    # harness/
    if [[ -d "${SCRIPT_DIR}/harness" ]]; then
        mkdir -p "${target_dir}/harness"
        cp -r "${SCRIPT_DIR}/harness/." "${target_dir}/harness/"
        info "Copied harness/"
    else
        warn "harness/ directory not found in source — skipping"
    fi

    # scripts/quality_gates/
    if [[ -d "${SCRIPT_DIR}/scripts/quality_gates" ]]; then
        mkdir -p "${target_dir}/scripts/quality_gates"
        cp -r "${SCRIPT_DIR}/scripts/quality_gates/." "${target_dir}/scripts/quality_gates/"
        info "Copied scripts/quality_gates/"
    else
        warn "scripts/quality_gates/ directory not found in source — skipping"
    fi

    printf "\n"
    divider
    printf "\n${GREEN}${BOLD}Done!${RESET} Your Claude Code now has marketing intelligence.\n\n"
    printf "  ${DIM}Target:${RESET} ${target_dir}\n"
    printf "  ${DIM}Start:${RESET}  Open ${BOLD}knowledge/_index.md${RESET} to explore frameworks.\n\n"
}

# ============================================================================
# Path B: Full OpenClaw Setup
# ============================================================================
path_openclaw() {
    printf "\n"
    divider
    printf "\n${BOLD}Full OpenClaw Setup${RESET}\n\n"

    # ── Collected values ────────────────────────────────────────────────────
    local owner_name="" company="" timezone=""
    local product_count=0
    local -a product_ids=() product_names=() product_urls=() product_descs=()
    local discord_writer="" discord_finance="" discord_updates="" discord_health="" discord_research=""
    local llm_provider="" llm_model=""
    local server_host=""

    # ── Step 1: Owner info ──────────────────────────────────────────────────
    header "1/7 — Owner Information"

    ask "Your name" ""
    owner_name="$REPLY"
    [[ -z "$owner_name" ]] && fatal "Name is required."

    ask "Company name" ""
    company="$REPLY"
    [[ -z "$company" ]] && fatal "Company name is required."

    ask "Timezone" "America/New_York"
    timezone="$REPLY"

    info "Owner: ${owner_name} @ ${company} (${timezone})"

    # ── Step 2: Products ────────────────────────────────────────────────────
    header "2/7 — Products"
    printf "  Configure the products/sites you are marketing.\n\n"

    ask "Number of products" "1"
    product_count="$REPLY"

    if ! [[ "$product_count" =~ ^[0-9]+$ ]] || [[ "$product_count" -lt 1 ]]; then
        fatal "Product count must be a positive integer."
    fi

    for ((i = 1; i <= product_count; i++)); do
        printf "\n  ${BOLD}Product ${i} of ${product_count}${RESET}\n"
        divider

        ask "  Product ID (lowercase, no spaces, e.g. myapp)" ""
        local pid="$REPLY"
        [[ -z "$pid" ]] && fatal "Product ID is required."
        # Sanitize: lowercase, replace spaces with hyphens
        pid="$(echo "$pid" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')"
        product_ids+=("$pid")

        ask "  Display name" "$pid"
        product_names+=("$REPLY")

        ask "  URL" "https://${pid}.com"
        product_urls+=("$REPLY")

        ask "  One-line description" ""
        product_descs+=("$REPLY")

        info "Product: ${pid} — ${product_names[-1]}"
    done

    # ── Step 3: Discord channels ────────────────────────────────────────────
    header "3/7 — Discord Channels"
    printf "  Enter Discord channel IDs for OpenClaw notifications.\n"
    printf "  ${DIM}Leave blank to skip — you can add them to config.yaml later.${RESET}\n\n"

    ask "Writer channel ID (content drafts)" ""
    discord_writer="$REPLY"

    ask "Finance channel ID (revenue alerts)" ""
    discord_finance="$REPLY"

    ask "Updates channel ID (daily/weekly reports)" ""
    discord_updates="$REPLY"

    ask "Health channel ID (infra alerts)" ""
    discord_health="$REPLY"

    ask "Research channel ID (research digest)" ""
    discord_research="$REPLY"

    info "Discord channels configured"

    # ── Step 4: LLM provider ───────────────────────────────────────────────
    header "4/7 — LLM Provider"
    printf "  Which LLM will generate content?\n\n"
    printf "    ${BOLD}gemini${RESET}    — Gemini 2.0 Flash (fast, cheap, good for volume)\n"
    printf "    ${BOLD}openai${RESET}    — GPT-4o / GPT-4o-mini\n"
    printf "    ${BOLD}anthropic${RESET} — Claude 3.5 Sonnet / Haiku\n\n"

    ask "LLM provider" "gemini"
    llm_provider="$REPLY"

    case "$llm_provider" in
        gemini)    ask "Model name" "gemini-2.0-flash" ;;
        openai)    ask "Model name" "gpt-4o" ;;
        anthropic) ask "Model name" "claude-3-5-sonnet-20241022" ;;
        *)         warn "Unknown provider '${llm_provider}' — proceeding anyway"
                   ask "Model name" "" ;;
    esac
    llm_model="$REPLY"

    info "LLM: ${llm_provider} / ${llm_model}"

    # ── Step 5: Server ──────────────────────────────────────────────────────
    header "5/7 — Server (Optional)"
    printf "  If you have a VPS for OpenClaw, enter its IP.\n"
    printf "  ${DIM}Leave blank to skip — you can deploy later.${RESET}\n\n"

    ask "Server host IP" ""
    server_host="$REPLY"

    if [[ -n "$server_host" ]]; then
        info "Server: ${server_host}"
    else
        info "No server configured — local-only setup"
    fi

    # ── Step 6: Generate config.yaml ────────────────────────────────────────
    header "6/7 — Generating Configuration"

    printf "  Writing ${BOLD}config.yaml${RESET} ...\n"

    {
        cat <<YAML_HEAD
# ============================================================================
# Kai CMO Harness — Configuration
# ============================================================================
# Generated by setup.sh on $(date -u '+%Y-%m-%d %H:%M:%S UTC')
# Edit this file to adjust products, thresholds, and schedules.
# Then run: python render_templates.py
# ============================================================================

owner:
  name: "${owner_name}"
  company: "${company}"
  timezone: "${timezone}"

# Products you're marketing. Each gets its own domain agent + analytics.
products:
YAML_HEAD

        for ((i = 0; i < product_count; i++)); do
            local pid="${product_ids[$i]}"
            local pname="${product_names[$i]}"
            local purl="${product_urls[$i]}"
            local pdesc="${product_descs[$i]}"
            local pid_upper
            pid_upper="$(echo "$pid" | tr '[:lower:]-' '[:upper:]_')"

            cat <<YAML_PRODUCT
  - id: ${pid}
    name: "${pname}"
    url: "${purl}"
    description: "${pdesc}"
    supabase_url_env: "${pid_upper}_SUPABASE_URL"
    supabase_key_env: "${pid_upper}_SUPABASE_KEY"
    ga4_property_env: "GA_${pid_upper}_PROPERTY_ID"
    gsc_url_env: "GSC_${pid_upper}_URL"
    discord_channel_id: ""
    proof_points: |
      - TODO: Add verified facts about ${pname}
      - TODO: Add pricing details
      - TODO: Add key metrics

YAML_PRODUCT
        done

        cat <<YAML_DISCORD
# Discord channels (OpenClaw path only)
discord:
  writer_channel_id: "${discord_writer}"
  finance_channel_id: "${discord_finance}"
  updates_channel_id: "${discord_updates}"
  health_channel_id: "${discord_health}"
  research_channel_id: "${discord_research}"

# Harness settings
harness:
  four_us_threshold: 12
  max_gate_retries: 2
  self_improvement: true
  llm_provider: "${llm_provider}"
  llm_model: "${llm_model}"

# Server deployment (OpenClaw path only)
server:
  host: "${server_host}"
  user: "root"
  workspace_path: "~/.openclaw/workspace"
  analytics_path: "/opt/cmo-analytics"
  venv_python: "/opt/cmo-analytics/venv/bin/python3"

# Scheduled tasks (OpenClaw path only)
schedule:
  daily_report: "0 8 * * *"
  weekly_report: "0 8 * * 1"
  pattern_extract: "0 8 * * 1"
  performance_check: "0 9 1 * *"
YAML_DISCORD
    } > "$CONFIG_FILE"

    info "config.yaml written"

    # ── Generate .env ───────────────────────────────────────────────────────
    printf "  Writing ${BOLD}.env${RESET} ...\n"

    {
        cat <<ENV_HEAD
# =============================================================================
# Kai CMO Harness — Environment Variables
# =============================================================================
# Generated by setup.sh on $(date -u '+%Y-%m-%d %H:%M:%S UTC')
# Fill in your API keys and credentials. NEVER commit this file.
# =============================================================================

# =============================================================================
# LLM API KEYS
# =============================================================================
ENV_HEAD

        case "$llm_provider" in
            gemini)
                echo "GEMINI_API_KEY=AIzaSy_REPLACE_ME"
                ;;
            openai)
                echo "OPENAI_API_KEY=sk-REPLACE_ME"
                ;;
            anthropic)
                echo "ANTHROPIC_API_KEY=sk-ant-REPLACE_ME"
                ;;
            *)
                echo "# Add your LLM API key here"
                echo "LLM_API_KEY=REPLACE_ME"
                ;;
        esac

        cat <<'ENV_COMMON'

# =============================================================================
# GOOGLE CREDENTIALS
# =============================================================================
GOOGLE_CREDENTIALS_PATH=/path/to/service-account.json

ENV_COMMON

        # Per-product env vars
        for ((i = 0; i < product_count; i++)); do
            local pid="${product_ids[$i]}"
            local pname="${product_names[$i]}"
            local pid_upper
            pid_upper="$(echo "$pid" | tr '[:lower:]-' '[:upper:]_')"

            cat <<ENV_PRODUCT
# =============================================================================
# ${pname}
# =============================================================================
${pid_upper}_SUPABASE_URL=https://xxx.supabase.co
${pid_upper}_SUPABASE_KEY=eyJ_REPLACE_ME
GA_${pid_upper}_PROPERTY_ID=123456789
GSC_${pid_upper}_URL=sc-domain:${pid}.com

ENV_PRODUCT
        done

        cat <<'ENV_TAIL'
# =============================================================================
# META / FACEBOOK ADS (optional)
# =============================================================================
META_ACCESS_TOKEN=REPLACE_ME
META_AD_ACCOUNT_ID=act_REPLACE_ME

# =============================================================================
# WEBHOOK GATEWAY
# =============================================================================
CMO_GATEWAY_API_KEY=REPLACE_ME_WITH_openssl_rand_hex_32
CMO_GATEWAY_HOST=0.0.0.0
CMO_GATEWAY_PORT=8088

# =============================================================================
# DISCORD (OpenClaw)
# =============================================================================
DISCORD_TOKEN=REPLACE_ME
ENV_TAIL
    } > "$ENV_FILE"

    info ".env template written"

    # ── Step 7: Create venv + install deps ──────────────────────────────────
    header "7/7 — Python Environment"

    if [[ -d "$VENV_DIR" ]]; then
        warn "Virtual environment already exists at ${VENV_DIR}"
        if confirm "Recreate it?" "n"; then
            rm -rf "$VENV_DIR"
        else
            info "Keeping existing venv"
        fi
    fi

    if [[ ! -d "$VENV_DIR" ]]; then
        printf "  Creating virtual environment ...\n"
        python3 -m venv "$VENV_DIR"
        info "Created .venv/"
    fi

    printf "  Installing dependencies ...\n"

    # Install core packages needed by the harness
    "${VENV_DIR}/bin/pip" install --quiet --upgrade pip
    "${VENV_DIR}/bin/pip" install --quiet jinja2 pyyaml python-dotenv

    # Install gateway requirements if present
    if [[ -f "${SCRIPT_DIR}/gateway/requirements.txt" ]]; then
        "${VENV_DIR}/bin/pip" install --quiet -r "${SCRIPT_DIR}/gateway/requirements.txt"
        info "Installed gateway dependencies"
    fi

    info "Python packages installed"

    # ── Render templates ────────────────────────────────────────────────────
    if [[ -f "${SCRIPT_DIR}/render_templates.py" ]]; then
        printf "  Rendering workspace templates ...\n"
        "${VENV_DIR}/bin/python" "${SCRIPT_DIR}/render_templates.py"
        info "Workspace templates rendered"
    else
        warn "render_templates.py not found — skipping template rendering"
        printf "  ${DIM}You can create this file later and run it manually.${RESET}\n"
    fi

    # ── Optional: copy to server ────────────────────────────────────────────
    if [[ -n "$server_host" ]]; then
        printf "\n"
        divider
        printf "\n"
        if confirm "Copy workspace to ${server_host}?" "n"; then
            printf "  Deploying to ${server_host} ...\n"

            local remote_user="root"
            local remote_path="~/.openclaw/workspace"

            # Create remote directories
            if ssh "${remote_user}@${server_host}" "mkdir -p ${remote_path}" 2>/dev/null; then
                # Copy workspace files
                scp -r "${SCRIPT_DIR}/workspace/." "${remote_user}@${server_host}:${remote_path}/" 2>/dev/null && \
                    info "Workspace copied to ${server_host}:${remote_path}" || \
                    warn "Failed to copy workspace — check SSH access"

                # Copy knowledge
                if [[ -d "${SCRIPT_DIR}/knowledge" ]]; then
                    ssh "${remote_user}@${server_host}" "mkdir -p ${remote_path}/knowledge" 2>/dev/null
                    scp -r "${SCRIPT_DIR}/knowledge/." "${remote_user}@${server_host}:${remote_path}/knowledge/" 2>/dev/null && \
                        info "Knowledge base copied" || \
                        warn "Failed to copy knowledge base"
                fi

                # Copy harness
                if [[ -d "${SCRIPT_DIR}/harness" ]]; then
                    ssh "${remote_user}@${server_host}" "mkdir -p ${remote_path}/harness" 2>/dev/null
                    scp -r "${SCRIPT_DIR}/harness/." "${remote_user}@${server_host}:${remote_path}/harness/" 2>/dev/null && \
                        info "Harness files copied" || \
                        warn "Failed to copy harness files"
                fi

                # Copy scripts
                if [[ -d "${SCRIPT_DIR}/scripts" ]]; then
                    local analytics_path="/opt/cmo-analytics"
                    ssh "${remote_user}@${server_host}" "mkdir -p ${analytics_path}/scripts" 2>/dev/null
                    scp -r "${SCRIPT_DIR}/scripts/." "${remote_user}@${server_host}:${analytics_path}/scripts/" 2>/dev/null && \
                        info "Scripts copied to ${analytics_path}/scripts/" || \
                        warn "Failed to copy scripts"
                fi
            else
                warn "Cannot reach ${server_host} via SSH — skipping deploy"
                printf "  ${DIM}You can deploy manually later with scp.${RESET}\n"
            fi
        else
            info "Skipping server deploy — you can copy files manually later"
        fi
    fi

    # ── Verify ──────────────────────────────────────────────────────────────
    printf "\n"
    divider
    printf "\n  Running status check ...\n\n"

    if [[ -f "${SCRIPT_DIR}/scripts/harness_cli.py" ]]; then
        # Try running status — this may fail if render_templates.py didn't run
        # or if server paths don't exist locally, so we catch errors gracefully
        "${VENV_DIR}/bin/python" "${SCRIPT_DIR}/scripts/harness_cli.py" status 2>/dev/null || \
            warn "Status check returned errors (expected for local-only setup)"
    else
        warn "harness_cli.py not found — skipping status check"
    fi

    # ── Summary ─────────────────────────────────────────────────────────────
    printf "\n"
    divider
    printf "\n${GREEN}${BOLD}Setup Complete!${RESET}\n\n"

    printf "  ${BOLD}Files generated:${RESET}\n"
    printf "    config.yaml    — Product configuration\n"
    printf "    .env           — API keys (fill in your values)\n"
    printf "    .venv/         — Python virtual environment\n"
    printf "\n"

    printf "  ${BOLD}Products configured:${RESET}\n"
    for ((i = 0; i < product_count; i++)); do
        printf "    ${GREEN}*${RESET} ${product_names[$i]} (${product_ids[$i]}) — ${product_urls[$i]}\n"
    done
    printf "\n"

    printf "  ${BOLD}LLM:${RESET} ${llm_provider} / ${llm_model}\n"

    if [[ -n "$server_host" ]]; then
        printf "  ${BOLD}Server:${RESET} ${server_host}\n"
    else
        printf "  ${BOLD}Server:${RESET} ${DIM}not configured${RESET}\n"
    fi

    printf "\n  ${BOLD}Next steps:${RESET}\n"
    printf "    1. Edit ${BOLD}.env${RESET} and add your API keys\n"
    printf "    2. Edit ${BOLD}config.yaml${RESET} and fill in proof_points for each product\n"

    if [[ -f "${SCRIPT_DIR}/render_templates.py" ]]; then
        printf "    3. Run ${BOLD}python render_templates.py${RESET} after editing config\n"
        printf "    4. Test: ${BOLD}.venv/bin/python scripts/harness_cli.py status${RESET}\n"
    else
        printf "    3. Create render_templates.py to generate workspace files from config\n"
        printf "    4. Test: ${BOLD}.venv/bin/python scripts/harness_cli.py status${RESET}\n"
    fi

    printf "\n"
}

# ============================================================================
# Main
# ============================================================================
main() {
    banner
    check_prerequisites
    choose_path

    case "$SETUP_PATH" in
        A) path_claude_code ;;
        B) path_openclaw ;;
    esac
}

main "$@"
