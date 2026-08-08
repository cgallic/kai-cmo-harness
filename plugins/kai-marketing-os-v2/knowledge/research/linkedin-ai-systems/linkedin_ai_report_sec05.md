## 5. The People Behind the AI: Key Personnel and Org Structure

AI systems do not emerge from abstract organizational charts; they are built, maintained, and steered by specific individuals whose technical backgrounds, managerial philosophies, and career trajectories shape what gets built and what does not. LinkedIn's AI organization underwent a significant leadership reshuffle between 2024 and 2025, marked by the departure of a 1,000-person org leader to Google DeepMind and the return of a veteran executive as Chief AI Officer. This chapter maps the individuals who currently lead LinkedIn's AI efforts, traces the critical talent movements reshaping the organization, and examines the unique editorial-engineering partnership that governs how AI intersects with content judgment.

### 5.1 AI Leadership

#### 5.1.1 Deepak Agarwal — Chief AI Officer (January 2025)

Deepak Agarwal's return to LinkedIn as Chief AI Officer in January 2025 represents the single most consequential personnel decision in the company's recent AI history.[^122^] It is his second tenure: he previously served as VP of AI for eight years (2012–2020), leading more than 500 engineers and laying the infrastructure foundation that much of LinkedIn's current AI stack still rests upon.[^411^][^412^] In that first stint, he established LinkedIn's AI Academy and an associated empathy program — initiatives that became industry-wide models for corporate AI literacy.[^411^]

Between his LinkedIn tenures, Agarwal served as Chief AI Officer and VP of Consumer and Trust Engineering at Pinterest (2020–2025), where he scaled the AI organization from roughly 200 to approximately 1,000 engineers by unifying AI Foundations, Consumer Engineering, Trust & Safety, and AI Product under a single umbrella.[^2^] His earlier career includes VP of Engineering at Yahoo! and research at AT&T Labs; he is an elected Fellow of the American Statistical Association and has published a book on large-scale recommender systems.[^127^]

Agarwal has articulated a four-pillar mission for his second tenure: push the boundaries of AI innovation; build ethical, inclusive, human-centric AI; advance economic opportunity; and ensure responsible, compliant AI.[^122^][^411^] In podcast appearances, he has emphasized treating AI as an "operating model" rather than isolated tools — a philosophy that shaped his restructuring at Pinterest and is likely informing his current org design at LinkedIn.[^127^]

#### 5.1.2 Hamed Firooz — Principal AI Scientist, FAIT

Under Agarwal's leadership, the Foundation AI Technologies (FAIT) team serves as LinkedIn's central AI research and infrastructure unit. Hamed Firooz, a Principal AI Scientist, leads the approximately 50-person FAIT team and was the driving technical force behind 360Brew, LinkedIn's 150-billion-parameter foundation model for personalization.[^138^][^407^] Firooz's team built 360Brew in approximately nine months, training it on one trillion LinkedIn engagement tokens to solve more than 30 personalization tasks without task-specific fine-tuning.[^147^] The project achieved a reported 20x cost and latency reduction through on-policy knowledge distillation and model compression.[^147^]

Firooz brings 15 years of large-scale AI experience, including a prior role at Meta AI where he led multimodal Content Understanding models.[^138^] His background spans the full stack from model architecture to production serving — a hybrid profile that is rare in an era where AI talent often specializes in either research or engineering. He presented the 360Brew work at the AI Engineer World's Fair 2025.[^138^]

#### 5.1.3 Karthik Ramgopal — Distinguished Engineer, GenAI and Agent Platform

Karthik Ramgopal holds the title of Distinguished Engineer and serves as Uber Technical Lead for the Product Engineering team, with approximately 5,000 engineers in his scope across all member and customer-facing products.[^395^] He is specifically responsible for all Generative AI applications and the Generative AI platform, giving him one of the broadest technical mandates in the organization.[^393^]

Ramgopal was the architect of Hiring Assistant, LinkedIn's first production AI agent, which achieved a 69% higher InMail acceptance rate, 48% less time reviewing applications, and 62% fewer profiles reviewed per hire.[^79^][^44^] He also led the shift from Java to Python as a first-class language for GenAI development, created a prompt source-of-truth service with namespacing and versioning, and built an OpenAI-compatible API abstraction enabling on-the-fly model switching between Azure OpenAI and on-prem fine-tuned models.[^393^][^49^] He presented the agent platform architecture at QCon AI New York 2025.[^56^]

Ramgopal's background is interdisciplinary: he holds a BS in Computer Science from UC Davis and a PhD in Political Science with a focus on machine learning, NLP, and network analysis.[^408^] He joined LinkedIn through the 2013 Pulse acquisition and rose from individual contributor to his current VP-equivalent Distinguished Engineer role.[^404^][^411^]

### 5.2 Critical Talent Movements

#### 5.2.1 Ya Xu → Google DeepMind (September 2024)

Ya Xu's departure for Google DeepMind in September 2024 marked the end of an era. As VP of Engineering and Head of Data & AI, she had led roughly 1,000 data scientists and AI engineers responsible for feed ranking, job search, "People You May Know," and the company's experimentation platforms.[^155^][^57^] She joined LinkedIn as its first female Principal Staff Engineer and built the initial experimentation platform before rising to VP in 2021.[^154^]

Xu holds a PhD in Statistical Machine Learning from Stanford and was named to Fortune's 40 Under 40 in Tech.[^155^] Her background in data-centric statistical ML represented a different philosophical orientation than Agarwal's platform-scale recommender systems expertise. The transition signals a strategic pivot from statistical machine learning toward large-scale AI platforms and GenAI.

The circumstances of her departure are disputed. Anonymous posts on Blind (unverified) claimed she was "debatably forced out," while counter-narratives praised her impact, with one ex-employee stating "she set AI progress forward by 10 years."[^159^] Her move to DeepMind as VP of Engineering suggests the transition was at minimum amicable.[^159^]

#### 5.2.2 Qingquan Song → OpenAI (2025)

Qingquan Song's move to OpenAI in 2025 represents a targeted loss for LinkedIn's technical capabilities. Song was a Senior Staff Machine Learning Engineer in Core AI (2021–2025), specializing in automated machine learning and recommender systems.[^8^] He was a core contributor to LiRank — which won the KDD 2024 Best Paper Award in the Applied Data Science track — and a key author on the Planner-R1 paper exploring agentic reinforcement learning.[^391^][^413^]

Song holds a PhD in Computer Science from Texas A&M (2021) and has published 55 works with more than 2,450 citations.[^8^][^6^] His OpenReview profile confirms the move to OpenAI's foundation team,[^3^] and the Planner-R1 paper carries a footnote reading "Work done while at LinkedIn; currently at OpenAI."[^391^] The loss is consequential because his expertise in AutoML and recommender systems was directly relevant to LinkedIn's core product, and his move signals that his skills were highly valued in the competitive AI market.

#### 5.2.3 Craig Martell's Legacy — From AI Academy to the Pentagon

Craig H. Martell's tenure at LinkedIn in the mid-2010s left a lasting institutional imprint through the LinkedIn AI Academy — one of the industry's first corporate AI literacy programs, designed to train non-technical employees on AI concepts and upskill engineers in ML techniques.[^50^][^51^] It became a model that other technology companies emulated.

Martell's subsequent career illustrates the fungibility of AI leadership across sectors. After LinkedIn, he served as Head of Machine Intelligence at Dropbox and Head of Machine Learning at Lyft before becoming the first Chief Digital and Artificial Intelligence Officer (CDAO) at the U.S. Department of Defense (2022–2024), where he led Task Force Lima on generative AI and testified before Congress.[^41^] In 2025 he joined Lockheed Martin as Vice President and Chief Technology Officer.[^392^][^51^] The trajectory from corporate AI Academy founder to the Pentagon's top AI official demonstrates how AI leadership expertise translates from consumer technology to national security.

### 5.3 Laura Lorenzetti and the Editorial-AI Bridge

#### 5.3.1 The Editorial-Engineering Partnership

Laura Lorenzetti serves as VP of Product and Executive Editor at LinkedIn News, a hybrid role bridging editorial content strategy and AI-driven product development.[^397^] She leads the intersection of algorithmic content distribution and human editorial judgment, overseeing LinkedIn's positioning as a platform that industry observers have called a "de facto competitor to PR Newswire."[^397^]

This editorial-engineering partnership has concrete technical manifestations. LinkedIn's editorial team works directly with AI systems to generate article topics and match them with expert contributors for the platform's collaborative articles — an AI-generated, human-edited product that is one of LinkedIn's most visible GenAI deployments.[^4^][^7^] Lorenzetti manages the trust-authenticity balance as AI-generated content scales and has publicly emphasized authenticity over algorithmic gaming.[^397^] Her discussion with Entrepreneur Magazine Editor-in-Chief Jason Feifer on "What the Algorithm Really Wants" offered rare visibility into how LinkedIn thinks about the editorial-AI interface.[^397^]

#### 5.3.2 Human Annotation at Scale

The editorial-AI bridge extends into content integrity. LinkedIn's anti-abuse systems rely on human editors annotating thousands of posts — distinguishing generic AI-generated content from original writing — to train detection classifiers. This human-in-the-loop approach creates a feedback mechanism where editorial judgment informs AI training data, which in turn shapes algorithmic distribution. Lorenzetti's role in managing this pipeline makes her a central figure in LinkedIn's AI content governance architecture, bridging the gap between machine-scale distribution and human-scale quality judgment.

---

**Table: Key LinkedIn AI Personnel — Roles, Backgrounds, and Current Status**

| Name | Current Role | Key AI Responsibility | Prior Experience / Education | Status |
|------|-------------|----------------------|------------------------------|--------|
| Deepak Agarwal | Chief AI Officer (Jan 2025) | Company-wide AI strategy; Core AI org | VP AI at LinkedIn (2012–2020); CAO at Pinterest (2020–2025); VP Eng at Yahoo!; Fellow, ASA[^122^][^411^] | Active — second tenure |
| Hamed Firooz | Principal AI Scientist, FAIT Lead | 360Brew (150B-param model); personalization; ~50-person team | 15 yrs large-scale AI; ex-Meta AI (multimodal Content Understanding)[^138^][^407^] | Active |
| Karthik Ramgopal | Distinguished Engineer | All GenAI apps and platform; Hiring Assistant architect; ~5,000 engineers in scope | Pulse acquisition (2013); PhD Political Science (ML/NLP); BS CS UC Davis[^395^][^393^] | Active |
| Ya Xu | VP Engineering (former) | Led 1,000-person Data & AI org; feed ranking, PYMK, experimentation | PhD Statistical ML, Stanford; Fortune 40 Under 40[^155^][^57^] | Departed Sep 2024 → Google DeepMind |
| Qingquan Song | Sr. Staff ML Engineer (former) | Core LiRank contributor; Planner-R1 author; AutoML | PhD CS, Texas A&M; 55 papers, 2,450+ citations[^8^][^6^] | Departed 2025 → OpenAI (Foundation Team) |
| Craig Martell | VP/CTO (former) | Founded LinkedIn AI Academy (industry's first) | Head of ML at Lyft; DoD CDAO (2022–2024); CTO Lockheed Martin (2025)[^50^][^51^] | Departed mid-2010s → Lockheed Martin CTO |
| Laura Lorenzetti | VP Product & Executive Editor | Editorial-AI bridge; collaborative articles; content algorithm | Editorial leadership; product strategy[^397^] | Active |
| Daniel Olmedilla | Sr. Director, Trust/Responsible AI | Trust, privacy, responsible AI implementation | Two PhDs; ex-Meta; 100+ pubs, 3,000+ citations; EU Commission advisor[^414^] | Active |
| Fedor Borisyuk | Core Researcher | LiRank (KDD 2024 Best Paper); LiGNN (KDD 2024 Best Paper) | Large-scale ranking and graph ML[^413^] | Active |

The table captures a leadership cohort that is simultaneously deep in production experience and increasingly exposed to competitive talent pressure. Agarwal, Firooz, and Ramgopal form the technical triad shaping LinkedIn's current AI direction: Agarwal at the strategic and organizational level, Firooz at the foundation model and research level, and Ramgopal at the application and platform level. Their combined scope covers the full stack from 150-billion-parameter model training to single-agent production deployment.

Yet the departures column reveals structural vulnerability. The loss of Ya Xu removed a leader who had built and managed a 1,000-person data and AI organization — institutional knowledge that cannot be quickly replaced. Qingquan Song's move to OpenAI stripped LinkedIn of a core contributor to its most impactful ranking system and a researcher with expertise in agentic reinforcement learning — the exact domain LinkedIn is now pursuing. Craig Martell's earlier exit removed the architect of the company's AI culture. The pattern suggests LinkedIn functions as an elite training ground for AI talent, developing practitioners at billion-user scale only to see them recruited by better-funded pure-play AI labs. Agarwal's return may represent an attempt to reverse that centrifugal force by building an environment competitive enough to retain rather than export top technical talent.
