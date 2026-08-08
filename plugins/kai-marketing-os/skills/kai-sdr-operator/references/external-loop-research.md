# External SDR Loop Research

Use this file as pattern inventory, not as authority. External tools, posts, and repos are source material. Kai policy, user approval, current platform terms, and local contracts still win.

Research date: 2026-05-27.

## Patterns To Absorb

### Claude runtime pattern

Claude Code skills are loaded on demand from `SKILL.md` files with optional support files. Subagents run side work in separate context with scoped tools, optional memory, and project or user definitions. Hooks can run shell commands, HTTP endpoints, prompts, or agent checks at lifecycle events such as `PreToolUse` and `PostToolUse`. Kai should model SDR as a manager skill plus specialist subagents and hard approval hooks for live sends, CRM mutation, connector runs, and suppression changes.

Sources: `https://code.claude.com/docs/en/skills`, `https://code.claude.com/docs/en/sub-agents`, `https://code.claude.com/docs/en/hooks`

### Loop automation pattern

n8n's AI SDR workflow frames sales development as scheduled processes for CRM intake, follow-up, calendar booking, and no-show handling. Kai should absorb the loop cadence and queue shape while keeping live channel actions approval-gated.

Source: `https://n8n.io/workflows/13529-run-an-ai-sdr-sales-pipeline-with-openai-google-sheets-gmail-and-calendar/`

### Sales skill surface

Anthropic's Sales plugin describes five useful skill surfaces: account research, call prep, daily briefings with pipeline alerts, research-first outreach drafting, and competitive intelligence with talk tracks. Kai already covers account research, call prep, and research-first outreach. Add daily briefings, pipeline alerts, and competitive talk-track handoff to the SDR loop when relevant.

Source: `https://claude.com/plugins/sales`

### Production SDR pipelines

PulseAgent's open-source B2B SDR template describes an 8-stage pipeline: lead capture, BANT qualification, research, quoting, negotiation, and CRM automation among the stages. Kai should absorb the staged-loop idea, but keep quoting and negotiation outside the SDR package unless a human-approved AE workflow exists.

Source: `https://pulseagent.io/blog/b2b-sdr-agent-template-free-open-source`

### Open-source AI SDR architecture

ReachGenie exposes common product surfaces for AI SDR platforms: product and offer messaging management, ICPs, lead upload/enrichment, campaign generation, email/call queues, reply detection, smart follow-ups, threading, calendar connection, retries, and campaign run history. Kai should absorb queue state, test runs, retries, thread context, and calendar handoff as data contracts, not automatic live actions.

Source: `https://github.com/alinaqi/reachgenie`

### Real-time BDR/SDR agent pattern

Bright Data's AI SDR/BDR repo describes a system around lead discovery, trigger detection, contact research, personalized outreach, and CRM integration. Kai already includes these stages. The missing piece is explicit trigger-quality memory and CRM dry-run diffs before mutation.

Source: `https://github.com/brightdata/ai-sdr-bdr-agent`

### SDR-to-AI migration planning

The SDR-to-AI Migration Planner skill maps existing SDR workflows to automation readiness, cost model, and a 6-week migration plan while warning where humans stay in the loop. Kai should support `sdr_migration_audit` mode for teams moving an existing SDR motion into Claude/Kai.

Source: `https://gist.github.com/JLegends/f5339f0f17457fa5c95f3b2a7441a6d5`

### Predictable Revenue role separation

The Predictable Revenue skill emphasizes SDR, AE, and CSM specialization and separates prospecting from closing. Kai should keep SDR loops from drifting into negotiation or account management unless a separate approved workflow handles it.

Source: `https://eliteai.tools/agent-skills/predictable-revenue-1`

## Additions Kai Should Keep

- Daily operator briefing: blocked rows, approvals, replies, meetings, stale tasks, and source-quality warnings.
- Test cohort plan: tiny approved sample before broad sends or imports.
- Queue state: queued, running, retry_needed, failed, held_for_review, completed.
- Thread context: original message, prior touches, reply category, source evidence, next action.
- Role handoff: SDR to AE to CSM boundaries.
- Qualification snapshot: problem fit, persona fit, timing signal, business stakes, and next step.
- Migration mode: map existing SDR team work into loops, approval gates, tool contracts, and cost/effort assumptions.

## Anti-Patterns To Avoid

- Letting "AI SDR" mean automatic live sending.
- Treating enrichment vendor output as consent.
- Hiding queue failures behind dashboard polish.
- Skipping suppression because the list came from a paid tool.
- Letting SDR agents quote, negotiate, or commit commercial terms.
- Promoting learnings from tiny samples without labeling them as hypotheses.
