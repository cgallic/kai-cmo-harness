# Kai Marketing OS — Operator Runbook

Day-to-day operational guide. Covers daily checks, weekly reviews, monthly planning, emergency procedures, and common scenarios.

---

## Daily Operations (5 min)

### Check Status
1. Open Claude Code in your project directory.
2. Run `/kai` to see the command menu and system status.
3. Review any pending approval requests — these are actions Kai wants to take but needs your OK.

### Review Proposals
- Kai queues proposals when it finds optimization opportunities.
- Each proposal shows: what it wants to do, expected impact, risk level, and estimated cost.
- **Approve** to execute. **Hold** to revisit later. **Reject** to discard.

### Approve Actions
- Low-risk actions (if auto-approve is enabled) execute without asking.
- Medium-risk actions show up as approval requests with full context.
- High-risk actions (ad spend increases, public content, compliance-sensitive) always require explicit sign-off.

### Monitor Execution
- Check `workspace/{business_id}/execution/` for recent run logs.
- Each run has a status: `running`, `completed`, `approved`, `held`, `failed`.
- Watcher alerts surface problems automatically — check notifications.

---

## Weekly Operations (15 min)

### Review Audit Findings
1. Run `/kai-audit` for a fresh marketing health check.
2. Compare against last week — look for score changes and new issues.
3. Focus on items marked "high priority" or "regression."

### Check Watcher Alerts
- Review the weekly digest (delivered via your configured notification channel).
- Watchers monitor: ranking changes, review velocity, competitor moves, site performance.
- Dismiss resolved alerts. Investigate persistent ones.

### Review Learnings
- Check `workspace/{business_id}/memory/` for patterns Kai has learned.
- Learnings include: what content performs, which channels convert, audience preferences.
- Correct any learnings that seem wrong — Kai will adjust.

### Update Content
- Review any content in `workspace/{business_id}/content/` awaiting publish.
- Run `/kai-gate` on drafts to verify quality scores before shipping.
- Publish approved content through your channels.

---

## Monthly Operations (30 min)

### Full Audit
1. Run `/kai-audit` with the `--full` flag for comprehensive analysis.
2. Review all checklist categories: SEO, content, email, ads, social, CRO.
3. Compare month-over-month trends.

### Performance Review
- Pull analytics for the month: traffic, conversions, revenue, ad spend, ROI.
- Run `/kai-analytics` to review attribution and channel performance.
- Identify the top 3 wins and top 3 areas needing improvement.

### Budget Reallocation
- Review spend by channel against performance.
- Shift budget from underperforming channels to winners.
- Update `config.yaml` budget settings if thresholds change.

### Archetype Tuning
- As the business grows, the archetype may need updating.
- A local service business expanding to 5+ locations should switch to `multi-location`.
- An ecommerce business adding B2B should add `professional-services` as an overlay.
- Re-run the setup wizard sections 3-4 to adjust.

---

## Emergency Procedures

### Kill Switch — Stop All Automated Actions
1. Set `auto_approve_low_risk: false` in your config.
2. Set `require_content_approval: true` if not already.
3. This halts all autonomous execution — everything queues for manual review.

### Compliance Violation Detected
1. Immediately pause the violating campaign or content.
2. Run `/kai-gate` on the content to identify specific violations.
3. Check the relevant policy reference in `harness/references/`.
4. Fix the violation, re-run quality gates, get approval before republishing.
5. Log the incident in `workspace/{business_id}/audit/` for the compliance record.

### Rolling Back an Action
1. Find the run ID in `workspace/{business_id}/execution/`.
2. Review the run's outputs and artifacts.
3. Manually revert the action in the affected platform (ad manager, CMS, email tool).
4. Mark the run as `failed` with a note explaining the rollback reason.
5. Add the pattern to blocked tactics in your business profile to prevent recurrence.

### Negative Review Spike
1. Run `/kai-audit` focusing on review signals.
2. Check review platforms directly for new negative reviews.
3. Draft responses using `/kai-write` with the review response template.
4. Investigate root cause — is it a service issue or a coordinated attack?
5. Adjust review monitoring frequency to `Comprehensive` temporarily.

---

## Common Scenarios

### Onboarding a New Client
1. Run the installer: `from kai.packaging.install import Installer; Installer(".").install()`
2. Run the setup wizard: answer all 8 sections with client details.
3. Run `/kai-audit` for the initial marketing health check.
4. Review proposals and approve initial quick wins.
5. Set up a content calendar: `/kai-content-calendar`.
6. Configure watcher alerts for the client's key metrics.

### Running a Campaign
1. Start with a brief: `/kai-brief` to define goals, audience, and channels.
2. Generate assets: `/kai-ad-campaign` for ads, `/kai-email-system` for emails.
3. Run quality gates on all assets before launch.
4. Launch and monitor daily for the first week.
5. Review performance at day 7, day 14, and day 30.

### Seasonal Marketing Adjustments
1. Review last year's seasonal data (if available).
2. Update content calendar for seasonal keywords and offers.
3. Adjust ad budgets — increase for peak season, decrease for slow periods.
4. Prepare seasonal landing pages: `/kai-landing-page`.
5. Set up seasonal email sequences: `/kai-email-system`.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Quality gates reject everything | Thresholds too strict or content needs work | Check Four U's scores — aim for 12+/16. Remove banned words. |
| Config file won't parse | YAML syntax error | Run through a YAML validator. Check for tab characters (use spaces). |
| Watchers not firing | Watchers disabled or quiet hours active | Check `enable_watchers` in config. Verify quiet hours window. |
| Missing dependencies | pyyaml or optional packages not installed | Run `pip install pyyaml`. Check `/kai` status for dependency warnings. |
| Proposals stuck in "held" | Nobody is reviewing them | Check approval preferences. Consider enabling auto-approve for low-risk. |
| Wrong archetype selected | Business type changed or was misidentified | Re-run setup wizard section 4. Update config.yaml archetype field. |
| Plugin install fails | Missing manifest or file references | Run `PluginPackager.validate_plugin()` on the plugin directory. |
| Content scores low on "Unique" | Generic content without proprietary insight | Add real data, case studies, named tools, or original research. |

---

## File Reference

| File | Purpose |
|------|---------|
| `config.yaml` | All runtime settings — edit here to change behavior |
| `workspace/{id}/config/business_profile.json` | Structured business understanding |
| `workspace/{id}/workspace_state.json` | Current operational state |
| `workspace/{id}/audit/` | Audit history and compliance records |
| `workspace/{id}/memory/` | Learned patterns and preferences |
| `workspace/{id}/execution/` | Run logs and execution history |
| `workspace/{id}/content/` | Generated content awaiting review |
| `.kai-plugins.json` | Installed plugin registry |
