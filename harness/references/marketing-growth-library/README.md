# Marketing growth prompt library

> **Use when:** The assistant needs to select business-appropriate research and growth work, adapt a reusable prompt, or prepare a client intelligence request.

Draft module, invoked through the existing `/kai` router or `/kai-growth-plan`. It adds no command, workflow registration, scheduler, account connection, publisher or learning engine. A local package is not an installation or a live campaign.

## Entry points

- [R0 and the complete 30-prompt library](prompts.md#r0): read the business configuration, operating rules and profile table before extracting an individual prompt.
- [Catalog](catalog.json): stable R0, P1–P23 and C1–C6 IDs, applicability, evidence requirements, outputs, downstream IDs and existing skill handoffs.
- [Fictional examples](examples.md): distinct outcome units and hybrid handling without customer history.
- [Source receipt](source-receipt.json): verified source version/hash and sanitization scope. The derivative intentionally differs from the private source.

## Selection contract

The receiving assistant performs R0 using authorized business evidence. The catalog is a context index, not a keyword classifier or a permission grant. Explain each profile choice, confidence and evidence. Multiple profiles are valid; no supported fit means unresolved, with no fallback to software, phone-led services or a named vendor. Ask only material missing questions. Inspect authorized context before asking.

Use actual interaction channels: call, form, cart, reservation, walk-in, demo, support or procurement. Distinguish purchaser, user, beneficiary and gatekeeper. Persona hypotheses are research tools, not verified people or platform targeting categories. Never fabricate quotes, infer sensitive traits or target children.

For hybrids, keep each offer's goal, conversion unit and journey separate. A paid order, completed job and retained subscription cannot be summed into one conversion count. Targets, deadlines and units come from this business; an unknown baseline stays `null` until reconciled. Zero needs the same evidence as any other number. Raw records, refunds, cancellations, fulfillment and contribution economics govern the definition.

The optional stdlib helper validates an assistant-prepared selection and reports `ready_to_draft` or `deferred` for the requested prompt IDs. It reads input and writes JSON only to stdout; it never runs a prompt, collector or skill, stores client history, calls a model, or publishes. Readiness means evidence references were supplied, not that this helper fetched or authenticated them. The trusted operator must check the cited evidence and permissions. Explicit requests do not bypass missing evidence.

From the repository or plugin root:

```bash
python scripts/marketing_library.py --input /path/to/client-private-selection.json
```

Selection input fields:

| Field | Shape and meaning |
|---|---|
| `client_id` | Nonempty isolated workspace/brand identity; a label alone is not authorization |
| `profiles` | List of `{id, confidence, rationale, evidence_refs}`; confidence is `low`, `medium` or `high`; empty means unresolved |
| `goal` | `{metric, unit, target, baseline, baseline_ref, period, timezone, reversal_rules}`; unknown values are `null`; numbers must be finite |
| `offers` | List of `{id, profile_ids, goal}`; required for hybrids, with separate outcomes and coverage of each selected profile |
| `evidence` | List of `{kind, ref, status}` with status `verified`, `hypothesis` or `unknown`; hybrid records also require `offer_id`; required kinds must be present for every offer |
| `prompt_ids` | Requested subset, or omit for R0/P1/P2/P3; only validated IDs are accepted |

`kind` is one of the catalog's `requires` values. Add references, never raw transcripts, identities or credentials. `baseline` evidence requires a reconciled numeric goal baseline and source, including every offer for a hybrid. The helper refuses extra input fields; it accepts no execution, approval or publication switch. It does not authenticate the client label, verifier or referenced permissions.

Each catalog entry declares `required_goal_fields` separately from evidence requirements. P3 can map an observed journey with a selected profile and verified journey evidence before a target or reporting window is known. It leaves those unknowns null. Goal-dependent planning, measurement, evaluation and channel work retain their configured-goal requirements; discovery readiness grants no downstream readiness. Numeric target/baseline values outside the helper's supported finite magnitude are rejected as invalid input.

## Existing contracts govern the handoff

| Need | Existing seam |
|---|---|
| Product discovery and owned context | `/kai-start`, project `MARKETING.md`, existing workspace/brand records |
| Baseline, journey, tracking and CRO | `/kai-funnel-audit`, `/kai-analytics`, `/kai-cro`; [audit provenance](../audit-data-provenance.md) |
| Offers, messages, creative and channels | Catalog `handoff_skills`; [brief schema](../../brief-schema.md) and the applicable [skill contracts](../../skill-contracts/campaign.yaml) |
| Quantitative/client-facing claims | Declare `sales_external`, `onboarding_connected` or `internal_demo`; collect with `python -m scripts.audit.collect --url <url> --mode <mode> --workflow <workflow> --out <data-folder>` before writing; cite collector evidence from `kai-data.json` / identical audit alias `audit-data.json`; gaps go in `_data-gaps.md`; apply provenance lint before handoff |
| Publishable assets | Applicable quality and platform policy gates, live policy checks when needed, exact-version human approval and existing action mandates; no authorization inherited from this library |
| Voice and corrections | [Customer voice scope](../../../docs/system/customer-voice-engine.md): same brand/writer/channel, approved sources; no cross-client corpus |
| Experiments and outcomes | [Outcome policy](../../../docs/system/models-and-outcome-learning.md), `kai/analytics/rl.py`: predeclared baseline/source/direction/scale/window/actor; independent mature observation; missing baseline blocks policy choice |
| Lessons and verdicts | [Learning loop](../../../docs/system/learning-loop.md), `/kai-retro`, [ECO doctrine](../../../docs/system/eco-completion-standard.md), [floors](../../eco-floors.yaml); author submits evidence, independent verifier issues the verdict |

Do not turn a draft into `rl_experiment`, a reward observation, a content-log publish record or an ECO verdict. Record prepared, approved, executed and measured states separately. A different agent name does not prove independence. Never duplicate the existing simulation adapter or label synthetic performance as live results. Phone Capture Fit Rule applies only when evidence shows the business is phone-led; compare alternatives, name no vendor by default and disclose ownership when relevant. No guessed lost-call revenue.

## Client intelligence and privacy

C1–C5 are prepared for clients to run in their own authorized context. Owner review, redaction, recipient, purpose and scoped sharing must precede vendor ingestion. C6 promotes only approved deidentified patterns, with provenance, conflicting evidence and quote/public-use permission preserved. Provider buyers and a client's end customers remain distinct.

Keep records, memory, credentials and destinations isolated per client. Open Brane business filters are not tenant authorization; separate deployments are required across customer trust boundaries. Never pool customer dossiers. Client claims, examples and permissions must not become portable defaults.

## Review and validation

Run `python -m pytest tests/test_marketing_library.py tests/test_skill_versions.py tests/test_skill_link_integrity.py tests/test_capability_manifest.py -q`, `python scripts/doctor.py --ci`, `python scripts/quality_gates/golden_check.py` and `python scripts/sync_plugin_assets.py --check` from a source checkout. These checks inspect packaging and selection, not marketing performance.

Independent review should compare the change against its base commit, read all 30 prompts for preserved intent, verify sanitization and handoff boundaries, inspect negative selection tests, and run the checks above. Do not merge or claim ECO readiness from the author's tests alone. Any eventual output must satisfy its own discipline gates and independent ECO floor.
