# Market Evidence — Voice Agent Differentiation (July 2026)

> Condensed output of three web-research sweeps run 2026-07-05. Every claim carries its source URL. Items the researchers could not verify are marked **(uncertain)**. Companion to `_strategy.md`.

---

## A. Infrastructure layer economics

### Vapi
- YC W21 (pivot from "Superpowered" notetaker, Nov 2023). **$50M Series B led by Peak XV, May 2026, ~$500M post; $72M total** (Bessemer led the $20M A). ARR "healthy eight figures" per TechCrunch investor source — likely $10–50M. ([TechCrunch](https://techcrunch.com/2026/05/12/vapi-hits-500m-valuation-as-amazon-ring-chose-its-ai-platform-over-40-rivals/), [GlobeNewswire](https://www.globenewswire.com/news-release/2026/05/12/3292882/0/en/vapi-raises-50m-series-b-as-it-reaches-1-billion-calls-powering-the-next-generation-of-enterprise-voice-ai.html), [BVP](https://www.bvp.com/news/our-investment-in-vapi-the-voice-ai-developer-platform))
- Scale claims: 1B+ cumulative calls, 1–5M calls/day, 1M+ developers, 2.7M agents, ~100 employees. Anchor customer: **Amazon Ring routes 100% of inbound calls through Vapi** (chosen over 40+ vendors).
- Pricing: **$0.05/min platform fee**; STT/LLM/TTS pass-through or BYO keys; +$10/concurrency line/mo; HIPAA $2,000/mo; ZDR $1,000/mo. ([vapi.ai/pricing](https://vapi.ai/pricing))
- Realistic all-in COGS: **~$0.10–0.25/min typical**; teardowns cite $0.07–0.33 depending on stack. ([Cekura](https://www.cekura.ai/blogs/vapi-ai-pricing), [Lindy](https://www.lindy.ai/blog/vapi-ai), [Zeeg](https://zeeg.me/en/blog/post/vapi-ai-pricing))
- Competes with builders? Mostly no — no acquisitions, no white-label tier. But: vertical SEO "custom agents" pages (dental, e-commerce), first-party "Vapi Voices" TTS (~$0.0025/min), and direct enterprise sales (Ring). Edges blurring. ([vapi.ai/custom-agents/dental-care-agent](https://vapi.ai/custom-agents/dental-care-agent), [Tracxn](https://tracxn.com/d/companies/vapi/___SoH-BLiCayDw_mTGLHOiTAhjxhsyDFWfZsDK9vzq4g))

### Alternatives (platform risk / swap options)
| Platform | Price | Notes |
|---|---|---|
| Retell AI | $0.07/min base; ~$0.085–0.19 all-in | **$60M ARR (3x YoY), 55M calls/mo, ~30 people, only ~$14M raised** ([Retell](https://www.retellai.com/pricing), [TipRanks](https://www.tipranks.com/news/private-companies/retell-ai-triples-arr-to-60-million-as-voice-agent-adoption-surges), [ARR Club](https://www.arr.club/retell/retell-scales-to-50m-arr-with-a-team-of-30-people)) |
| Bland AI | ~$0.09–0.11/min | In-house models; $40M Series B + $50M June 2026 after 180 rejections ([Fortune](https://fortune.com/2026/06/16/voice-ai-bland-50-million-after-being-rejected-by-180-investors/)) |
| ElevenLabs Agents | $0.08/min overage | **$500M ARR, $11B valuation — the gravity well**; owns TTS layer ([ElevenLabs](https://elevenlabs.io/pricing/agents), [TechCrunch](https://techcrunch.com/2026/01/13/elevenlabs-ceo-says-the-voice-ai-startup-crossed-330-million-arr-last-year/)) |
| OpenAI Realtime | ~$0.18–0.46/min uncached; $0.05–0.10 cached; mini ~60% cheaper | Speech-to-speech collapses STT→LLM→TTS pipeline; cut prices twice ([HackerNoon](https://hackernoon.com/openai-realtime-api-pricing-in-2026-real-world-data-from-4000-measured-sessions), [OpenAI](https://developers.openai.com/api/docs/pricing)) |
| Twilio ConversationRelay | $0.07/min + voice | Telephony incumbent absorbing orchestration ([Twilio](https://www.twilio.com/en-us/products/conversational-ai/pricing)) |
| Pipecat / LiveKit | OSS free; cloud from ~$0.01/min | Price floor for anyone with engineers ([LiveKit](https://livekit.com/), [GitHub](https://github.com/pipecat-ai/pipecat)) |

- Component deflation: streaming STT $0.0015–0.024/min; commodity TTS $0.0025–0.015/min. ([Coval](https://www.coval.ai/blog/best-speech-to-text-providers-in-2026-independent-benchmarks-and-how-to-choose/), [Softcery](https://softcery.com/lab/how-to-choose-stt-tts-for-ai-voice-agents-in-2025-a-comprehensive-guide))

### Wrapper commoditization
- Wrapper-of-the-wrapper platforms exist solely to white-label Vapi: [Vapify](https://vapify.agency/), [VoiceAIWrapper](https://voiceaiwrapper.com/), [Voicerr](https://voicerr.ai/), Trillet. Synthflow agency plan **$1,400/mo, unlimited sub-accounts, Stripe rebilling** ([Synthflow](https://synthflow.ai/)); Autocalls.ai $0.09/min all-in.
- Upwork/Fiverr saturated with Vapi/Retell/GHL voice-agent gigs; YouTube guru economy ("[Build a $10,000 AI Receptionist in 25 Minutes](https://www.youtube.com/watch?v=nyzSRnuPAS8)", "[Sell AI Receptionist to Local Businesses ($500/Month)](https://www.youtube.com/watch?v=ACJhO0TD1tA)").
- Standard agency model: $500–1,500/mo per local business on ~$0.10–0.25/min COGS; direct-resell margins cap at **10–20%** per wrapper vendors themselves (self-interested source). ([Trillet](https://trillet.ai/blogs/top-10-white-label-voice-ai-platforms-for-agencies-2026); VoiceAIWrapper insights post, June 2026)
- One vendor claims voice-AI agencies see **15–25% monthly churn** year one; 40% lower churn on native platforms vs wrapper resellers **(uncertain — vendor source)**. ([Trillet](https://trillet.ai/blogs/voice-agent-client-retention-strategies))
- No publicized exits of Vapi-built startups found **(uncertain — absence of evidence)**.

---

## B. SMB AI receptionist competitive landscape

### Direct competitors
| Player | Pricing | Traction |
|---|---|---|
| **Rosie** (heyrosie.com) | $49/mo (250 min) / $149 (1,000) / $299 (2,000); no-card trial | 1,900+ SMBs, 3.1M+ calls claimed; likely bootstrapped **(uncertain)**; cheapest tier omits in-call booking ([pricing](https://heyrosie.com/pricing), [oncrew.ai](https://oncrew.ai/blog/rosie-ai-pricing-2026)) |
| **Goodcall** | ~$59–199/agent, unlimited min but **$0.50/unique-caller overage** | ~$8M raised since 2021, ex-Google founder, Yelp partnership; hasn't converted head start ([pricing](https://www.goodcall.com/pricing), [TechCrunch](https://techcrunch.com/2021/09/01/goodcall-picks-up-4m-yelp-partnership-to-answer-merchant-inbound-calls/)) |
| **Smith.ai** | AI from $95/mo (~$1.60–2.40/call); hybrid $292.50–1,170/mo, $9.75/call overage; $2,000 AI-training fee | ~3,000 customers; strongest legal brand; Lawmatics/Clio/MyCase integrations ([pricing](https://smith.ai/pricing/ai-receptionist), [blog](https://smith.ai/blog/ai-receptionist-now-integrates-with-lawmatics)) |
| **Dialzara** | $29–349/mo, $0.35–0.48/min overage; 88 industry templates | Trustpilot 4.0 on only 19 reviews — price-floor player ([pricing](https://dialzara.com/pricing)) |
| **My AI Front Desk** | Wholesale **$54.99**/receptionist; white-label $419/mo; resellers retail $250–500 | Commoditizes from below via agency channel ([white-label](https://www.myaifrontdesk.com/white-label)) |
| **Sameday AI** (YC) | ~$349–449/mo flat **(uncertain)** | Home services, between SMB tools and Avoca ([pricing](https://www.gosameday.com/pricing)) |
| **Loman.ai** | ~$299/mo | Restaurant-focused; traction unclear **(uncertain)** ([pricing](https://loman.ai/pricing)) |
| **Voctiv** | Free–$29/mo consumer app | Not a serious B2B threat ([pricing](https://voctiv.com/pricing-page/)) |

### Incumbent bundling (the structural threat)
- **Jobber AI Receptionist** (Aug 2025): help center cites **$29/mo for 30 conversations, $0.79/extra**; included on Plus plan. Third parties cite $99 — conflicting **(uncertain)**. ([help.getjobber.com](https://help.getjobber.com/hc/en-us/articles/25315927533847-Receptionist-powered-by-Jobber-AI), [PRNewswire](https://www.prnewswire.com/news-releases/jobber-launches-ai-powered-receptionist-to-answer-calls-and-texts-for-busy-home-service-businesses-302531125.html))
- **Housecall Pro CSR AI**: quote-only add-on; third-party estimates $200–500/mo. ([housecallpro.com](https://www.housecallpro.com/features/ai-team/csr-ai/))
- **ServiceTitan Contact Center Pro**: quote-only atop $245–398/tech/mo — mid-market. ([servicetitan.com](https://www.servicetitan.com/features/pro/contact-center))
- **Podium AI Employee**: $99–399 add-on atop $399–999 plans; real spend $500–800/mo; Trustpilot 1.5/5 on billing disputes. ([replifast](https://www.replifast.com/blog/podium-pricing-2026))
- **Weave** acquired TrueLark (May 2025) — dental/medical AI receptionist inside $399+/mo platform. ([getweave.com](https://www.getweave.com/ai-receptionist/))

### Human answering services (price umbrella)
- Ruby $235/mo for **50 human minutes** ($4.70/min over); AnswerConnect $325/200 min; PATLive from $75 at $2.60/min; Moneypenny ~$165/50 min. Human labor keeps them 3–10x AI per-minute pricing; AI moves are defensive. ([ruby.com](https://www.ruby.com/plans-and-pricing/), [vokaro](https://vokaro.net/en/costs/virtual-receptionist-costs))

### Distribution reality
- Buying happens via vendor-authored/affiliate comparison content ("best AI answering service 2026" SERPs); the 74.1% unanswered-contractor-calls stat is the category's universal hook. ([leadtruffle](https://www.leadtruffle.co/blog/best-ai-answering-services-contractors-2026/), [ringly.io](https://www.ringly.io/blog/best-ai-answering-service))
- Marketplaces: Jobber sells native (channel closed); Square App Marketplace lists AI receptionists; no meaningful QuickBooks/Google Business Profile third-party channel found **(uncertain)**. ([squareup.com](https://squareup.com/us/en/app-marketplace/app/ai-receptionist))

---

## C. Moat patterns among winners

| Company | Vertical | Capital/scale | The actual moat |
|---|---|---|---|
| **Avoca** | HVAC/home services | $125M+ at **$1B** (Apr 2026, KP/Meritech/GC); 800+ customers; ~$1B jobs booked/yr claimed | Live ServiceTitan booking, capacity-aware dispatch, trade-network distribution (Nexstar, Turnpoint, 1-800-GOT-JUNK?); founders did field immersion ([PRNewswire](https://www.prnewswire.com/news-releases/avoca-raises-125m-at-1b-valuation-to-power-americas-services-economy-with-ai-302753962.html), [Fortune](https://fortune.com/2026/04/27/avoca-ai-agents-missed-calls-hvac-plumbing-roofing-kleiner-perkins-chen-shrivastava-braswell/)) |
| **Sierra** | Enterprise CX | **$100M ARR in 7 quarters**; $10B → ~$15.8B **(uncertain)** | Outcome pricing (per autonomous resolution, escalations free), enterprise trust ([TechCrunch](https://techcrunch.com/2025/11/21/bret-taylors-sierra-reaches-100m-arr-in-under-two-years/), [Cheeky Pint](https://cheekypint.substack.com/p/bret-taylor-of-sierra-on-ai-agents)) |
| **Decagon** | Enterprise support | $4.5B valuation on ~$35M ARR — priced for perfection | 100+ enterprise logos ([Forbes](https://www.forbes.com/sites/alexyork/2026/02/06/ai-agent-startup-decagon-triples-valuation-to-45-billion/)) |
| **PolyAI** | Enterprise voice | $86M Series D at $750M; ~$40M ARR | Governance tooling, 2,000+ deployments, 45 languages ([Forbes](https://www.forbes.com/sites/iainmartin/2025/12/15/polyai-raises-86-million-as-fight-to-answer-calls-with-ai-heats-up/)) |
| **Toma** (YC W24) | Auto dealers | $17M a16z; 100+ dealers, 7-fig ARR <1yr, no sales team | DMS/workflow depth; trained on each dealer's real calls; founders lived in dealerships ([TechCrunch](https://techcrunch.com/2025/06/05/tomas-ai-voice-agents-have-taken-off-at-car-dealerships-and-attracted-funding-from-a16z/)) |
| **Slang.ai** | Restaurants | $36M Series B; 2,000+ locations at $399–799/mo | 25M-call proprietary dataset; low AOV caps pricing ([PRNewswire](https://www.prnewswire.com/news-releases/slang-ai-raises-36m-series-b-to-scale-ai-for-guest-communications-across-every-restaurant-302695306.html)) |
| **HappyRobot** | Logistics | $44M Series B at ~$500M; DHL/Ryder/Schneider | Freight workflows (carrier check calls, load booking) ([Tech Funding News](https://techfundingnews.com/happyrobot-44m-series-b-ai-workforce-supply-chain/)) |
| **Salient** | Lending collections | $60M a16z; $25M ARR, zero churn claimed | Loan-system integration + compliance ([Fortune](https://fortune.com/2025/12/18/salients-quiet-ai-boom-how-this-two-year-old-startup-is-building-a-company-to-survive-the-bubble-burst/)) |
| **Numa** | Auto | $48M (Google Gradient); 700–1,300 dealers (claims conflict) | ~$200–400/rooftop + **pay-per-booked-appointment option** ([numa.com](https://numa.com/), [oncrew](https://oncrew.ai/blog/numa-pricing-2026)) |

### VC theses (convergent)
- **a16z / Olivia Moore**: "voice will become the wedge, not the product"; each vertical gets its own core providers "similar to systems of record"; per-minute pricing under pressure; defensibility = vertical expertise + GTM as technical barriers fall; 22% of a recent YC class built with voice. ([a16z 2025 update](https://a16z.com/ai-voice-agents-2025-update/), [interview](https://www.smartspeakers.fm/p/olivia-moore-a16z-voice-as-a-wedge))
- **Bessemer**: demos easy, edge-case reliability is the moat; "customers quickly churn if agents don't consistently deliver"; voice is a new data layer. ([BVP Roadmap](https://www.bvp.com/atlas/roadmap-voice-ai), [Euclid interview](https://insights.euclid.vc/p/whats-working-in-vertical-voice-ai-mike-droesch-bessemer-venture-partners))
- **Menlo**: "defensive moats" (compliance, human sign-off) buy time; "generative moats" (compounding data, expanding workflow coverage) widen the gap. ([Menlo](https://menlovc.com/perspective/software-finally-gets-to-work-the-opportunity-in-vertical-ai/))
- Consensus across commentary: wrappers commoditize; moats form in workflow, compliance, proprietary data, vertical integration. No evidence buyers care about "built on Vapi." ([HatchWorks](https://hatchworks.com/blog/gen-ai/ai-wrapper-product-strategy/), [M Accelerator](https://maccelerator.la/en/blog/startup-strategy/why-ai-wrappers-don-t-have-moats/))

### Outcome pricing
- Sierra per-resolution is the flagship; market ranges (vendor-published, **uncertain**): $3–25/qualified lead, $8–40/booked appointment, $1–6/resolved ticket. Failure mode: contracts never define "resolved/booked" — attribution disputes. ([Aloware](https://aloware.com/ai-voice-agent/outcome-based-pricing), [Cekura](https://www.cekura.ai/blogs/how-to-price-ai-voice-agents), [DILR](https://www.dilr.ai/blog/voice-ai-containment-rate-enterprise-benchmark))

### Consumer sentiment + regulation
- 31% of consumers would hang up on AI (up from 29%, Apr 2026); 85% prefer human; 43.9% yell "human" at bots — **but source sells human answering (biased)** and 13.6% trust AI with complex requests. ([AnswerConnect](https://www.answerconnect.com/blog/news/consumers-turning-away-from-ai-customer-service/), [Futurism](https://futurism.com/artificial-intelligence/customers-fed-up-ai-service-agents))
- Counter-data: only ~3% of missed callers leave voicemail; 27% of home-services inbound calls missed (vendor data, **uncertain**); Slang.ai bypass attempts fell 33% → 22–25% over a year. ([Tradesly](https://www.tradesly.ai/blog/24-7-ai-voice-agents-capture-revenue-loss), [Numa](https://www.numa.com/blog/ai-voice-agent-appointment-booking-rates), [Forbes](https://www.forbes.com/sites/quickerbettertech/2025/10/02/for-restaurants-slang-ai-is-a-great-example-of-an-ai-platform-using-voice-recognition-for-roi/))
- Regulation: FCC Feb 2024 — AI voices are "artificial" under TCPA → outbound AI calls need prior express consent, disclosure, opt-out; $500–1,500/call uncapped; Sept 2024 NPRM on explicit AI-disclosure rules, final status unverified **(uncertain)**. Utah (May 2025), California B.O.T. Act + SB 243 (Jan 2026), Colorado AI Act. **Inbound answering largely sits outside TCPA consent rules — exposure concentrates in outbound.** ([FCC](https://www.fcc.gov/document/fcc-makes-ai-generated-voices-robocalls-illegal), [Federal Register](https://www.federalregister.gov/documents/2024/09/10/2024-19028/implications-of-artificial-intelligence-technologies-on-protecting-consumers-from-unwanted-robocalls), [Alston](https://www.alstonprivacy.com/new-artificial-intelligence-laws-in-effect-in-utah/), [FPF](https://fpf.org/blog/understanding-the-new-wave-of-chatbot-legislation-california-sb-243-and-beyond/))
- SMB owner sentiment (thin primary data): like "sounds human, books into our calendar"; hate urgent callers ringing 5x against inbound-only bots. Direct r/HVAC / r/Plumbing threads not surfaced — worth manual scraping **(uncertain)**. ([smash.vc](https://smash.vc/best-ai-answering-services/))
