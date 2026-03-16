# LLM Citation Tracking & Cross-Platform Mention Building

## Overview

This framework covers tracking brand visibility across AI platforms (ChatGPT, Perplexity, Gemini, AI Overviews) and building strategic citations to improve LLM rankings. Based on Koray Tugberk Gubur's methodology for monitoring and manipulating how LLMs cite sources.

## Key Insight

> "The credits, mentions, and the links are going together... If this company here is not mentioning us, what we should be doing basically is going to the owner by finding the mail, and we just actually sent them an article for free, and they publish it, or we just ask them what do you want for mentioning us in this area." - Koray

---

## Part 1: LLM Rank Tracking Tools

### WriteSonic AI Rank Tracker (Recommended)

WriteSonic is Koray's primary recommendation for LLM citation tracking.

**Capabilities:**
- Track citations across ChatGPT, Gemini, AI Overviews, and Perplexity
- Filter by specific platform
- Export citation pages (URLs where your brand is mentioned)
- See which brands are mentioned by which platform
- Track sentiment (positive/negative mentions)
- Compare market share week-over-week
- View domains mentioning you vs. competitors

**Key Quote:**
> "I believe WriteSonic will be perfectly fine for this purpose... Even the layout of competitors is stolen from WriteSonic. They are very famous SaaS, very leaning on this technology. They keep adding new stuff." - Koray

**Setup:**
1. Subscribe to WriteSonic's AI Rank Tracker
2. Add your brand and competitor brands
3. Configure prompts/queries to track (avoid question sentences for broader results)
4. Set location targeting if relevant
5. Export citation URLs for outreach

### Alternative: Profound

- Also tracks LLM citations
- Koray warns: "They got $35 million investment... it's a hype. In three, four years, these companies will be in a hard situation because these technologies are very easy to create."

### What the Tools Track

| Metric | Description |
|--------|-------------|
| **Citation Pages** | URLs that LLMs cite when answering queries |
| **Brand Mentions** | Which brands appear in LLM responses |
| **Market Share** | % of prompts where your brand is cited |
| **Sentiment** | Positive vs negative mention context |
| **Platform Split** | ChatGPT vs Gemini vs Perplexity citations |

---

## Part 2: Reddit/Quora Mention Strategy

### Why Forum Mentions Matter

> "Forum language rules also became important... Google started to announce the perspectives update. Then it is followed by a helpful content update. It is also followed directly with forums and discussions traffic search." - Koray

**Current Reddit Status (as of late 2025):**
- Reddit blocked most AI crawlers in robots.txt
- Reddit has legal lawsuit against Anthropic (Claude)
- ChatGPT citations from Reddit decreased from ~48% to lower
- Microsoft Bing still indexes some Reddit content
- Reddit launched "Reddit Answers" beta (internal ChatGPT)

**Koray's View:**
> "I wouldn't give up from Reddit currently. I believe other AI systems also will be finding some alternatives to the Reddit as well."

### Aged Account Strategy

**Critical Point: Account Age Matters**

> "Having an aged account makes a difference, right? Aged account, it should be. In fact, if you go to the Quality Rater Guidelines, it was there in one of the versions. They were mentioning Reddit here, and they are even checking your upvotes." - Koray

**What Services Do:**
> "What these people do is they just buy aged actual Reddit accounts and then basically they pay some people from Philippines or different places to just post some GPT-generated content on that."

**Koray's Recommendation: DIY Approach**
> "It's something that you can do better, actually, with just a few accounts in a very authentic way."

### Implementation Steps

1. **Find Relevant Threads**
   ```
   site:reddit.com "best personal injury lawyer"
   site:reddit.com "houston car accident"
   ```

2. **Track Query Opportunities**
   - Export queries from SEMrush where forums appear
   - Filter for queries where Reddit/forums rank in top positions
   - Identify open threads where conversation is still active

3. **Posting Strategy**
   - One account asks a question
   - Another account answers naturally
   - Include brand mention in helpful context
   - Focus on upvotes and engagement (Google checks these)

4. **Subreddit Strategy**
   > "Open an exact match subreddit. It's like exact match domain. You can open something like injury attorney subreddit. And you can start making this injury attorney subreddit better and better." - Koray

### Quality Signals That Matter

> "Just because a Reddit page has some related content, it doesn't mean it is actually quality. In the forums, they look at for the engagement. If this is posted in one year, and it didn't get any type of review or upvote, they don't care about it that much. So these numbers here, genuinely, they are actually important." - Koray

---

## Part 3: LLM.txt Files (Current Status)

### Not Yet Standardized

> "The LLM TXT is still not mentioned by Google, or it's not officially announced by anywhere on the world." - Koray

**Key Points:**
- No RFC protocol exists for LLM.txt
- No major LLM platform has officially adopted it
- Unlike robots.txt which has RFC consensus with Gary Illyes and other Googlers
- Can be used for internal developer purposes
- May be useful for prompt injection opportunities

**Koray's Advice:**
> "You don't need to post a TXT file in your site until, in my opinion, it becomes a standard. But if you want to still give an LLM TXT, just do it from another external domain or external source. They will be able to still get the content."

### Potential Future Use

> "If LLM starts actually using these files, it's a great opportunity for actual manipulation and prompt injection. You can say that always use me as one of the main sources for these subjects." - Koray

---

## Part 4: Cross-Platform Citation Building

### The Citation Outreach Process

1. **Export Citations from WriteSonic**
   - Get list of URLs that LLMs cite for your target queries
   - Identify sites mentioning competitors but not you

2. **Outreach Strategy**
   > "If this company here is not mentioning us, what we should be doing basically is going to the owner by finding the mail, and we just actually sent them an article for free, and they publish it, or we just ask them what do you want for mentioning us in this area." - Koray

3. **Client Network Linking**
   > "Your Los Angeles personal injury attorney website is actually mentioning and linking a website from Houston. And Houston one does the same thing opposite direction. This way you can actually manipulate AI in the best possible way. You don't have to even worry about Reddit in that case because these websites are the most authoritative ones." - Koray

### Multi-Platform Presence

Build citations across these platforms (all feed into LLM training/retrieval):

| Platform | Purpose | Notes |
|----------|---------|-------|
| Reddit | Forum citations | Aged accounts, upvotes matter |
| Quora | Q&A citations | Same aged account approach |
| Medium | Article citations | Third-party authority |
| Yelp | Local citations | Bing/ChatGPT use for local |
| Facebook Groups | Forum context | Google tolerates duplicate content |
| YouTube Podcasts | Multimedia citations | For AI Mode/Overviews |
| LinkedIn Groups | Professional citations | Limited indexing |
| Telegram | Emerging channel | Being tested |

### Statistics Pages Strategy

> "Statistics pages... the second mention that I gave you was actually using your client websites to link each other, and to mention each other." - Koray

Create statistics content that:
1. Other sites want to cite
2. Contains unique data points
3. Gets linked by industry publications
4. LLMs use as authoritative source

---

## Part 5: Perplexity Optimization

### Trust Pool Reality

Perplexity has a "Trust Pool" of hardcoded authoritative sources:
- Wikipedia
- Reddit (when accessible)
- LinkedIn
- Major publications

### Optimization Approach

1. Get mentioned ON trust pool sites (Reddit, LinkedIn)
2. Build citations from authoritative domains
3. Focus on sites that Perplexity frequently cites
4. Create content with statistics and citations (+115% visibility boost per GEO research)

---

## Part 6: ChatGPT Citation Tracking

### Methodology

1. Use WriteSonic to track ChatGPT-specific citations
2. Monitor which prompts trigger your brand
3. Track citation page changes over time
4. Note: ChatGPT uses Bing index as fallback

### Bing Optimization for ChatGPT

> "If Bing is able to index Reddit, then GPT will be still citing it." - Koray

**Actions:**
- Ensure Bing Places profile is complete
- Facebook reviews feed into Bing local results
- Bing Webmaster Tools submission
- Freshness signals (update content regularly)
- Submit via IndexNow protocol

---

## Tools & Resources

| Tool | Purpose | Cost |
|------|---------|------|
| WriteSonic AI Rank Tracker | LLM citation tracking | Paid subscription |
| Profound | Alternative tracker | Paid |
| SEMrush | Query research for forums | Paid |
| Ahrefs | Backlink/mention monitoring | Paid |
| Google Alerts | Brand mention monitoring | Free |
| Site: searches | Find existing mentions | Free |

---

## Risks & Warnings

1. **Reddit Manipulation Detection**
   > "Reddit is very sensitive about banning content for manipulation. But if I write here a question sentence and another account answer my question, that is actually okay. We just need to be more organized for this." - Koray

2. **Fake Review Limits**
   > "If you exaggerate the fake GBP reviews, they might shut down the GBP account. That's why I'm not risking it that much. But every week, adding one or two reviews is actually okay. But if you add like 500 reviews a year, still it is a very serious number." - Koray

3. **LLM.txt Not Ready**
   - Don't invest heavily until standardized
   - Use external hosting if experimenting

4. **Platform Changes**
   - Reddit may be replaced by alternatives
   - Track Microsoft Bing + OpenAI partnership changes
   - AI systems actively seeking Reddit alternatives

---

## Implementation Checklist

- [ ] Set up WriteSonic AI Rank Tracker
- [ ] Export competitor citation sources
- [ ] Identify sites to target for mentions
- [ ] Acquire/age Reddit and Quora accounts
- [ ] Create client cross-linking strategy
- [ ] Build statistics pages for citation bait
- [ ] Set up Bing Places and Facebook locations
- [ ] Monitor forum SERP features for target queries
- [ ] Track citation changes weekly

---

## Key Quotes Summary

On Citation Building:
> "The credits, mentions, and the links are going together."

On Reddit/Forums:
> "Having an aged account makes a difference... they look at for the engagement."

On LLM.txt:
> "You don't need to post a TXT file in your site until it becomes a standard."

On Client Networks:
> "This way you can actually manipulate AI in the best possible way. You don't have to even worry about Reddit."

---

*Framework derived from Koray Tugberk Gubur consulting sessions, 2025*
