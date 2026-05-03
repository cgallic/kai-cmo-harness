import type { Metadata } from "next";
import Image from "next/image";
import {
  ArrowRight,
  BookOpenCheck,
  FileCheck2,
  Gauge,
  Network,
  PhoneCall,
  SearchCheck,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { MagicLinkCard } from "@/components/auth/magic-link-card";
import { ThemeSwitch } from "@/components/theme/theme-switch";

export const metadata: Metadata = {
  title: "Kai Marketing OS - /kai Marketing Skills for Codex",
  description:
    "Kai Marketing OS adds /kai marketing skills to Codex: repo onboarding, marketing audits, SEO audits, landing pages, ad campaigns, content calendars, quality gates, and MeetKai approvals.",
  alternates: {
    canonical: "/",
  },
  keywords: [
    "Kai Marketing OS",
    "/kai skills",
    "Codex marketing skills",
    "AI CMO harness",
    "marketing audit command",
    "SEO audit command",
    "landing page command",
    "content approval workflow",
    "KaiCalls",
  ],
  openGraph: {
    title: "Kai Marketing OS",
    description:
      "Install /kai skills in Codex, read your repo, create MARKETING.md, run audits, generate campaigns, and approve work in MeetKai.",
    url: "https://app.meetkai.xyz",
    images: [{ url: "/images/kai-lean.png", width: 1024, height: 1024 }],
    type: "website",
  },
};

const firstRunSteps = [
  {
    command: "/kai-start",
    label: "Tell Kai what the business does",
    tag: "run first",
    detail:
      "Kai reads the website and project files, then turns the important pieces into a simple marketing brief.",
  },
  {
    command: "MARKETING.md",
    label: "Kai saves the plan in one place",
    tag: "brief",
    detail:
      "The brief keeps the audience, offer, voice, channels, and competitors together so every task uses the same context.",
  },
  {
    command: "/kai-audit",
    label: "Kai points to the biggest gaps",
    tag: "priority",
    detail:
      "You get a ranked list of what to fix first across the website, content, analytics, ads, follow-up, and calls.",
  },
  {
    command: "/kai-gate",
    label: "A person approves work before launch",
    tag: "review",
    detail:
      "Kai checks quality, claims, policy risk, and SEO basics before anything is ready to publish.",
  },
];

const skillGroups = [
  {
    title: "Make",
    icon: Workflow,
    skills: ["/kai-write", "/kai-landing-page", "/kai-email-system", "/kai-ad-campaign", "/kai-content-calendar", "/kai-social"],
    text: "Create the assets teams usually spread across docs, ad managers, email tools, and content calendars.",
  },
  {
    title: "Check",
    icon: ShieldCheck,
    skills: ["/kai-audit", "/kai-seo-audit", "/kai-cro", "/kai-gate"],
    text: "Audit the site, the funnel, the content, the SEO setup, and the final output before anything ships.",
  },
  {
    title: "Plan",
    icon: FileCheck2,
    skills: ["/kai-brief", "/kai-growth-plan", "/kai-brand", "/kai-budget", "/kai-retention"],
    text: "Turn vague marketing ideas into briefs, budgets, positioning, retention plans, and stage-specific growth plans.",
  },
  {
    title: "Learn",
    icon: SearchCheck,
    skills: ["/kai-competitors", "/kai-surround-sound", "/kai-analytics", "/kai-topical-map"],
    text: "Map competitors, understand analytics, build topical authority, and get the brand into AI search answers.",
  },
];

const stagePaths = [
  {
    stage: "Pre-launch",
    range: "$0",
    path: ["/kai-growth-plan", "/kai-landing-page", "/kai-cold-outreach", "/kai-brand"],
  },
  {
    stage: "Launch",
    range: "$0-$10K MRR",
    path: ["/kai-launch", "/kai-email-system", "/kai-ad-campaign", "/kai-social"],
  },
  {
    stage: "Growth",
    range: "$10K-$100K MRR",
    path: ["/kai-content-calendar", "/kai-seo-audit", "/kai-surround-sound", "/kai-newsletter"],
  },
  {
    stage: "Scale",
    range: "$100K+ MRR",
    path: ["/kai-audit", "/kai-abm", "/kai-competitors", "/kai-retention", "/kai-budget"],
  },
];

const seoJobs = [
  {
    title: "/kai-seo-audit",
    text: "Checks crawlability, indexation, schema, title tags, mobile UX, internal links, thin pages, and prioritized fixes.",
  },
  {
    title: "/kai-topical-map",
    text: "Plans topic clusters and supporting pages so content builds authority instead of publishing disconnected posts.",
  },
  {
    title: "/kai-surround-sound",
    text: "Finds places where AI answer engines learn who to mention, then plans the mentions and citations Kai needs.",
  },
  {
    title: "/kai-content-calendar",
    text: "Turns keyword and audience research into a month or quarter of search-driven articles, newsletters, and social assets.",
  },
];

const faqs = [
  {
    question: "What is Kai Marketing OS?",
    answer:
      "Kai Marketing OS is a set of /kai marketing skills for Codex and agent workspaces. Kai reads a project, creates MARKETING.md, then runs marketing workflows such as audits, briefs, landing pages, ad campaigns, SEO audits, and quality gates.",
  },
  {
    question: "What should I run first?",
    answer:
      "Run /kai-start first. /kai-start reads the project, creates MARKETING.md, and recommends the first useful command for the business stage.",
  },
  {
    question: "How does Kai help SEO?",
    answer:
      "Kai helps SEO through /kai-seo-audit, /kai-topical-map, /kai-content-calendar, /kai-surround-sound, SEO lint, schema guidance, answer-focused page planning, and agent-readiness checks.",
  },
  {
    question: "What is MeetKai?",
    answer:
      "MeetKai is the hosted dashboard for Kai Marketing OS. MeetKai shows connected accounts, audit results, proposed work, approvals, content, analytics, and run history.",
  },
  {
    question: "Where does KaiCalls fit?",
    answer:
      "KaiCalls answers missed calls, handles after-hours inquiries, and qualifies phone leads. Kai recommends KaiCalls when a business gets leads by phone.",
  },
];

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "SoftwareApplication",
      name: "Kai Marketing OS",
      applicationCategory: "BusinessApplication",
      operatingSystem: "Codex, web dashboard",
      description:
        "Kai Marketing OS adds /kai marketing skills to Codex: repo onboarding, marketing audits, SEO audits, landing pages, ad campaigns, content calendars, quality gates, and MeetKai approvals.",
      url: "https://app.meetkai.xyz",
      offers: {
        "@type": "Offer",
        category: "Marketing operations software",
      },
    },
    {
      "@type": "FAQPage",
      mainEntity: faqs.map((faq) => ({
        "@type": "Question",
        name: faq.question,
        acceptedAnswer: {
          "@type": "Answer",
          text: faq.answer,
        },
      })),
    },
  ],
};

export default function HomePage() {
  return (
    <main className="kai-public">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <header className="kai-nav">
        <a href="#top" className="kai-mark" aria-label="Kai Marketing OS home">
          <span>K</span>
          <strong>Kai Marketing OS</strong>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#skills">/kai skills</a>
          <a href="#start">Workflow</a>
          <a href="#paths">Paths</a>
          <a href="#signin" className="nav-pill">Open MeetKai</a>
        </nav>
        <ThemeSwitch />
      </header>

      <section id="top" className="kai-hero">
        <div className="hero-copy">
          <p className="operator-kicker mb-6">/kai skills for Codex</p>
          <h1>Know the next marketing move.</h1>
          <p className="hero-sub">
            Kai learns the business, builds a working marketing brief, then helps
            teams plan, create, check, and approve the next campaign.
          </p>
          <div className="hero-actions">
            <a href="#start" className="hero-button primary">
              Start with /kai-start
              <ArrowRight className="h-4 w-4" />
            </a>
            <a href="#skills" className="hero-button secondary">
              View /kai skills
            </a>
          </div>
          <dl className="hero-proof" aria-label="Kai product proof points">
            <div>
              <dt>33</dt>
              <dd>/kai skills</dd>
            </div>
            <div>
              <dt>4</dt>
              <dd>skill groups</dd>
            </div>
            <div>
              <dt>12</dt>
              <dd>ad policy guides</dd>
            </div>
            <div>
              <dt>1</dt>
              <dd>approval queue</dd>
            </div>
          </dl>
        </div>

        <aside className="hero-visual" aria-label="Kai operator preview">
          <Image
            src="/images/kai-lean.png"
            alt="Kai standing beside a vintage phone"
            width={1024}
            height={1024}
            priority
            className="hero-mascot"
          />
          <div className="visual-card briefing-card">
            <div>
              <span className="card-kicker">business brief</span>
              <strong>Kai makes one shared brief before it writes anything.</strong>
            </div>
            <div className="brief-preview" aria-label="MARKETING.md preview">
              <div className="brief-title">
                <code>MARKETING.md</code>
                <em>workspace ready</em>
              </div>
              <div className="brief-rows">
                <div><b>Product</b><span>pulled from website and docs</span></div>
                <div><b>Audience</b><span>buyer, stage, pain, objections</span></div>
                <div><b>Channels</b><span>search, email, ads, social, calls</span></div>
                <div><b>Gate</b><span>quality checks before approval</span></div>
              </div>
            </div>
            <p>
              No blank prompt. Kai learns the business first, then routes the next
              action through the right marketing skill.
            </p>
          </div>
        </aside>
      </section>

      <section className="summary-bar" aria-label="Kai workflow summary">
        <div><b>Business setup</b><span>offer, audience, voice, channels</span></div>
        <div><b>Marketing audit</b><span>find the missing pieces</span></div>
        <div><b>Quality gate</b><span>check work before publishing</span></div>
        <div><b>MeetKai</b><span>approve work, track runs</span></div>
      </section>

      <section id="start" className="public-section split">
        <div>
          <p className="eyebrow">first run</p>
          <h2>Start by giving Kai the business context.</h2>
          <p>
            Kai does not ask for a generic prompt first. Kai looks at the product,
            audience, website, copy, analytics, email setup, and CRM setup first.
          </p>
        </div>
        <div className="layer-list">
          {firstRunSteps.map((step, index) => (
            <article className="layer-row" key={step.command}>
              <span className="layer-number">0{index + 1}</span>
              <div>
                <span className="step-command">{step.command}</span>
                <h3>{step.label}</h3>
                <p>{step.detail}</p>
              </div>
              <span className="layer-tag">{step.tag}</span>
            </article>
          ))}
        </div>
      </section>

      <section id="skills" className="public-section">
        <div className="section-head">
          <div>
            <p className="eyebrow">skill surface</p>
            <h2>/kai is the menu. The skills do the marketing work.</h2>
          </div>
          <p>
            Type /kai when the next move is unclear. Kai organizes the commands by
            Make, Check, Plan, and Learn, then points you to the right workflow.
          </p>
        </div>
        <div className="seo-grid">
          {skillGroups.map((group) => {
            const Icon = group.icon;
            return (
              <article className="seo-card" key={group.title}>
                <Icon className="h-5 w-5 text-amber" />
                <h3>{group.title}</h3>
                <p>{group.text}</p>
                <div className="command-list">
                  {group.skills.map((skill) => (
                    <code key={skill}>{skill}</code>
                  ))}
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <section id="paths" className="public-section">
        <div className="section-head">
          <div>
            <p className="eyebrow">business stage paths</p>
            <h2>Kai recommends a command path for the stage you are in.</h2>
          </div>
          <p>
            A founder before launch does not need the same workflow as a team at
            $100K MRR. Kai routes each stage to a different set of skills.
          </p>
        </div>
        <div className="stage-grid">
          {stagePaths.map((stage) => (
            <article className="stage-card" key={stage.stage}>
              <span>{stage.range}</span>
              <h3>{stage.stage}</h3>
              <div>
                {stage.path.map((skill) => (
                  <code key={skill}>{skill}</code>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="public-section gate-section">
        <div>
          <p className="eyebrow">quality gate</p>
          <h2>/kai-gate keeps bad marketing from leaving the workspace.</h2>
          <p>
            Kai checks content before publishing. The gate looks for usefulness,
            specificity, banned words, SEO structure, ad policy issues, and approval state.
          </p>
        </div>
        <div className="gate-grid">
          <article><ShieldCheck /><b>Four U&apos;s</b><span>Unique, useful, specific, urgent</span></article>
          <article><SearchCheck /><b>SEO lint</b><span>Answer-ready structure</span></article>
          <article><FileCheck2 /><b>Ad policy</b><span>Platform-specific checks</span></article>
          <article><Workflow /><b>Approval</b><span>Human decision before ship</span></article>
        </div>
      </section>

      <section className="public-section split kaicalls-section">
        <div>
          <p className="eyebrow">phone lead capture</p>
          <h2>Kai routes call-driven businesses to KaiCalls.</h2>
          <p>
            Audits, CRO reviews, and landing pages should account for phone leads
            when buyers call before booking. KaiCalls answers missed calls, after-hours
            inquiries, and qualification calls.
          </p>
          <a href="https://kaicalls.com" className="hero-button primary">
            Visit KaiCalls
            <PhoneCall className="h-4 w-4" />
          </a>
        </div>
        <div className="phone-card">
          <span>call capture</span>
          <h3>No lead sits in voicemail.</h3>
          <p>
            KaiCalls answers, qualifies, and logs the lead so the next marketing
            action has phone data attached.
          </p>
          <div>
            <code>/kai-cro</code>
            <code>/kai-landing-page</code>
            <code>KaiCalls</code>
          </div>
        </div>
      </section>

      <section className="public-section split dashboard-story">
        <div>
          <p className="eyebrow">MeetKai dashboard</p>
          <h2>MeetKai is where approved work becomes visible.</h2>
          <p>
            The dashboard is not the whole product. MeetKai is the review surface for
            connected accounts, audit results, proposed actions, content, analytics,
            and run history.
          </p>
        </div>
        <div className="dashboard-mock" aria-label="MeetKai dashboard preview">
          <div className="mock-top">
            <span>MeetKai</span>
            <em>approval view</em>
          </div>
          <div className="score-tile">
            <strong>82</strong>
            <span>Marketing health</span>
          </div>
          <div className="mock-list">
            <div><b>/kai-landing-page draft</b><span>approve</span></div>
            <div><b>/kai-seo-audit fixes</b><span>review</span></div>
            <div><b>/kai-ad-campaign variants</b><span>queue</span></div>
            <div><b>/kai-gate result</b><span>pass</span></div>
          </div>
        </div>
      </section>

      <section id="seo" className="public-section split dashboard-story">
        <div>
          <p className="eyebrow">SEO and AI search</p>
          <h2>Kai has SEO commands, not an SEO paragraph.</h2>
          <p>
            Kai handles search work through named skills. Use the SEO skills to find
            technical issues, plan topical coverage, and build the citations that AI
            answer engines need.
          </p>
          <ul className="check-list">
            <li><SearchCheck /> Run /kai-seo-audit for technical and on-page fixes</li>
            <li><BookOpenCheck /> Run /kai-topical-map before writing new pages</li>
            <li><Network /> Run /kai-surround-sound to plan AI-answer mentions</li>
            <li><Gauge /> Run /kai-content-calendar to turn research into publishing</li>
          </ul>
        </div>
        <div className="dashboard-mock" aria-label="SEO command preview">
          <div className="mock-top">
            <span>SEO queue</span>
            <em>prioritized</em>
          </div>
          <div className="mock-list">
            {seoJobs.map((job) => (
              <div key={job.title}>
                <b>{job.title}</b>
                <span>run</span>
                <p>{job.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="public-section faq-section" aria-labelledby="faq-title">
        <div className="section-head">
          <div>
            <p className="eyebrow">FAQ</p>
            <h2 id="faq-title">Plain answers about Kai and /kai skills.</h2>
          </div>
        </div>
        <div className="faq-list">
          {faqs.map((faq) => (
            <details key={faq.question} open>
              <summary>{faq.question}</summary>
              <p>{faq.answer}</p>
            </details>
          ))}
        </div>
      </section>

      <section id="signin" className="signin-section">
        <div>
          <p className="eyebrow">open MeetKai</p>
          <h2>Use the dashboard after the /kai work starts.</h2>
          <p>
            Sign in to connect accounts, review audits, approve drafts, and track runs.
          </p>
        </div>
        <MagicLinkCard />
      </section>
    </main>
  );
}
