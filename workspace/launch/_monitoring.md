# Post-Launch Monitoring Plan

**Launch date:** April 9, 2026

---

## Check-In Schedule

| Day | Date | Focus | Actions |
|-----|------|-------|---------|
| **T+1** | Apr 10 | First 24h pulse | Check GitHub stars, clones, issues. Monitor email open rates. Check social engagement. Fix any install bugs reported. |
| **T+3** | Apr 12 | Activation check | How many installs → first command run? Check GitHub issues for onboarding friction. Publish deep-dive blog post. |
| **T+7** | Apr 16 | Week 1 retro | Full metrics review (table below). Identify top-performing channel. Double down or adjust. Kill underperformers. |
| **T+14** | Apr 23 | Two-week retro | Metric trends. Community growth. Content performance. Decide on next content batch. |
| **T+30** | May 9 | Month 1 retro | Full performance review against success metrics. Plan sustain phase or next push. |

---

## Metrics to Watch

### GitHub (check daily for first week)

| Metric | Target (30 days) | Check via |
|--------|:-----------------:|-----------|
| Stars | 500+ | `gh api repos/cgallic/kai-cmo-harness` |
| Clones (unique) | 200+ | Repo insights → Traffic |
| Forks | 20+ | Repo page |
| Open issues | Monitor (not a target) | Issues tab |
| Contributors | 5+ | Contributors page |

### Email (check after each send)

| Metric | Benchmark | Check via |
|--------|:---------:|-----------|
| Open rate | 25%+ | Loops dashboard |
| Click rate | 3%+ | Loops dashboard |
| Unsubscribe rate | <0.5% | Loops dashboard |
| Reply rate | Track (any is good) | Inbox |

### Blog (check at T+3, T+7, T+14)

| Metric | Target (30 days) | Check via |
|--------|:-----------------:|-----------|
| Page views | 2,000+ combined | Analytics |
| dev.to views | 500+ | dev.to dashboard |
| Hashnode views | 200+ | Hashnode dashboard |
| Medium views | 300+ | Medium stats |
| Time on page | 3min+ | Analytics |

### Social (check daily for first week)

| Metric | Target | Check via |
|--------|:------:|-----------|
| Impressions | 10,000+ (30 days) | Platform analytics |
| Engagement rate | 2%+ | Platform analytics |
| Link clicks | Track | UTMs |
| Reddit upvotes | 50+ per post | Reddit |
| HN points | 20+ | HN |

### KaiCalls Cross-Sell (check weekly)

| Metric | Target (30 days) | Check via |
|--------|:-----------------:|-----------|
| meetkai.xyz → KaiCalls clicks | 50+ | UTM tracking |
| KaiCalls trial signups (from Kai traffic) | 10+ | Attribution |

---

## Decision Triggers

### Double down if:
- A social post gets 2x expected engagement → create follow-up content on that angle
- A Reddit community responds well → do an AMA or follow-up post
- Blog post gets >500 views in 48h → promote with paid boost or cross-post wider
- Email reply rate >2% → personal follow-ups to every reply

### Adjust if:
- Install→first-command drop-off >80% → onboarding is broken, fix /kai-start immediately
- Email open rate <15% → test new subject lines on follow-up sends
- Zero GitHub issues in 72h → people aren't trying it, push harder on activation emails
- Social engagement <0.5% → messaging isn't landing, test different angles

### Kill if:
- A platform gets <100 impressions after 3 posts → stop posting there, reallocate effort
- A specific content angle gets zero engagement → don't produce more of that angle

---

## Content to Produce Based on Early Results

| Signal | Produce |
|--------|---------|
| FAQ questions repeat in issues/replies | FAQ blog post addressing top 5 questions |
| Users share screenshots of Kai output | "What people are building with Kai" roundup post |
| Specific command gets disproportionate usage | Tutorial: "How to [command] in 5 minutes" |
| Install friction reported | Updated install guide / troubleshooting doc |
| Feature requests cluster | Roadmap post: "What's coming to Kai" |
| KaiCalls interest from Kai users | Dedicated cross-sell email to Kai installers |
