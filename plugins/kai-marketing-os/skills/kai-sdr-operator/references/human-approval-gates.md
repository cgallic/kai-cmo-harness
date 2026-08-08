# Human Approval Gates

SDR packages can prepare actions. They do not execute live actions without approval.

## Risk Tiers

| Tier | Examples | Approval |
|---|---|---|
| `read_only` | Read local files, inspect trusted exports, score accounts, draft copy. | No approval unless data is sensitive. |
| `paid_read` | Run a connector that spends credits or billable API calls. | Sales owner or operator approval. |
| `data_export` | Export, enrich, or move contact/account data between systems. | Sales owner and compliance owner approval. |
| `crm_mutation` | Create or update CRM records, tasks, notes, owners, stages, or associations. | CRM owner approval. |
| `message_mutation` | Add leads to sequencer, send email, send DM, SMS, call, or calendar invite. | Sales owner and compliance owner approval. |
| `regulated` | Healthcare, finance, legal, employment, housing, credit, minors, political, or sensitive data. | Human review required before production. |

## Required Approval Record

Every approval request must include:

```text
approval_id,action_type,risk_tier,system,account_or_list_scope,row_count,fields_touched,cost_or_credit_cap,dry_run_path,evidence_ids,suppression_list_id,rollback_plan,requested_by,approver,decision,decision_at
```

## Approval Checklists

### Connector Run

- Source and vendor terms are reviewed.
- Fields requested are minimal.
- Cost or credit cap is set.
- Rate and volume limits are set.
- Output destination is declared.
- Sensitive-data risk is checked.
- Dry-run preview exists.

### CRM Mutation

- Duplicate policy is declared.
- External ID or merge key is present.
- Owner assignment is clear.
- Stage mapping is clear.
- Triggered workflows are known.
- Rollback or cleanup plan exists.

### Sequencer Import

- Sender identity is complete.
- SPF/DKIM/DMARC and sender-risk review are done.
- Suppression list is synced.
- Opt-out language is present.
- Claim evidence is attached.
- Campaign is paused or queued, not auto-activated.

### Message Send

- Sequence passed `cold-email.yaml`.
- Recipient rows passed source, suppression, relevance, and claim gates.
- Send volume is within approved limits.
- No deceptive subject lines.
- No sensitive personal attributes.
- Opt-out processing path exists.

### Phone Or SMS

- TCPA and regional consent risk are reviewed.
- Number source and business relationship are clear.
- Script has opt-out or no-call handling when required.
- Call recording consent rules are reviewed if recording is used.
- Routing and logging path are approved.

## Stop Conditions

Stop and request human decision when:

- Source rights are unclear.
- Suppression source is missing.
- A connector would spend credits.
- A live system would change.
- A contact asks to opt out.
- A reply indicates complaint, legal concern, harassment concern, or sensitive topic.
- A regulated category is detected.
- A user asks to bypass terms, access controls, or policy.
