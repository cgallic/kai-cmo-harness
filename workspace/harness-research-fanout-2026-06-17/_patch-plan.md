# Patch Plan

## Priority Order

1. P0 transcript safety patch
   - Add `harness/references/transcript-video-research-rules.md`.
   - Disable unofficial YouTube transcript/subtitle/audio fallbacks by default in `scripts/knowledge_cloner/transcription.py`.
   - Update `scripts/knowledge_cloner/README.md`.

2. P0 source registry patch
   - Add `harness/references/marketing-platform-source-registry.json`.
   - Update `harness/references/research-fanout-best-practices.md`.
   - Update `harness/references/research-fanout-vertical-registry.json`.

3. P1 routing patch
   - Update `AGENTS.md`, `CLAUDE.md`, `knowledge/_index.md`.
   - Update `knowledge/playbooks/transcript-to-content-ops.md`.
   - Update `harness/skills/kai-repurpose/SKILL.md` and `harness/skills/kai-video/SKILL.md`.

4. P1 contract and gate patch
   - Update `harness/skill-contracts/podcast-repurpose.yaml`.
   - Update `harness/skill-contracts/video-clip.yaml`.
   - Add quality policies:
     - `scripts/quality/policies/openai-ad.yaml`
     - `scripts/quality/policies/social-post.yaml`
     - `scripts/quality/policies/video-clip.yaml`
     - `scripts/quality/policies/podcast-repurpose.yaml`
     - `scripts/quality/policies/newsletter.yaml`

5. P2 future executable enforcement
   - Add a broad official-source monitor for `marketing-platform-source-registry.json`.
   - Add transcript provenance lint for `_transcript-ledger.md`, `_quote-bank.md`, blocked source terms, and quote limits.
   - Add quality gate enforcement for `require_policy_ref` and `require_secondary_refs`.
   - Add platform requirements crosswalk inside vertical registry.

## Validation Commands

Run:

```powershell
python -m json.tool harness\references\research-fanout-vertical-registry.json > $null
python -m json.tool harness\references\social-platform-source-registry.json > $null
python -m json.tool harness\references\marketing-platform-source-registry.json > $null
python - <<'PY'
from pathlib import Path
import yaml
for p in Path("harness/skill-contracts").glob("*.yaml"):
    yaml.safe_load(p.read_text())
for p in Path("scripts/quality/policies").glob("*.yaml"):
    yaml.safe_load(p.read_text())
print("yaml ok")
PY
git diff --check -- AGENTS.md CLAUDE.md knowledge\_index.md harness\references harness\skill-contracts harness\skills scripts\knowledge_cloner scripts\quality\policies workspace\harness-research-fanout-2026-06-17
python -m py_compile scripts\knowledge_cloner\transcription.py
```

Optional after the next gate patch:

```powershell
python scripts\quality_gates\golden_check.py
python scripts\doctor.py
```

