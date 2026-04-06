# Task 081: Build packaging, install, and setup system

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 14. Operator Surfaces, Packaging, and Delivery
**Priority:** P2
**Depends on:** 079
**Estimated complexity:** Large

## Context

Kai must be installable by non-technical operators. The packaging system handles dependency checking, directory structure creation, configuration generation, and interactive setup. The setup wizard walks operators through creating their first business profile, selecting an archetype, configuring channels, and setting approval preferences — without requiring them to edit YAML files manually. The plugin packaging system defines how Kai skills, knowledge, and configuration can be bundled and installed into any Claude Code-compatible project. The runbook provides day-to-day operational guidance.

## Scope

Create `kai/packaging/` module with an installer, setup wizard, plugin packaging definitions, and operational runbook documentation.

## Detailed Requirements

### File: `kai/packaging/__init__.py`
- Module docstring explaining the packaging layer
- Export key classes

### File: `kai/packaging/install.py`

**Model: InstallationResult**
- `success: bool`
- `python_version: str`
- `python_version_ok: bool`
- `dependencies_installed: List[str]`
- `dependencies_failed: List[str]`
- `directories_created: List[str]`
- `config_generated: bool`
- `config_path: str`
- `errors: List[str]`
- `warnings: List[str]`
- `next_steps: List[str]`

**Model: DependencyCheck**
- `name: str`
- `required_version: Optional[str]`
- `installed: bool`
- `installed_version: Optional[str]`
- `required: bool` — True for required, False for optional
- `purpose: str` — what this dependency is for

**Class: Installer**
- `__init__(self, target_dir: str)`
- `check_prerequisites(self) -> Dict[str, Any]`:
  - Check Python version (require >= 3.9)
  - Check for required system tools: git
  - Return: {python_version, python_ok, git_available, git_version}
- `check_dependencies(self) -> List[DependencyCheck]`:
  - Check for required packages:
    - `pyyaml` (required) — configuration files
    - `fastapi` (optional) — gateway/remote surface
    - `uvicorn` (optional) — gateway server
    - `httpx` (optional) — API connectors
    - `python-dotenv` (optional) — environment variable management
  - For each: check if installed, check version
  - Return list of DependencyCheck objects
- `create_directory_structure(self, business_id: str = "default") -> List[str]`:
  - Create the workspace directory structure:
    - `workspace/` — root workspace
    - `workspace/{business_id}/` — per-business workspace
    - `workspace/{business_id}/audit/` — audit trail storage
    - `workspace/{business_id}/memory/` — memory/learning storage
    - `workspace/{business_id}/execution/` — execution history
    - `workspace/{business_id}/content/` — generated content
    - `workspace/{business_id}/config/` — business-specific config
  - Return list of created directory paths
- `generate_config(self, template_path: str = "config.example.yaml") -> str`:
  - Read config.example.yaml
  - Generate a new config.yaml with placeholder values
  - Return path to generated config
- `validate_installation(self) -> Dict[str, Any]`:
  - Verify all directories exist
  - Verify config file is valid YAML
  - Verify required Python modules importable
  - Return: {valid, issues (list of str)}
- `install(self) -> InstallationResult`:
  - Run full installation flow:
    1. Check prerequisites
    2. Check and report dependencies
    3. Create directory structure
    4. Generate config from template
    5. Validate installation
  - Return InstallationResult with full details

### File: `kai/packaging/setup.py`

**Model: SetupQuestion**
- `id: str`
- `prompt: str` — the question to ask the operator
- `field_name: str` — which config/profile field this maps to
- `input_type: str` — "text", "select", "multiselect", "boolean", "number"
- `options: Optional[List[str]]` — for select/multiselect types
- `default: Optional[Any]`
- `required: bool`
- `validation: Optional[str]` — validation rule description
- `help_text: Optional[str]` — additional guidance

**Model: SetupSection**
- `title: str`
- `description: str`
- `questions: List[SetupQuestion]`
- `required: bool` — whether this section can be skipped

**Model: SetupResult**
- `business_profile: Dict[str, Any]`
- `archetype: str`
- `config: Dict[str, Any]`
- `workspace_state: Dict[str, Any]`
- `completed_sections: List[str]`
- `skipped_sections: List[str]`

**Class: SetupWizard**
- `__init__(self, workspace_dir: str)`
- `get_sections(self) -> List[SetupSection]`:
  - Section 1: "Business Information" (required)
    - Business name (text, required)
    - Website URL (text, optional)
    - Business phone (text, required for local service)
    - Business description (text, required)
    - Year founded (number, optional)
    - Employee count range (select: "1-5", "6-20", "21-50", "51-200", "200+")
  - Section 2: "Services & Offerings" (required)
    - Primary service/product (text, required)
    - Full service list (text, comma-separated)
    - Pricing model (select: "per-job", "hourly", "subscription", "project", "retainer", "product-based")
    - Average deal value (text, optional)
  - Section 3: "Service Area" (conditional — required for local/multi-location)
    - Primary city (text)
    - State/province (text)
    - Service radius miles (number)
    - Additional service areas (text, comma-separated)
  - Section 4: "Archetype Selection" (required)
    - Business type (select: "Local Service Business", "Ecommerce/Online Store", "Professional Services/B2B", "Multi-Location Business")
    - Auto-detect option (boolean: "Let Kai determine the best archetype automatically")
  - Section 5: "Channel Configuration" (required)
    - Active social platforms (multiselect: "Facebook", "Instagram", "LinkedIn", "TikTok", "X/Twitter", "YouTube", "Pinterest")
    - Active ad platforms (multiselect: "Google Ads", "Meta Ads", "LinkedIn Ads", "TikTok Ads", "Microsoft Ads")
    - Email marketing platform (select: "None", "Mailchimp", "Klaviyo", "Loops", "ActiveCampaign", "Other")
    - CRM (select: "None", "HubSpot", "Salesforce", "Pipedrive", "Jobber", "ServiceTitan", "Other")
  - Section 6: "Budget & Risk Preferences" (optional)
    - Monthly marketing budget (number, optional)
    - Max daily ad spend (number, optional)
    - Risk tolerance (select: "Conservative", "Moderate", "Aggressive")
    - Auto-approval for low-risk actions (boolean, default True)
  - Section 7: "Approval Preferences" (optional)
    - Require approval for all public content (boolean, default True)
    - Notification preference (select: "in-app only", "email", "email + slack")
    - Operator email for notifications (text, optional)
  - Section 8: "Watcher Configuration" (optional)
    - Enable background monitoring (boolean, default True)
    - Monitoring frequency (select: "Minimal", "Standard", "Comprehensive")
    - Quiet hours (text: "22:00-07:00" format, optional)
- `process_section(self, section_index: int, answers: Dict[str, Any]) -> Dict[str, Any]`:
  - Validate answers against question requirements
  - Return processed data
- `build_business_profile(self, all_answers: Dict[str, Any]) -> Dict[str, Any]`:
  - Compile all section answers into a BusinessProfile dict
  - Set archetype based on section 4
  - Configure channels based on section 5
  - Return the profile
- `build_config(self, all_answers: Dict[str, Any]) -> Dict[str, Any]`:
  - Generate config.yaml content from answers
  - Include: business profile, channel config, budget settings, approval settings, watcher settings
  - Return config dict
- `build_workspace_state(self, all_answers: Dict[str, Any]) -> Dict[str, Any]`:
  - Initialize workspace state with defaults based on archetype and answers
  - Return workspace state dict
- `complete_setup(self, all_answers: Dict[str, Any]) -> SetupResult`:
  - Build profile, config, and workspace state
  - Write config.yaml to disk
  - Write business profile to disk
  - Initialize workspace state
  - Return SetupResult

### File: `kai/packaging/plugin.py`

**Model: PluginManifest**
- `name: str` — plugin name (e.g., "kai-marketing")
- `version: str`
- `description: str`
- `author: str`
- `compatibility: str` — minimum Kai version
- `skill_files: List[str]` — skill files to install in harness/skills/
- `knowledge_files: List[str]` — knowledge files to install in knowledge/
- `config_files: List[str]` — config files to install in workspace/
- `dependencies: List[str]` — Python package dependencies
- `hooks: List[Dict[str, str]]` — hooks to register: {event, handler_file}
- `install_instructions: str`

**Class: PluginPackager**
- `__init__(self, source_dir: str)`
- `create_manifest(self) -> PluginManifest`:
  - Scan source directory for skill, knowledge, and config files
  - Generate manifest
- `package(self, output_path: str) -> str`:
  - Create a distributable package (directory with manifest + files)
  - Return output path
- `validate_plugin(self, plugin_dir: str) -> Dict[str, Any]`:
  - Check plugin has required manifest
  - Check all referenced files exist
  - Check version compatibility
  - Return: {valid, issues}

**Class: PluginInstaller**
- `__init__(self, target_dir: str)`
- `install(self, plugin_dir: str) -> Dict[str, Any]`:
  - Read manifest
  - Copy skill files to harness/skills/
  - Copy knowledge files to knowledge/
  - Copy config files to workspace/
  - Return: {installed_files, errors}
- `uninstall(self, plugin_name: str) -> Dict[str, Any]`:
  - Read manifest to find installed files
  - Remove installed files
  - Return: {removed_files, errors}

### File: `kai/packaging/RUNBOOK.md`

A step-by-step operational guide covering:
- **Daily Operations**: checking status, reviewing proposals, approving actions, monitoring execution
- **Weekly Operations**: reviewing audit findings, checking watcher alerts, reviewing learnings, updating content
- **Monthly Operations**: full audit, performance review, budget reallocation, archetype tuning
- **Emergency Procedures**: using kill switches, handling compliance violations, rolling back actions
- **Common Scenarios**: onboarding a new client, running a campaign, handling a negative review spike, seasonal marketing adjustments
- **Troubleshooting**: common errors and their resolution
- Maximum 300 lines, practical and actionable

## Output Files

- `kai/packaging/__init__.py`
- `kai/packaging/install.py`
- `kai/packaging/setup.py`
- `kai/packaging/plugin.py`
- `kai/packaging/RUNBOOK.md`

## Acceptance Criteria

- All Python files parse as valid Python
- Installer checks Python version, dependencies, creates directories, and generates config
- SetupWizard has all 8 sections with appropriate question types and validation
- Section 3 (Service Area) is correctly marked as conditional on archetype
- Channel configuration covers all major platforms
- Plugin packaging includes manifest, packager, installer, and uninstaller
- RUNBOOK.md is practical, under 300 lines, and covers daily/weekly/monthly operations
- build_business_profile correctly maps wizard answers to BusinessProfile fields
- build_config generates valid YAML-compatible config dict
- No external dependencies in the core install/setup code (YAML parsing should try yaml, fall back to json)

## Reference Materials

- `config.example.yaml` — existing config template
- `install.sh` — existing install script patterns
- `kai/runtime/business_profile.py` — BusinessProfile for setup wizard mapping
- `kai/runtime/store.py` — workspace directory conventions
- `kai/flows/onboarding.py` (Task 079) — onboarding flow that setup wizard feeds into
- `kai/compliance/approval_routing.py` (Task 064) — RoutingConfig for approval preferences
- `kai/watchers/scheduling.py` (Task 072) — ArchetypeWatcherPacks for watcher configuration
- `harness/skills/` — skill file patterns for plugin packaging
