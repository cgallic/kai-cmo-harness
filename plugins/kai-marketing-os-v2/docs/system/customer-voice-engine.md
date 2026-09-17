# Customer voice and outcome engine

## Implemented scope

The canonical Python content engine passes a scoped customer voice packet
through briefing, drafting, revision and quality evaluation. Those calls use
the shared model router. Host-executed Claude/Codex skills and independent
legacy scripts remain separate execution surfaces.

Customer voice is stored in SQLite at CMO_DATA_DIR/customer-voice.sqlite.
All imports are explicit; the engine no longer searches the operator's home
directory for a voice guide. This repository contains no customer voice corpus
to migrate. No profiles or claimed customer preferences were fabricated.

## Voice identity and provenance

Profiles are keyed by brand, writer and channel. A packet layers the same
brand's company profile, individual writer profile and channel profiles.
Banned phrases combine across layers. Resolve contradictory prose rules
through an explicit profile update.

Profiles require a source reference and approving operator/customer identity.
Updates retain history and require the current expected_version. These fields
are attestations from a trusted operator, not an authentication mechanism.

Examples preserve original text, customer final text, correction category,
reviewer, reason, source, authorship origin, channel, audience and train/holdout
split. Exact text reuse across train and holdout is rejected within a writer.
Near-duplicate detection is not implemented; operators must avoid paraphrased
test leakage when curating the corpus.

Generation retrieves only the same brand, writer and channel. It excludes
mismatched audience segments, held-out examples, factual corrections as voice
examples, and AI-approved examples from automatic voice learning. Topic
selection uses lexical overlap, not embeddings. Four examples are retrieved
by default, with each source passage capped at 2,400 characters.

An explicitly requested writer must have a scoped profile. The default
company writer can run without one; metadata says voice is unconfigured.
Multi-brand workspaces also stop importing root-level learned defaults/winners
as customer context; their learning root is workspace/brand-id and runtime
memory remains explicitly brand-scoped.

## Editorial feedback and gates

Feedback links to a recorded run and retains the last presented draft and
customer final. Identical resubmission is idempotent; conflicting feedback for
the same run is rejected. Feedback creates an example, not a standing rule.
Only explicit profile updates change standing instructions.

Metrics distinguish reviewed assets, acceptance rate, unchanged acceptance
rate and edit fraction from business rewards. Cost per accepted asset includes
all recorded generation and judging estimates; it stays null if any call has
unknown pricing. This is an estimate, not an invoice or provider cost audit. Edit fraction is character
sequence difference, not editing time. Unchanged acceptance measures the
presented draft after automatic revisions, not necessarily its first draft.

A prohibited customer phrase cannot be averaged away by a high overall score.
The deterministic cache includes brand, full profile contents, model setting,
category weights, content and file path. Cached results are copied before
return. LLM evaluations are not cached.

The semantic judge returns a verdict and issues with exact draft quotes,
rule references and revision directions. Invented quotes or malformed verdicts
are rejected. Configured profiles require human review because the judge is
not yet calibrated for those customers. A model PASS does not authorize
automatic publication. Existing human approval workflows remain applicable.

The CLI runs blind held-out comparisons, hiding the preferred variant and
correction rationale. It reports agreement, errors and sample count; it never
promotes a judge automatically. No customer calibration score or business lift
is asserted by this implementation.

Revisions preserve unaffected passages and voice context. They may shorten
when a listed issue requires it and remove unsupported claims. There is no
blanket instruction to preserve every number or inflate length.

## Provider execution

ContentClient routes content stages through LLMRouter. The gemini_fn injection
name remains for compatibility. Provider-specific transport stays in the router.

Stage model overrides:
- KAI_CONTENT_BRIEF_MODEL
- KAI_CONTENT_PIPELINE_MODEL
- KAI_CONTENT_REVISION_MODEL
- KAI_CONTENT_QUALITY_REVIEW_MODEL

AGENT_DEFAULT_MODEL remains a general override. Existing YAML Gemini model,
key and timeout settings are honored for Gemini. Model IDs must match the
selected provider. KAI_CONTENT_MAX_TOKENS defaults to 8192.
Truncated/empty results are rejected.

Draft/revision calls and blocking brief calls use worker threads. Call records
retain prompt, hash, model, stage, usage, latency, output or failure type.
SDK retry behavior is unchanged; there are no nested retries or silent fallbacks.

## Replay and business outcome joins

The database records context versions, briefs with drafts, revisions, gate
reports including judge calls, final assets, publication references and model
calls. Failure exits retain failure and call records.

Replay regenerates the stored writing prompt through a candidate model. It has
no publication path. Replaying incurs a new inference request when credentials
are connected. Full prompts and drafts are sensitive customer data: keep this
database private and outside public git. Export is explicitly brand-scoped.

An optional rl_decision_id must reference the brand's unsettled content_pipeline
decision. The run reserves the decision transactionally before generating,
preventing concurrent runs from executing the same experiment. A failed or
unpublished reserved run retains its history and cannot be reused by a new run;
start a new predeclared decision for a new attempt.
When the existing publisher returns a real URL, the decision binds
to the run, exact final SHA-256, receipt URL and time. A later collector
measurement joins through that binding. Editorial scores never become rewards.

Collectors authenticate identity and verify receipt/measurement upstream.
Publisher success is a receipt, not independent live readback.
Scheduled collectors are not automatically wired to this interface.
Manually published drafts need a separate execution-binding integration;
automatic binding here covers engine-published content.

## Operator commands

Each command reads a JSON object of keyword arguments from --input.

~~~bash
python -m kai.voice --db data/customer-voice.sqlite profile --input profile.json
python -m kai.voice --db data/customer-voice.sqlite example --input example.json
python -m kai.voice --db data/customer-voice.sqlite feedback --input feedback.json
python -m kai.voice --db data/customer-voice.sqlite packet --input scope.json
python -m kai.voice --db data/customer-voice.sqlite metrics --input brand.json
python -m kai.voice --db data/customer-voice.sqlite export --input brand.json
python -m kai.voice --db data/customer-voice.sqlite calibrate --input judge.json
python -m kai.voice --db data/customer-voice.sqlite replay --input replay.json
python -m kai.voice --db data/customer-voice.sqlite outcome --input outcome.json
~~~

Profile input, illustrative schema only:

~~~json
{
  "brand": "customer-id",
  "writer": "founder",
  "channel": "*",
  "rules": ["A customer-approved instruction backed by the source below."],
  "banned_phrases": ["a customer-prohibited phrase"],
  "source_ref": "approved-guide-reference",
  "approved_by": "verified-customer-or-operator"
}
~~~

Use the returned version as expected_version when replacing a profile.

Example requires brand, writer, channel, original, final, source_ref, reviewer
and reason. Optional: category (voice/facts/positioning/structure/preference),
audience, topic, split (train/holdout), accepted, origin
(customer_written/customer_edited/ai_approved), example_id.

Feedback: brand, run_id, final, reviewer, reason; optional category, accepted,
split. Packet: brand, writer, channel; optional audience, topic, limit.
Export/metrics: brand; export optionally takes run_id.
Calibration: brand, writer, channel; optional model, seed.
Replay: brand, run_id; optional candidate model.
Outcome: brand, run_id, rl_db, decision_id, value, observed_at, verifier,
evidence_ref; optional cost. Execution time comes from the binding.

~~~bash
python scripts/harness_cli.py generate --format linkedin --site customer-id --keyword topic --writer founder --audience business-owners
~~~

The site must exist in workspace configuration. --rl-decision-id is optional
and requires KAI_RL_DB.

## Verification boundaries

Offline regression tests exercise isolation, cache scope, versioning,
corrections, holdout separation, invented-quote rejection, review holds,
routing, replay and outcome binding.
No paid comparison, customer calibration, production migration or measured
marketing improvement is established by those tests.
