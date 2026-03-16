# Deep Research Prompts for Marketing Frameworks

> **Use when:** You need to generate comprehensive marketing frameworks for channels not yet covered. Run these prompts with Claude's extended thinking or deep research capabilities.

---

## Prompt Engineering Notes

These prompts are designed to extract expert-level, practitioner knowledge—not generic marketing advice. Each prompt:
- Requests specific mental models and decision frameworks
- Asks for failure modes and anti-patterns (what NOT to do)
- Requires quantitative benchmarks with confidence intervals
- Demands business-model-specific variations (B2B, B2C, SaaS, DTC, Crypto)
- Specifies output format for AI agent consumption

---

## 1. Email & Lifecycle Marketing Framework

```
You are an expert email marketer who has managed lifecycle programs for companies from seed stage through IPO, across B2B SaaS, DTC e-commerce, fintech, and crypto. You've personally built email programs generating $10M+ ARR and have deep expertise in deliverability, automation architecture, and behavioral segmentation.

Create a comprehensive Email & Lifecycle Marketing Framework covering:

## PART 1: STRATEGIC FOUNDATIONS

### Email Program Architecture
- The 5 lifecycle stages and their primary email objectives (Acquisition → Activation → Engagement → Retention → Reactivation)
- How to structure an email team: when to hire specialists vs. generalists, agency vs. in-house decision framework
- Tech stack selection criteria: ESP evaluation matrix (Klaviyo vs. Customer.io vs. Braze vs. Iterable), CDP integration requirements, deliverability monitoring tools
- The "Email P&L" mental model: how to calculate true email revenue attribution vs. last-click inflation

### Deliverability Engineering
- IP warming schedules with specific volume ramps (day 1-30 protocols)
- Domain authentication checklist: SPF, DKIM, DMARC configuration with failure modes
- Inbox placement factors ranked by impact: sender reputation signals, engagement metrics, content triggers
- The spam trap taxonomy: pristine vs. recycled vs. typo traps, detection and remediation
- ISP-specific quirks: Gmail tabs, Outlook clutter, Apple Mail Privacy Protection implications
- List hygiene protocols: sunset policies by engagement tier, re-permission campaigns, hard vs. soft bounce handling

## PART 2: SEQUENCE ARCHITECTURE

### Welcome Sequences
- Optimal email count and timing by business model:
  - B2B SaaS: [specific cadence]
  - DTC E-commerce: [specific cadence]
  - Fintech/Crypto: [specific cadence]
- The "Value-First" vs. "Conversion-First" welcome philosophy: when to use each
- Progressive profiling techniques: what data to collect and when
- Welcome sequence conversion benchmarks with confidence intervals

### Onboarding & Activation Sequences
- Behavioral trigger mapping: which user actions should trigger which emails
- The "Aha Moment" email strategy: how to identify and accelerate time-to-value
- Segmentation by user intent signals: trial behavior patterns that predict conversion
- Re-engagement branches: when users stall, specific intervention emails
- Activation sequence benchmarks: open rates, click rates, activation lift by industry

### Nurture Sequences
- Content-to-commerce ratio frameworks (80/20, 70/30, etc.) by business model
- The "Invisible Funnel" concept: educational sequences that sell without selling
- Segmentation strategies: by persona, by behavior, by lifecycle stage, by engagement level
- Frequency optimization: how to find the fatigue threshold for your audience
- Nurture-to-SQL conversion benchmarks

### Retention & Loyalty Sequences
- Churn prediction triggers: behavioral signals that indicate risk
- Win-back timing: optimal delay after last engagement by business model
- Loyalty program email integration: point balance, tier status, exclusive access
- Expansion revenue emails: upsell/cross-sell timing and positioning
- NPS and feedback loop integration

### Transactional Emails
- The hidden revenue opportunity in transactional emails
- Order confirmation optimization: what to include beyond the receipt
- Shipping notification engagement tactics
- Account-related emails that drive re-engagement

## PART 3: TACTICAL EXECUTION

### Subject Line Frameworks
- The 7 proven subject line formulas with examples and when to use each
- Personalization tactics ranked by lift: name, company, behavior, location
- Emoji usage guidelines: when they help vs. hurt by audience segment
- A/B testing methodology: sample size requirements, statistical significance thresholds
- Subject line benchmarks by email type and industry

### Email Copywriting Principles
- The inverted pyramid for email: critical information hierarchy
- Scannable formatting rules: line length, paragraph breaks, visual anchors
- CTA optimization: button vs. text link, placement, copy formulas
- Personalization beyond [FIRST_NAME]: dynamic content blocks, conditional logic
- Mobile-first design constraints: touch targets, preview text, image handling

### Segmentation & Personalization
- The segmentation hierarchy: demographic → firmographic → behavioral → predictive
- RFM analysis for email: implementation and segment definitions
- Engagement scoring models: how to build and maintain
- Dynamic content decision trees: when complexity pays off vs. diminishes returns
- The "Segment of One" myth: practical limits of hyper-personalization

## PART 4: MEASUREMENT & OPTIMIZATION

### Metrics Framework
- Primary metrics by email type: what to optimize for in each sequence
- The "Email Dashboard" template: what metrics to review daily, weekly, monthly
- Cohort analysis for email: how to measure lifecycle program effectiveness over time
- Revenue attribution models: first-touch, last-touch, multi-touch, incremental lift testing
- Industry benchmarks with confidence intervals:
  - B2B SaaS: [specific metrics]
  - DTC E-commerce: [specific metrics]
  - Fintech: [specific metrics]

### Testing & Optimization
- What to test first: the prioritization framework for email optimization
- Minimum sample sizes by metric type
- Multivariate testing: when it's worth the complexity
- Send time optimization: methodology and expected lift
- The testing velocity imperative: how many tests per month by program maturity

## PART 5: BUSINESS MODEL VARIATIONS

### B2B SaaS Specifics
- Lead scoring integration with email
- Account-based email strategies
- Multi-threading: reaching multiple stakeholders
- Trial-to-paid conversion sequences
- Enterprise vs. SMB email strategy differences

### DTC E-commerce Specifics
- Browse abandonment vs. cart abandonment: different strategies
- Post-purchase sequences that drive LTV
- Seasonal campaign planning and calendar
- Inventory-based triggers (back in stock, low stock)
- Review solicitation timing and tactics

### Crypto/Fintech Specifics
- Compliance considerations: what you can and can't say
- Security-focused transactional emails
- Market condition-triggered campaigns
- Regulatory email requirements by jurisdiction

## PART 6: ANTI-PATTERNS & FAILURE MODES

- The 10 most common email program mistakes and how to avoid them
- When email is the WRONG channel: scenarios where other channels outperform
- Over-automation pitfalls: when sequences become spam
- The "blast culture" trap: why batch-and-blast destroys deliverability
- Measurement theater: vanity metrics that mislead

## OUTPUT FORMAT

Structure this as an AI-agent-friendly framework document with:
- "Use when:" trigger at the top
- Quick Reference section with key principles
- Detailed sections with specific, actionable guidance
- Decision trees for common scenarios
- Templates and formulas that can be directly applied
- Checklists for implementation and QA
- Benchmark tables with ranges, not just averages
```

---

## 2. Paid Acquisition Framework

```
You are an expert performance marketer who has managed $100M+ in paid media spend across Google, Meta, LinkedIn, TikTok, Twitter/X, and programmatic. You've scaled startups from $0 to $10M ARR on paid channels and have deep expertise in creative strategy, audience architecture, measurement, and budget optimization.

Create a comprehensive Paid Acquisition Framework covering:

## PART 1: STRATEGIC FOUNDATIONS

### Paid Media Philosophy
- The "Paid as Accelerant" mental model: when paid works and when it doesn't
- CAC payback period frameworks by business model and funding stage
- The efficiency vs. scale tradeoff: diminishing returns curves and breakpoints
- Channel selection decision tree: which platforms for which objectives
- The "Full Funnel" fallacy: when to run awareness vs. direct response

### Unit Economics for Paid
- CAC calculation methodologies: blended vs. channel-specific vs. incremental
- LTV:CAC ratios by business model with healthy ranges:
  - B2B SaaS: [specific ratios and payback periods]
  - DTC E-commerce: [specific ratios]
  - Fintech/Crypto: [specific ratios]
- Contribution margin requirements for profitable paid acquisition
- The "Efficiency Frontier": mapping spend to CAC across channels
- Budget allocation frameworks: portfolio theory applied to paid media

## PART 2: PLATFORM-SPECIFIC PLAYBOOKS

### Google Ads
- Campaign architecture: account structure best practices
- Search campaign strategy: keyword hierarchy, match type evolution, SKAG vs. STAG debate
- Performance Max: when to use, how to structure, what to expect
- Display and YouTube: prospecting vs. retargeting, audience strategies
- Bidding strategy selection: manual vs. automated, tCPA vs. tROAS vs. maximize conversions
- Quality Score optimization: the factors that actually matter
- Google Ads benchmarks by industry and objective

### Meta (Facebook/Instagram)
- Campaign structure in the "Advantage+" era
- Audience strategy evolution: broad vs. lookalikes vs. interest stacking
- The "Creative is the new targeting" reality: implications for strategy
- Creative testing frameworks: how many variants, how to structure tests
- Advantage+ Shopping Campaigns: when to use, how to set up
- iOS 14.5+ attribution reality: what you can and can't measure
- Meta benchmarks by vertical and objective

### LinkedIn
- When LinkedIn makes sense: the $50+ CAC reality check
- Campaign types and when to use each
- Audience building: job title vs. skills vs. company lists vs. matched audiences
- Lead Gen Forms vs. website conversions: the quality tradeoff
- ABM on LinkedIn: account list targeting strategies
- LinkedIn benchmarks for B2B

### TikTok Ads
- The "Don't Make Ads, Make TikToks" reality
- Spark Ads vs. standard ads: performance differences
- Creative production for TikTok: the 3-second hook imperative
- Audience strategy on a discovery platform
- TikTok Shop integration for e-commerce
- Measurement challenges and workarounds
- TikTok benchmarks by objective

### Twitter/X
- When X advertising works: the consideration set use case
- Campaign objectives and bidding strategies
- Audience targeting options and effectiveness
- Creative formats and best practices
- Current state of measurement and optimization

### Programmatic & Display
- When programmatic makes sense: brand awareness scale
- DSP selection criteria
- Audience strategy: 1P data, 3P data, contextual
- Viewability and fraud considerations
- Connected TV (CTV) opportunities and measurement

## PART 3: CREATIVE STRATEGY

### Creative Frameworks
- The "Creative Diversification" imperative: why one winner isn't enough
- Hook taxonomy: the 7 types of hooks that stop the scroll
- Creative testing velocity: how many new creatives per week by spend level
- The "Creative Fatigue" curve: detection and refresh timing
- UGC vs. produced content: when to use each, how to source

### Ad Copy Principles
- Direct response copywriting for paid: different from organic
- Headlines, primary text, descriptions: character limits and best practices
- Call-to-action optimization: what works, what doesn't
- Social proof integration in ad copy
- Regulatory considerations for claims (especially fintech/health)

### Landing Page Integration
- Message match: creative-to-landing-page consistency
- Landing page vs. homepage: when to build dedicated LPs
- Page speed impact on conversion and ad performance
- Mobile optimization requirements
- A/B testing landing pages in conjunction with ads

## PART 4: AUDIENCE ARCHITECTURE

### First-Party Data Strategy
- Customer list building and segmentation for paid
- Lookalike/Similar audiences: seed list best practices
- Website visitor audiences: pixel setup and segmentation
- CRM integration for suppression and targeting
- The "Data Clean Room" future: preparing for cookieless

### Retargeting Strategy
- Retargeting funnel architecture: visitor → engaged → cart → purchaser
- Frequency capping: optimal impressions by funnel stage
- Sequential retargeting: telling a story across impressions
- Exclusion strategy: who NOT to retarget
- Retargeting benchmarks vs. prospecting

### Prospecting Strategy
- Cold audience testing methodology
- Interest and behavior targeting: what still works post-ATT
- Broad targeting: when algorithms outperform manual targeting
- Geographic and demographic constraints
- B2B targeting: reaching decision-makers

## PART 5: MEASUREMENT & ATTRIBUTION

### Attribution Reality
- The post-iOS 14.5 measurement landscape
- Platform-reported vs. actual: the gap and why it exists
- Attribution models: last-click, first-click, data-driven, MMM
- Conversion API (CAPI) implementation: requirements and benefits
- Server-side tracking: what it solves, what it doesn't

### Incrementality Measurement
- Geo-lift testing methodology
- Holdout testing for retargeting
- Conversion lift studies: platform-native options
- Marketing Mix Modeling (MMM): when it makes sense
- The "Always Be Testing" incrementality culture

### Reporting & Optimization
- Daily, weekly, monthly reporting cadences
- The metrics that actually matter by funnel stage
- Optimization levers ranked by impact
- Pacing and budget management
- Automated rules vs. manual optimization

## PART 6: BUDGET & SCALING

### Budget Planning
- Annual planning: top-down vs. bottom-up approaches
- Seasonality planning: how to forecast demand spikes
- Channel allocation: the portfolio approach
- Testing budget: how much to reserve for experiments
- Contingency and opportunity budgets

### Scaling Methodology
- The scaling playbook: from $10K to $100K to $1M monthly spend
- When to scale and when to hold: decision criteria
- Diminishing returns: how to identify the efficiency ceiling
- Geographic expansion: testing new markets
- New channel introduction: the experimentation framework

## PART 7: BUSINESS MODEL VARIATIONS

### B2B SaaS
- Long consideration cycles: nurture integration with paid
- Demo/trial optimization strategies
- ABM paid strategies: account-level targeting
- Content syndication and lead gen
- Webinar and event promotion

### DTC E-commerce
- ROAS vs. CAC: which metric to optimize
- Catalog/dynamic product ads
- Promotional calendar integration
- New customer vs. returning customer strategies
- Subscription acquisition tactics

### Crypto/Fintech
- Platform restrictions and workarounds
- Compliance requirements for financial advertising
- Crypto-specific audiences and targeting
- Trust-building in regulated industries
- Geographic restrictions and considerations

## PART 8: ANTI-PATTERNS & FAILURE MODES

- The 10 most expensive paid media mistakes
- When to STOP spending on paid: the kill criteria
- Platform dependency risks and diversification
- Creative burnout and the testing treadmill
- Attribution theater: fooling yourself with bad data
- The "Agency Industrial Complex": when agencies optimize for wrong metrics

## OUTPUT FORMAT

Structure this as an AI-agent-friendly framework document with:
- "Use when:" trigger at the top
- Quick Reference section with key principles
- Platform-specific sections with current best practices
- Decision trees for channel selection and budget allocation
- Templates for campaign structures and naming conventions
- Checklists for campaign launch and optimization
- Benchmark tables with ranges by vertical
```

---

## 3. Analytics & Measurement Framework

```
You are a marketing analytics leader who has built measurement programs at high-growth startups and Fortune 500 companies. You've implemented attribution systems, designed experimentation programs, and built executive dashboards that drive decisions. You have deep expertise in GA4, Amplitude, Mixpanel, Looker, and MMM tools.

Create a comprehensive Analytics & Measurement Framework covering:

## PART 1: STRATEGIC FOUNDATIONS

### The Measurement Philosophy
- "What gets measured gets managed" — and what gets mis-measured gets mis-managed
- The hierarchy of measurement maturity: tracking → reporting → analysis → optimization → prediction
- Leading vs. lagging indicators: the temporal dimension of metrics
- The "North Star Metric" concept: when it works, when it's a trap
- Proxy metrics: useful shortcuts and their dangers

### Metrics Taxonomy
- The AARRR framework revisited: modern interpretations
  - Acquisition: traffic, leads, signups
  - Activation: first value moment, onboarding completion
  - Retention: DAU/MAU, cohort curves, churn
  - Revenue: ARPU, LTV, expansion, contraction
  - Referral: NPS, viral coefficient, word-of-mouth attribution
- Input metrics vs. output metrics: what you control vs. what you measure
- Health metrics vs. growth metrics: sustainability indicators
- Vanity metrics: what to stop measuring

### Metrics by Business Model
- B2B SaaS metrics with healthy ranges:
  - MRR/ARR growth rate by stage
  - Net Revenue Retention benchmarks
  - CAC payback periods
  - Magic Number and SaaS Quick Ratio
  - Sales efficiency metrics
- DTC E-commerce metrics with healthy ranges:
  - AOV, purchase frequency, LTV
  - Contribution margin targets
  - Repeat purchase rates
  - Inventory and fulfillment metrics
- Fintech/Crypto metrics:
  - TVL and protocol-specific metrics
  - Wallet-based cohort analysis
  - On-chain attribution methods

## PART 2: ATTRIBUTION MODELING

### Attribution Fundamentals
- The attribution problem: why perfect attribution is impossible
- Attribution windows: standard practices and when to deviate
- View-through vs. click-through: the eternal debate
- Cross-device attribution: methods and limitations
- Offline conversion tracking: bridging online-offline gaps

### Attribution Models Deep Dive
- Last-click: when it's appropriate, limitations
- First-click: use cases for demand gen
- Linear: the "fairness" model and its problems
- Time-decay: matching to sales cycles
- Position-based (U-shaped, W-shaped): custom weightings
- Data-driven attribution: how it works, when to trust it
- Incrementality-based attribution: the gold standard

### Post-Cookie Attribution
- The deprecation timeline and implications
- First-party data strategies for attribution
- Server-side tracking implementation
- Conversion APIs: Meta, Google, TikTok
- Probabilistic matching: methods and accuracy
- Data clean rooms: what they solve, limitations
- Privacy-preserving measurement: differential privacy, aggregated reporting

### Marketing Mix Modeling (MMM)
- When MMM makes sense: budget thresholds, channel diversity
- MMM methodology: regression basics for marketers
- Time series considerations: seasonality, trend, lag effects
- Adstock and saturation curves: modeling media response
- MMM tools: Robyn, Meridian, proprietary solutions
- MMM + MTA: unified measurement approaches

## PART 3: EXPERIMENTATION FRAMEWORK

### Experimentation Culture
- The "Test Everything" philosophy: where it helps, where it hurts
- Experimentation velocity: how many tests per month by team size
- The experimentation backlog: prioritization frameworks (ICE, PIE, RICE)
- Documentation and learning repositories
- Failure culture: celebrating learning, not just wins

### A/B Testing Methodology
- Sample size calculation: the math marketers need to know
- Statistical significance: p-values, confidence intervals explained simply
- Power analysis: detecting the effect you care about
- Test duration: minimum runtime considerations
- Segmentation in testing: when to slice results
- Multiple comparison problems: Bonferroni and alternatives

### Testing Infrastructure
- Feature flagging for marketing experiments
- Holdout groups: implementation and maintenance
- Randomization methods: user-level, session-level, cookie-level
- Testing tools: Optimizely, VWO, LaunchDarkly, in-house
- QA processes for experiments

### Advanced Testing
- Multi-armed bandits: when to use instead of A/B
- Geo-lift testing: methodology and implementation
- Incrementality testing: holdout design, synthetic control
- Sequential testing: early stopping without p-hacking
- Bayesian vs. Frequentist: practical implications

## PART 4: TOOL STACK & IMPLEMENTATION

### Analytics Tool Selection
- GA4 deep dive: what it does well, limitations, setup best practices
- Product analytics (Amplitude, Mixpanel, Heap): when you need them
- Customer data platforms (Segment, Rudderstack): architecture decisions
- Business intelligence (Looker, Tableau, Metabase): visualization layer
- Reverse ETL and warehouse-native analytics
- The "modern data stack" for marketing

### Tracking Implementation
- Event taxonomy design: naming conventions, properties, standards
- Tracking plan templates and documentation
- Tag management (GTM): architecture and governance
- Data validation: ensuring tracking accuracy
- Privacy compliance: consent management, data retention

### Data Warehouse for Marketing
- Why marketing needs warehouse access
- Common data models for marketing analytics
- Connecting marketing data to revenue data
- Identity resolution across systems
- Data freshness requirements by use case

## PART 5: REPORTING & DASHBOARDS

### Reporting Hierarchy
- Executive dashboards: what leadership needs to see
- Channel dashboards: platform-specific deep dives
- Campaign dashboards: tactical optimization views
- Experimental dashboards: test monitoring and results

### Dashboard Design Principles
- The "So What?" test: every metric needs context
- Comparisons that matter: period-over-period, target vs. actual, segment vs. total
- Visualization best practices for marketing data
- Alert thresholds: when to notify vs. when to report
- Self-serve vs. analyst-delivered insights

### Reporting Cadences
- Daily reporting: what to check, automated alerts
- Weekly reporting: team-level reviews, optimization actions
- Monthly reporting: executive summaries, strategic insights
- Quarterly reporting: planning inputs, trend analysis
- Annual reporting: budgeting, strategy development

## PART 6: ADVANCED ANALYTICS

### Cohort Analysis
- Cohort definition strategies: acquisition date, first behavior, etc.
- Retention curves: construction and interpretation
- LTV modeling with cohorts
- Behavioral cohorts: engagement-based segmentation

### Predictive Analytics
- Churn prediction: models and features
- LTV prediction: methods and accuracy expectations
- Propensity modeling: likely to convert, likely to upsell
- Lead scoring: building and maintaining models
- When ML is overkill: simple heuristics that work

### Customer Segmentation
- RFM analysis: implementation and segment definitions
- Behavioral clustering: methods and interpretation
- Value-based segmentation: high-value customer identification
- Segment-specific strategies and measurement

## PART 7: BUSINESS MODEL VARIATIONS

### B2B SaaS Analytics
- Lead-to-revenue attribution
- Multi-touch B2B attribution
- Account-level analytics
- Sales + marketing alignment metrics
- Expansion and churn analytics

### DTC E-commerce Analytics
- Purchase funnel analytics
- Product analytics: what's selling, what's not
- Promotional effectiveness measurement
- Inventory and demand forecasting
- Customer acquisition vs. retention spend allocation

### Crypto/Fintech Analytics
- On-chain analytics: tools and methodologies
- Wallet-based user identification
- TVL attribution
- Protocol-specific metrics
- Compliance and audit requirements

## PART 8: ANTI-PATTERNS & FAILURE MODES

- The 10 most common analytics mistakes
- Correlation vs. causation: marketing examples
- Survivorship bias in marketing analytics
- Simpson's paradox: when aggregation misleads
- Goodhart's Law: when metrics become targets
- Analysis paralysis: when to stop analyzing and act
- The "Data Lake" that became a "Data Swamp"
- Premature optimization: measuring too early

## OUTPUT FORMAT

Structure this as an AI-agent-friendly framework document with:
- "Use when:" trigger at the top
- Quick Reference section with key principles and metric definitions
- Implementation guides for common tools
- Decision frameworks for tool selection and methodology
- Templates for tracking plans, dashboards, and reports
- Checklists for analytics audits and setup
- Benchmark tables for key metrics by business model
```

---

## 4. Social Media Strategy Framework

```
You are a social media strategist who has built audiences from zero to millions across Twitter/X, LinkedIn, Instagram, TikTok, Discord, Telegram, and Reddit. You've managed social for VC-backed startups, Fortune 500 brands, and crypto protocols. You understand both organic growth and community building at depth.

Create a comprehensive Social Media Strategy Framework covering:

## PART 1: STRATEGIC FOUNDATIONS

### Social Media Philosophy
- The "Distribution Arbitrage" mindset: platforms want content, you want reach
- Owned vs. rented audiences: the email backup imperative
- Platform half-lives: how long content lives on each platform
- The "1-9-90" rule and participation inequality
- Social as distribution vs. social as community: different strategies

### Platform Selection Framework
- Decision criteria: where is your audience, what can you produce, what's the ROI
- Platform-audience fit matrix by business model:
  - B2B SaaS: [platform priorities]
  - DTC E-commerce: [platform priorities]
  - Fintech/Crypto: [platform priorities]
  - Creator/Media: [platform priorities]
- Resource requirements by platform: what each demands
- Platform risk: algorithm changes, policy shifts, platform decline
- The "One Platform" strategy: when to focus vs. diversify

### Content Strategy Foundations
- Content pillars: the 3-5 themes that define your presence
- Content-market fit: how to find what resonates
- The content flywheel: creation → distribution → engagement → data → creation
- Evergreen vs. timely content: the right mix
- Original vs. curated vs. UGC: content sourcing strategies

## PART 2: PLATFORM PLAYBOOKS

### Twitter/X
- Account architecture: personal brand vs. company brand vs. both
- The follower growth formula: consistency × quality × engagement
- Tweet anatomy: hooks, body, CTAs, threads vs. singles
- Engagement strategy: ratio of original vs. replies vs. retweets
- Crypto Twitter (CT) specifics: culture, norms, influencer dynamics
- Twitter/X algorithm: what drives reach in 2024-2025
- Metrics and benchmarks: impressions, engagement rate, follower growth

### LinkedIn
- Profile optimization: the 7 elements that matter
- Content formats ranked by reach: documents > polls > text > links > video
- The LinkedIn algorithm: dwell time, early engagement, network effects
- B2B thought leadership: what works, what's cringe
- Company pages vs. personal pages: strategy differences
- LinkedIn engagement pods: do they work, should you use them
- Metrics and benchmarks for B2B

### Instagram
- Feed vs. Stories vs. Reels: where to invest effort
- Reels strategy: the TikTok-to-Instagram pipeline
- Visual identity: consistency without monotony
- Hashtag strategy: current best practices (it's changed)
- Instagram shopping integration
- Engagement tactics: DMs, comments, Stories interactions
- Metrics and benchmarks

### TikTok (Organic)
- Content strategy for discovery: trends vs. original formats
- The hook imperative: first 3 seconds or death
- Sound strategy: trending audio, original audio, voiceover
- Posting frequency and timing
- Engagement and comment strategy
- TikTok-to-other-platform funneling
- Metrics and benchmarks

### YouTube
- Long-form vs. Shorts strategy
- Searchability: YouTube as a search engine
- Thumbnail and title optimization
- Audience retention: the metric that matters most
- Community tab and engagement
- YouTube's algorithm: watch time, CTR, retention
- Metrics and benchmarks

### Discord
- Server architecture: channels, roles, permissions
- Community warmth: onboarding new members
- Moderation at scale: bots, human mods, culture
- Engagement tactics: events, AMAs, giveaways
- Discord for crypto: specific patterns and expectations
- When Discord makes sense vs. other platforms
- Health metrics for Discord communities

### Telegram
- Channel vs. group strategies
- Crypto/fintech Telegram culture
- Bot integrations and automation
- Moderation challenges
- Engagement patterns
- Metrics for Telegram

### Reddit
- Subreddit selection and participation strategy
- The "1-9-90" rule extreme: mostly lurkers
- Content that works on Reddit: value-dense, not promotional
- AMA strategy
- Reddit for B2B: surprisingly effective niches
- Getting banned: what to avoid
- Metrics and expectations

## PART 3: CONTENT PRODUCTION

### Content Formats by Platform
- Platform-native formats: what each platform rewards
- Repurposing strategy: one piece of content, 10 distribution points
- Production quality expectations: lo-fi vs. hi-fi by platform
- Batching and scheduling: efficient production workflows

### Content Cadence Frameworks
- Platform-specific posting frequencies:
  - Twitter: [frequency]
  - LinkedIn: [frequency]
  - Instagram: [frequency]
  - TikTok: [frequency]
  - YouTube: [frequency]
- Quality vs. quantity: the tradeoff by platform
- Minimum viable presence: what's the floor

### Content Calendar Management
- Planning horizons: how far ahead by content type
- Reactive vs. planned content mix
- Seasonal and event integration
- Tool recommendations: scheduling, collaboration, analytics

## PART 4: COMMUNITY BUILDING

### Community Strategy
- Community vs. audience: the difference and when each matters
- The community flywheel: value → attraction → contribution → value
- Community governance: rules, moderation, member roles
- Community platforms: Discord vs. Slack vs. Circle vs. native

### Engagement Tactics
- Response strategy: who, when, how to reply
- User-generated content: solicitation and amplification
- Ambassador and champion programs
- Community rituals: recurring events that build habit
- Conflict resolution: handling negative members

### Influencer & KOL Partnerships
- Influencer identification: beyond follower count
- Partnership structures: paid, affiliate, equity, product
- Brief creation: what influencers need to succeed
- Measurement: how to attribute influencer impact
- Crypto KOL specifics: disclosure, FTC, and the grey areas
- Long-term relationships vs. one-off campaigns

## PART 5: GROWTH TACTICS

### Organic Growth Levers
- The engagement loop: engage first, post second
- Collaboration and cross-promotion
- Trend jacking: how to do it without being cringe
- SEO for social: optimizing for in-platform search
- The "Reply Guy" strategy: systematic engagement for growth
- Giveaways and contests: what works, what backfires

### Viral Mechanics
- What makes content shareable: the STEPPS framework (Social currency, Triggers, Emotion, Public, Practical value, Stories)
- Network effects in content: why some content spreads
- Seeding strategy: initial distribution for maximum reach
- Viral hooks: patterns that consistently perform

### Paid Amplification of Organic
- When to boost organic content
- Spark Ads, boosted posts, thought leader ads
- Retargeting social engagers
- Influencer whitelisting

## PART 6: CRISIS & REPUTATION

### Crisis Management
- The crisis response timeline: first 60 minutes, first 24 hours
- Response frameworks: acknowledge, action, update
- When to respond vs. when to ignore
- Platform-specific crisis dynamics
- Legal and PR coordination

### Reputation Monitoring
- Social listening tools and setup
- Mention tracking and alerts
- Sentiment analysis: manual vs. automated
- Competitive monitoring
- Review management integration

## PART 7: MEASUREMENT

### Metrics by Platform
- Platform-native metrics: what each dashboard shows
- Cross-platform metrics: standardizing measurement
- Engagement rate calculations: the different formulas
- Reach vs. impressions: what each means
- Follower quality: how to assess beyond quantity

### Attribution Challenges
- Social's role in the funnel: often early, rarely last-click
- Brand lift measurement
- Social as assisted conversion
- UTM strategy for social links
- Dark social: measurement gaps

### Reporting Frameworks
- Weekly social reports: what to include
- Monthly performance reviews
- Competitive benchmarking
- ROI calculation attempts: the honest limitations

## PART 8: BUSINESS MODEL VARIATIONS

### B2B SaaS Social
- LinkedIn-first strategy
- Twitter for developer audiences
- Thought leadership positioning
- Lead generation from social
- ABM social tactics

### DTC E-commerce Social
- Instagram and TikTok shopping
- UGC at scale
- Influencer seeding
- Social proof generation
- Customer service on social

### Crypto/Web3 Social
- Twitter/X as the center of crypto
- Discord community management at scale
- Telegram for announcements
- The "airdrop culture" and engagement farming
- Regulatory considerations in social content

## PART 9: ANTI-PATTERNS & FAILURE MODES

- The 10 most common social media mistakes
- Automation that backfires
- Engagement bait that destroys trust
- The "LinkedIn Cringe" taxonomy
- Platform dependency: the danger of rented audiences
- Vanity metric addiction
- Inauthenticity: how audiences detect it
- The "Silence is Golden" scenarios: when not to post

## OUTPUT FORMAT

Structure this as an AI-agent-friendly framework document with:
- "Use when:" trigger at the top
- Quick Reference section with key principles
- Platform-specific sections with current algorithms and best practices
- Content templates and formats for each platform
- Community building playbooks
- Crisis response protocols
- Checklists for account setup and content creation
- Benchmark tables by platform and business model
```

---

## 5. General Marketing Advice by Business Model

```
You are a marketing leader who has served as CMO or VP Marketing at multiple companies across B2B SaaS, DTC e-commerce, fintech, marketplaces, and crypto protocols. You've seen what works and what fails across different business models and stages.

Create a comprehensive Business Model Marketing Playbook covering:

## PART 1: B2B SAAS MARKETING

### Strategic Foundations
- The B2B SaaS marketing funnel: awareness → demand → pipeline → revenue
- Marketing's relationship with sales: MQL, SQL, SAL definitions and SLAs
- Self-serve vs. sales-assisted vs. enterprise: different marketing motions
- Product-led growth (PLG) marketing: how it changes everything
- Category creation vs. category competition: strategic choice implications

### Channel Priorities by Stage
- Seed/Pre-Seed: founder-led sales, content, community
- Series A: paid demand gen, content marketing, events
- Series B+: brand, ABM, multi-channel orchestration
- Channel CAC benchmarks by stage

### Content Marketing for B2B SaaS
- The content-to-pipeline journey
- SEO for B2B: different from B2C, how and why
- Gated vs. ungated: the modern debate
- Webinars, podcasts, events: high-touch content
- Customer case studies: the most valuable asset

### Demand Generation
- Demand gen vs. lead gen: the critical distinction
- Paid channels that work for B2B: LinkedIn, Google, programmatic
- ABM: account-based marketing, when and how
- Intent data: what it is, how to use it
- Outbound's role: marketing-assisted outbound

### Metrics & Benchmarks
- B2B SaaS marketing benchmarks:
  - Website visitor to lead: [range]%
  - Lead to MQL: [range]%
  - MQL to SQL: [range]%
  - SQL to opportunity: [range]%
  - Opportunity to close: [range]%
  - CAC by channel
  - Payback periods by motion

## PART 2: DTC E-COMMERCE MARKETING

### Strategic Foundations
- The DTC model: brand + margin + data
- Customer acquisition vs. retention: the LTV equation
- The "DTC Reckoning": rising CACs and path forward
- Omnichannel: when to expand beyond DTC
- Brand vs. performance: the false dichotomy

### Channel Priorities
- Meta and Google: the foundational channels
- TikTok: the new customer acquisition engine
- Influencer marketing: scaling word-of-mouth
- Email and SMS: the owned channel imperative
- Affiliate: when it works, when it's fraud
- Retail and wholesale: diversification strategy

### Creative Strategy
- The creative volume imperative: testing velocity
- UGC at scale: sourcing, licensing, production
- Brand campaigns vs. DR campaigns: different creative
- Seasonality and promotional creative
- Video vs. static: platform-specific guidance

### Retention Marketing
- The retention math: why it matters more than ever
- Email and SMS strategy for e-commerce
- Loyalty programs: what works, what's table stakes
- Subscription models: the holy grail
- Win-back campaigns

### Metrics & Benchmarks
- DTC e-commerce benchmarks:
  - Blended CAC: $[range]
  - First-order AOV: $[range]
  - 60-day LTV: $[range]
  - Repeat purchase rate: [range]%
  - Email revenue %: [range]%
  - ROAS by channel

## PART 3: FINTECH MARKETING

### Strategic Foundations
- Trust as the foundational asset
- Regulatory constraints on marketing: what you can and can't say
- The compliance review process: building it in
- Education-first marketing: complex products require explanation
- Competitive positioning in regulated markets

### Channel Strategies
- Content marketing: education and thought leadership
- Paid acquisition: platform restrictions and workarounds
- Referral programs: particularly powerful in fintech
- Partnership marketing: embedded finance, co-marketing
- PR and earned media: credibility building

### Specific Verticals
- Consumer fintech (neobanks, payments)
- B2B fintech (infrastructure, embedded)
- Lending and credit
- Insurance
- Wealth and investing

### Compliance Considerations
- Fair lending and ECOA implications
- UDAP/UDAAP in marketing
- State-specific requirements
- Disclosures and fine print
- Social media compliance

### Metrics & Benchmarks
- Fintech marketing benchmarks:
  - CAC by product type
  - Funding/account opening rates
  - Activation metrics
  - Referral rates

## PART 4: CRYPTO/WEB3 MARKETING

### Strategic Foundations
- Decentralization and marketing: the philosophical tension
- Community-first: marketing in crypto is community building
- Token incentives: the unique lever, and its dangers
- The "crypto winter" marketing playbook: building when others retreat

### Channel Priorities
- Twitter/X: the center of crypto discourse
- Discord: community home base
- Telegram: announcements and international audiences
- Crypto media: Decrypt, CoinDesk, The Block, etc.
- Crypto podcasts and YouTube
- Airdrops and token-gated experiences

### Community Building
- Discord community architecture
- Governance and DAOs: community as stakeholder
- Ambassador programs with token incentives
- Developer relations: if building infrastructure
- IRL events: conferences, meetups, hackathons

### Crypto-Specific Tactics
- Airdrop strategy and mechanics
- Retroactive rewards: incentivizing early users
- Points programs: the new meta
- KOL partnerships: the unique crypto dynamics
- Listing and launch marketing

### Regulatory Reality
- What you can and can't say about tokens
- Geographic restrictions
- Disclosure requirements
- The evolving regulatory landscape

### Metrics & Benchmarks
- Crypto marketing metrics:
  - Community size (Discord, Telegram, Twitter)
  - TVL as a marketing outcome
  - Wallet growth
  - Transaction volume
  - Holder distribution

## PART 5: MARKETPLACE MARKETING

### Strategic Foundations
- The chicken-and-egg problem: supply vs. demand
- Liquidity as the goal: what it means, how to measure
- Winner-take-most dynamics: the race to scale
- Geographic expansion: market-by-market playbooks

### Supply-Side Marketing
- Supplier acquisition channels
- Supplier value proposition
- Supplier success and retention
- Supplier community building

### Demand-Side Marketing
- Consumer acquisition: often more traditional
- Trust and safety messaging
- Category expansion
- Repeat purchase / booking

### Marketplace-Specific Tactics
- Managed marketplaces vs. open platforms
- Take rate and pricing as marketing tools
- Cross-side network effects marketing
- Geographic launch playbooks

## PART 6: CROSS-CUTTING THEMES

### Stage-Appropriate Marketing
- Pre-product-market fit: marketing's role
- Post-PMF, pre-scale: finding the channels
- Scaling phase: efficiency and diversification
- Mature phase: brand and efficiency

### Team Building
- First marketing hire: generalist vs. specialist
- Building the team: order of roles
- Agency vs. in-house: decision framework
- Marketing ops and systems

### Budget Allocation
- Marketing budget as % of revenue by model
- Channel allocation frameworks
- Testing budget reserves
- Brand vs. performance splits

## OUTPUT FORMAT

Structure this as an AI-agent-friendly framework document with:
- "Use when:" trigger at the top indicating which business model
- Quick Reference section for each business model
- Detailed playbooks by business model and stage
- Channel prioritization frameworks
- Metric benchmarks with ranges and confidence levels
- Common mistakes and anti-patterns by business model
- Checklists for marketing strategy development
```

---

## 6. 2026 Marketing Playbook

```
You are a forward-thinking marketing strategist who advises high-growth companies and investment firms on marketing trends. You have deep expertise in AI/ML applications to marketing, privacy technology evolution, platform economics, and consumer behavior shifts. You correctly predicted the rise of TikTok, the iOS 14.5 attribution crisis, and the AI content explosion.

Create a comprehensive 2026 Marketing Playbook covering what will be different, what will matter, and how to prepare NOW.

## PART 1: THE MACRO SHIFTS

### AI Transformation of Marketing
- Generative AI content saturation: when everyone has AI, what's the moat?
- AI agents as customers: marketing to LLMs that research on behalf of humans
- The "AI-discoverable" content imperative: structured data, clear answers, citation-worthy
- AI-native creative production: from ideation to execution to optimization
- Synthetic media: AI influencers, personalized video at scale, authenticity signals
- Search transformation: Google AI Overviews, Perplexity, ChatGPT search, and the zero-click future
- The human premium: when AI is everywhere, authentic human touch becomes differentiator

### Privacy & Data Evolution
- Post-cookie reality: what's working, what's failed, what's next
- First-party data as competitive moat: strategies for collection and activation
- Privacy-preserving measurement: differential privacy, aggregated APIs, clean rooms at scale
- Consent fatigue: user experience implications and conversion impact
- Geographic fragmentation: EU, US states, global compliance complexity
- Identity resolution: unified IDs, probabilistic matching, contextual resurgence

### Platform Power Shifts
- Platform consolidation vs. fragmentation: where audiences are migrating
- Social commerce maturation: TikTok Shop, Instagram Checkout, YouTube Shopping
- The "everything app" attempts: X, Meta, others bundling services
- Vertical social networks: niche communities gaining share from mass platforms
- Decentralized social: Farcaster, Lens, Bluesky — if/when they matter for marketing
- Platform algorithm evolution: engagement to "time well spent" to ???

### Economic & Consumer Context
- Marketing budgets in uncertain economy: efficiency imperative
- Consumer attention scarcity: competing in the most cluttered environment ever
- Value-conscious consumers: messaging and positioning shifts
- Sustainability expectations: greenwashing backlash, authentic environmental messaging
- Gen Z and Gen Alpha: the audiences that will define 2026

## PART 2: CHANNEL-BY-CHANNEL 2026 OUTLOOK

### Search in 2026
- Google's AI transformation: what organic looks like with AI Overviews everywhere
- SEO evolution: from "10 blue links" to "AI-optimized content"
- Zero-click optimization: winning in featured snippets, AI answers, knowledge panels
- Alternative search: TikTok as search engine, Reddit resurgence, vertical search
- Voice and multimodal search: optimization requirements
- Paid search changes: auction dynamics with AI, Performance Max evolution
- **What to do NOW to prepare**

### Social Media in 2026
- TikTok: regulatory uncertainty, platform maturation, commerce integration
- Instagram: the Reels pivot completion, AR/VR integration, checkout optimization
- LinkedIn: creator economy growth, B2B attribution improvements, video shift
- X/Twitter: the Elon experiment results, what audience remains
- YouTube: Shorts monetization, AI-generated content policies, competition from TikTok
- Emerging platforms: what to watch, when to invest
- **What to do NOW to prepare**

### Email & Messaging in 2026
- Email deliverability: AI spam filters, authentication requirements, inbox competition
- SMS/RCS evolution: rich messaging capabilities, regulatory environment
- WhatsApp Business: expansion in US market
- In-app messaging and push: permission challenges, personalization requirements
- Conversational AI: chatbots that actually work, agent-based customer interaction
- **What to do NOW to prepare**

### Paid Media in 2026
- Creative automation: AI-generated ads at scale, platform-native tools
- Targeting evolution: broad + signals vs. detailed targeting, privacy-safe audiences
- Measurement: incrementality as standard, MMM accessibility, platform reporting trust
- Channel diversification: CTV growth, retail media networks, audio advertising
- Creative velocity requirements: how many variants, how fast
- **What to do NOW to prepare**

### Content in 2026
- AI content flood: differentiation when everyone can produce at scale
- Video-first everything: written content's declining role
- Interactive and immersive: AR, spatial computing, interactive experiences
- User-generated content: authentic voices matter more than ever
- Podcast evolution: saturation, discovery, monetization
- **What to do NOW to prepare**

## PART 3: EMERGING CHANNELS & TACTICS

### AI-Native Marketing
- Marketing to AI agents: how LLMs will research and recommend
- Structured data and knowledge graphs: making your brand AI-discoverable
- AI shopping assistants: optimization for automated purchase decisions
- Conversational commerce: marketing through AI interfaces
- Brand safety in AI-generated contexts

### Retail Media Networks
- Amazon Ads, Walmart Connect, Target Roundel, Instacart: the fragmented landscape
- First-party data gold: why retail media is exploding
- Attribution advantages: closed-loop measurement
- Strategy: when to invest, how to allocate, expected returns
- Emerging networks: grocery, convenience, specialty retail

### Connected TV (CTV)
- CTV growth trajectory: cord-cutting acceleration
- Targeting capabilities: household, behavioral, deterministic matching
- Measurement maturation: cross-device, incrementality, attention metrics
- Creative requirements: TV-quality expectations, personalization
- Platform selection: programmatic vs. direct, FAST channels

### Audio & Voice
- Podcast advertising evolution: dynamic insertion, attribution
- Streaming audio: Spotify, Amazon Music advertising
- Voice search optimization: Alexa, Google Home, Siri
- Audio branding: sonic identity requirements

### Spatial Computing & AR
- Apple Vision Pro and competitors: marketing opportunities
- AR advertising: try-before-buy, immersive brand experiences
- Spatial commerce: virtual stores, product visualization
- When this matters: timeline expectations, early mover considerations

## PART 4: BUSINESS MODEL SPECIFIC 2026 SHIFTS

### B2B SaaS in 2026
- AI-augmented buyer journey: prospects doing 90% of research before contact
- Product-led growth maturation: self-serve expectations everywhere
- Account-based everything: ABM beyond marketing to full GTM
- Event renaissance: in-person as differentiator post-COVID normalization
- Community as competitive moat
- **What to prioritize, what to deprioritize**

### DTC E-commerce in 2026
- Profitability imperative: the "growth at all costs" hangover
- Omnichannel requirement: DTC-only is over for scale
- Social commerce acceleration: native checkout expectations
- Subscription fatigue: membership models evolution
- Sustainability as table stakes
- **What to prioritize, what to deprioritize**

### Crypto/Web3 in 2026
- Post-regulatory clarity: marketing in a compliant world
- Institutional adoption: B2B crypto marketing evolution
- Consumer crypto: mainstream use cases beyond speculation
- Community-led growth: decentralized marketing
- Token-incentive sophistication: beyond simple airdrops
- **What to prioritize, what to deprioritize**

### Fintech in 2026
- Embedded finance marketing: B2B2C complexity
- Trust rebuilding: post-2023 instability messaging
- AI-powered personalization: hyper-relevant financial advice
- Open banking: data-driven marketing opportunities
- Regulatory marketing requirements evolution
- **What to prioritize, what to deprioritize**

## PART 5: SKILLS & TEAM EVOLUTION

### Marketing Skills That Matter in 2026
- AI fluency: prompt engineering, AI tool selection, output refinement
- Data literacy: not just analysts, everyone reads dashboards
- Creative direction: guiding AI, not just creating
- Systems thinking: martech stack orchestration
- Soft skills premium: as AI handles execution, strategy and communication rise

### Team Structure Evolution
- AI as team member: roles AI replaces, augments, creates
- Specialist vs. generalist pendulum: where it's swinging
- In-house vs. outsource: what's changing
- Cross-functional integration: marketing + product + sales blurring
- Remote/global teams: accessing talent globally

### Martech Stack 2026
- Consolidation vs. best-of-breed: platform economics forcing choices
- AI-native tools replacing legacy
- CDP as foundation: first-party data orchestration
- Composable martech: headless, API-first architecture
- Build vs. buy: when custom solutions make sense

## PART 6: METRICS & MEASUREMENT EVOLUTION

### What We'll Measure Differently
- Incrementality as default: holdout-tested performance
- Attention metrics: beyond impressions to actual engagement
- AI-influenced attribution: LLM research touchpoint credit
- Lifetime value sophistication: predictive, segment-specific
- Brand metrics integration: brand and performance unified

### The Death of Certain Metrics
- Last-click attribution: finally gone
- Vanity social metrics: reach and impressions without context
- MQLs (maybe): product-qualified evolution
- CPM as primary efficiency metric: attention-adjusted

### New Metrics to Track
- AI discoverability score: how well LLMs can find and represent your brand
- Synthetic media detection: authenticity signals
- Privacy compliance cost: total cost of data practices
- Owned audience value: reducing rented audience dependency

## PART 7: STRATEGIC RECOMMENDATIONS

### Universal Priorities for 2026
1. **First-party data strategy**: if you haven't built this, you're already behind
2. **AI content differentiation**: human expertise, original research, unique voice
3. **Measurement infrastructure**: incrementality capability, clean room access
4. **Creative velocity**: systems to produce 10x more variants
5. **Owned audiences**: email lists, communities, direct relationships

### What to START Now
- Building first-party data assets
- Experimenting with AI creative tools
- Structuring content for AI discoverability
- Testing retail media networks (if relevant)
- Investing in community

### What to STOP Now
- Over-reliance on third-party cookies/targeting
- Generic AI-generated content at scale
- Single-channel dependency
- Vanity metric optimization
- Annual planning cycles (move to quarterly+)

### What to CONTINUE
- Brand investment (it's not going away)
- Video content production
- Testing and experimentation culture
- Customer-centric messaging
- Multi-channel attribution improvement

## PART 8: SCENARIO PLANNING

### If AI Regulation Tightens
- Content labeling requirements
- AI creative restrictions
- Transparency requirements
- Contingency playbooks

### If Economic Downturn Deepens
- Efficiency-first marketing
- Budget preservation tactics
- Revenue marketing emphasis
- Brand vs. performance allocation shifts

### If a Major Platform Fails/Changes
- TikTok ban implications
- X continued deterioration
- Meta antitrust outcomes
- Diversification strategies

### If Privacy Regulation Expands
- State-by-state US complexity
- Global compliance frameworks
- First-party data acceleration
- Contextual targeting renaissance

## OUTPUT FORMAT

Structure this as an AI-agent-friendly framework document with:
- "Use when:" trigger at the top
- Executive summary with top 5-10 predictions
- Quick Reference checklist: "2026 Readiness Checklist"
- Detailed sections by channel and business model
- Timeline: what to do Q1 2025, Q2 2025, H2 2025, H1 2026
- Scenario planning frameworks
- Resource allocation recommendations
- Anti-patterns: what NOT to do based on outdated 2024 assumptions
```

---

## Usage Notes

1. **Run with extended thinking** - These prompts require deep synthesis
2. **Iterate on output** - Ask follow-up questions for areas needing more depth
3. **Validate benchmarks** - Numbers may need updating; treat as starting points
4. **Customize for context** - Adapt to your specific client or industry

After generating, save outputs to:
- `channels/email-lifecycle.md`
- `channels/paid-acquisition.md`
- `measurement/analytics-frameworks.md`
- `channels/social-media.md`
- `frameworks/business-model-playbooks.md`
- `frameworks/2026-playbook.md`
