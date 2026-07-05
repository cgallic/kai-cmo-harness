# Task 002: Build profile loaders

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 1. Workspace and Business Understanding
**Priority:** P1
**Depends on:** 001
**Estimated complexity:** Medium

## Context

The BusinessProfile schema (Task 001) defines what a business looks like in Kai's data model, but profiles can come from many sources: YAML config files, onboarding interviews captured as markdown, the gateway's brand_config, and operator overrides. The loader layer is responsible for constructing BusinessProfile objects from any of these sources and merging partial profiles with clear priority ordering. This is how business context enters the system.

## Scope

Build `kai/loaders/profile_loader.py` and `kai/loaders/__init__.py` with functions that parse each source format into a partial BusinessProfile, plus a merge function that combines them.

## Detailed Requirements

### File: `kai/loaders/__init__.py`
- Package init that imports and re-exports the key public functions
- Include `__all__` listing

### File: `kai/loaders/profile_loader.py`

**Loader functions — each returns a partial `Dict[str, Any]` representing BusinessProfile fields:**

1. **`load_from_yaml(file_path: str) -> Dict[str, Any]`**
   - Parse a YAML file (like `config.yaml.example` or a dedicated `business.yaml`)
   - Map known YAML keys to BusinessProfile field paths
   - Handle the `products` array from config.yaml.example — map each product entry to the BusinessProfile structure
   - Handle nested workspace/brand config structures
   - If the YAML has a `business_profile` top-level key, treat it as a direct mapping
   - If the YAML has `products[0]` style entries, extract the first product as a partial profile
   - Return only the fields that were actually present in the YAML — do NOT infer or hallucinate missing data

2. **`load_from_markdown(file_path: str) -> Dict[str, Any]`**
   - Parse a markdown file (onboarding notes, interview transcripts, brand docs)
   - Extract structured data from markdown headings and lists:
     - H2 headings map to top-level profile sections (e.g., "## Offers", "## Target Audience")
     - Bullet lists under headings become list fields
     - Key-value patterns like "**Name:** Value" become field values
   - Support common interview note patterns:
     - "Business name: XYZ" or "Company: XYZ" -> identity.business_name
     - "Website: url" -> identity.website_url
     - "Industry: X" -> classification.industry
     - "Services:" followed by bullet list -> offers
     - "Target customers:" followed by description -> personas
     - "Service area:" or "Location:" -> geography
   - Be conservative — only extract clearly stated information
   - Return the partial dict with a `_source: "markdown"` metadata field

3. **`load_from_brand_config(brand_config: Dict[str, Any]) -> Dict[str, Any]`**
   - Accept a gateway-style brand config dict (see `KaiBrandProfile` in `kai/runtime/models.py`)
   - Map: id -> id, name -> identity.business_name, url -> identity.website_url, description -> identity.elevator_pitch
   - Map: primary_archetype -> classification.archetype, archetype_overlays -> metadata.archetype_overlays
   - Map: active_channels -> channels (create ChannelPresence stubs), proof_points -> trust
   - Map: ga_property, gsc_site -> metadata

4. **`load_from_overrides(overrides: Dict[str, Any]) -> Dict[str, Any]`**
   - Accept a flat or nested dictionary of override values
   - Support dot-notation keys: "identity.business_name" -> nested dict
   - Support direct nested dicts
   - This is the highest-priority source — operator explicitly saying "this field is X"

5. **`load_from_form(form_data: Dict[str, Any]) -> Dict[str, Any]`**
   - Stub interface for future UI/form input
   - Accept a dict with form field names, map to profile fields
   - Implement basic mapping, mark as `NotImplementedError` for unmapped fields
   - Include docstring describing the expected form field schema

**Merge function:**

6. **`merge_profiles(*partials: Dict[str, Any], priority_order: Optional[List[str]] = None) -> Dict[str, Any]`**
   - Merge multiple partial profile dicts into one
   - Default priority order (lowest to highest): yaml, markdown, brand_config, form, overrides
   - For scalar fields: higher priority wins
   - For list fields: concatenate and deduplicate (by name field if objects, by value if strings)
   - For dict fields: deep merge with higher priority overriding conflicting keys
   - Preserve `_source` metadata on each field if possible (track where each value came from)
   - Never fill in a field that no source provided — missing stays missing

7. **`build_profile(sources: List[Dict[str, Any]], priority_order: Optional[List[str]] = None) -> "BusinessProfile"`**
   - High-level function: takes a list of source dicts, merges them, instantiates a BusinessProfile
   - Import BusinessProfile from `kai.models.business_profile`
   - Handle instantiation errors gracefully — if a required field is missing, raise a clear error naming the field
   - Return the constructed BusinessProfile object

**Utilities:**

8. **`flatten_dotted_keys(d: Dict[str, Any]) -> Dict[str, Any]`**
   - Convert {"identity.business_name": "X"} to {"identity": {"business_name": "X"}}
   - Handle arbitrary nesting depth

9. **`deep_merge(base: Dict, override: Dict) -> Dict`**
   - Recursive dict merge utility
   - Lists are concatenated, not replaced
   - None values in override do NOT overwrite existing values (explicit removal requires a sentinel)

### Error Handling

- All loaders should catch file I/O errors and return empty dicts with error metadata
- YAML parsing errors should be caught and wrapped with file path context
- Markdown parsing should never crash — malformed markdown returns whatever was parseable
- The merge function should log (via a `warnings` list in metadata) when conflicting values are resolved

### Dependencies

- Use `yaml` (PyYAML) for YAML parsing — import with try/except, raise ImportError with helpful message if missing
- Use only stdlib for markdown parsing (re module) — no external markdown libraries
- Import BusinessProfile from `kai.models.business_profile` (created in Task 001)

## Output Files

- `kai/loaders/__init__.py`
- `kai/loaders/profile_loader.py`

## Acceptance Criteria

- [ ] `kai/loaders/profile_loader.py` contains all 9 functions listed above
- [ ] Each loader function has a clear docstring with parameter descriptions and return format
- [ ] `load_from_yaml` handles both `business_profile:` top-level key and `products:` array format
- [ ] `load_from_markdown` uses regex to extract key-value pairs and bulleted lists from markdown
- [ ] `merge_profiles` correctly implements priority ordering and deep merging
- [ ] `build_profile` imports from `kai.models.business_profile` and returns a BusinessProfile instance
- [ ] No fields are ever hallucinated or inferred — missing data stays missing
- [ ] YAML import has try/except with helpful error message
- [ ] `kai/loaders/__init__.py` exports all public functions via `__all__`
- [ ] The code is well-structured with clear section comments

## Reference Materials

- `kai/models/business_profile.py` (created by Task 001) — the schema being loaded into
- `config.yaml.example` — existing YAML config format to support
- `kai/runtime/models.py` — KaiBrandProfile structure for brand_config loader
- `kai/runtime/loader.py` — existing loader patterns in the runtime
- `gateway/models.py` — Pydantic import pattern
