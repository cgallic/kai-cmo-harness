# Marketing growth library draft review

Status: local draft for independent review. No ECO SHIPPED/CLOSED verdict is asserted. Independent craft review and exact-version human approval remain outstanding (C/E); no commercial outcome has been measured (O).

## Change surface

`harness/references/marketing-growth-library/` holds all 30 prompts, the selection catalog, source receipt, packaging guidance and separate fictional examples. Existing `/kai` and `/kai-growth-plan` skills in both versions discover it. `scripts/marketing_library.py` is a stdlib, read-only route validator; it does not classify businesses itself or execute a selected skill. Existing plugin asset synchronization includes the validator and reference files in both payloads.

No runtime modules, workflow registry, accounts, publishers, credentials, client stores, learning engines, campaigns or schedules are changed. Client labels, evidence references and confidence are attestations, not authentication or tenant authorization.

## Author-run checks

- Full suite: **1346 passed**, 212 existing datetime deprecation warnings, with missing test dependencies installed into a temporary virtual environment.
- Focused library/skill parity/link/capability suite: **290 passed**.
- `python scripts/doctor.py --ci`: passed hard checks. Its final configured message concerns repository checks, not client account access.
- `python scripts/quality_gates/golden_check.py`: **6/6 passed**.
- `python scripts/sync_plugin_assets.py --check`: passed, 33 asset entries.
- Banned-word checks on prompt library and README: passed Tier 1; ordinary journey/impact qualifiers flagged for editorial review.
- Earlier runs stopped on missing FastAPI/dotenv/async-test dependencies. Those environment issues were resolved in the temporary environment before the passing runs above.
- Four U's/model judging, live collectors, actual prompt generation, client account tests, installation, publishing and commercial outcome evaluation: **not run**. This is a prompt/context package, not publishable client copy or proof of business results.

## Independent review instructions

Compare the branch to base `46fe97f`. Read canonical files before plugin mirrors. Confirm:

1. R0 + P1–P23 + C1–C6 preserve all intents, adaptations and documented practices; no private working links, conversation IDs or actual customer records appear.
2. Seven profiles, unresolved fit and hybrids remain evidence-based; no universal target, deadline, baseline zero, software stage or vendor default slips into portable configuration.
3. Hybrid goals and evidence stay per offer; zero requires source evidence; quotes, estimates, buyer/user roles, owner redaction/sharing and cross-client reuse remain correctly scoped.
4. The helper can report draft readiness only. Evidence references are not fetched or authenticated. It cannot grant permission, execute, create outcomes or emit a verdict.
5. Existing provenance, channel, voice, approval, outcome and learning interfaces govern downstream work. A simulation or different verifier name is not proof of live performance or independent review.
6. Run the focused suite, full suite, doctor, golden corpus and plugin sync check. Assess marketing craft separately from mechanical tests. Keep the PR draft until independent review and applicable checks pass; do not merge based only on this author's report.
