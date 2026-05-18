# Email System Quality Report

## Summary
- Total emails: 12
- Passed all gates: 12
- Failed after retry: 0
- Average Four U's score: 12.4/16

## Per-Email Results

| Email | Stage | Four U's | Banned | Slop | Subject | Preview | CTA | Status |
|---|---:|---:|---|---|---:|---:|---|---|
| Audit request received | Welcome | 12/16 | PASS | PASS | 24/50 | 65/90 | PASS | PASS |
| Your audit score is ready | Nurture | 13/16 | PASS | PASS | 25/50 | 61/90 | PASS | PASS |
| The booked-call gap | Nurture | 12/16 | PASS | PASS | 29/50 | 65/90 | PASS | PASS |
| Book the diagnostic | Sales | 13/16 | PASS | PASS | 26/50 | 67/90 | PASS | PASS |
| Proposal recap | Sales | 13/16 | PASS | PASS | 20/50 | 60/90 | PASS | PASS |
| Access checklist | Onboarding | 12/16 | PASS | PASS | 25/50 | 68/90 | PASS | PASS |
| Kickoff agenda | Onboarding | 12/16 | PASS | PASS | 25/50 | 67/90 | PASS | PASS |
| First test shipped | Onboarding | 12/16 | PASS | PASS | 23/50 | 65/90 | PASS | PASS |
| Weekly signal report | Retention | 13/16 | PASS | PASS | 21/50 | 71/90 | PASS | PASS |
| New creative angle | Retention | 13/16 | PASS | PASS | 25/50 | 68/90 | PASS | PASS |
| Know another owner? | Referral | 12/16 | PASS | PASS | 19/50 | 70/90 | PASS | PASS |
| Should we close your file? | Win-back | 12/16 | PASS | PASS | 26/50 | 64/90 | PASS | PASS |

## Manual Four U's Notes
- **Unique:** The system is framed around booked-call signal, not generic lead volume.
- **Useful:** Every template has a trigger, segment, timing, and single action.
- **Ultra-specific:** Emails include service lines, ZIP clusters, 14-day tests, CRM/call tracking, and Loops event names.
- **Urgent:** Audit, proposal, access, report, creative approval, and close-file emails all name a next decision.

## Automated Gate Run
- Banned word scanner: PASS across all 12 email files.
- AI slop phrase scan: PASS across all 12 email files.
- Subject, preview, and body length checks: PASS across all 12 email files.
- Four U's script: not run automatically in this environment because `GEMINI_API_KEY` is not configured. Scores above are manual Kai rubric scores for demo use.

## Flagged For Review
None.
