# Two Weeks With OpenClaw. Here's What Actually Works.

**Headline character count: 53**
**Target: 1,400-1,600 words**
**Hashtags: #AI #AIAgents #Entrepreneurship #SoftwareEngineering #Automation**
**Publish: Tuesday-Thursday, 9-11 AM ET**

---

## Article

I installed OpenClaw two weeks ago. I've been running it mostly through WhatsApp. Messaging my agent from my phone, getting things done while I'm walking around, sitting in a meeting, wherever. That part is genuinely cool. And my biggest takeaway is that most of what people are posting about agentic workflows is nonsense.

Not all of it. Managing things through a messaging app you already live in — that works. Actually getting agents to do complex coding and autonomous workflows from a chat window — that's where reality sets in. Here's the honest breakdown — what worked, what didn't, and what I'd tell anyone thinking about setting one up.

## Scripts Beat Free-Roaming Agents Every Time

The single most useful thing I've done is write specific scripts that the agent calls on command. Not "go figure this out." Not "build me a dashboard." **Predefined scripts that do exactly one thing, exactly the way I want.**

The agent doesn't have to think. It doesn't have to go traipsing through my file system guessing what I need. It calls the script. The script runs. The result comes back clean.

I spend the upfront time coding these scripts — yes, with AI helping me write them. For small, single-purpose scripts this works great. The agent writes it, I run it, it does what I asked. But once you're building something bigger — a real application, a complex integration, anything with moving parts — I open a terminal and an IDE and edit it properly. We're not freeballing everything through a chat window. **You still need to look at the code on complicated programs, and anyone telling you otherwise is selling something.**

The pattern that works: write a tight script, test it, hand it to the agent as a callable tool. The agent becomes a dispatcher, not a developer. That's where the leverage actually is.

This isn't just my experience talking. Anthropic's engineering team published a paper back in November showing that code execution through predefined scripts reduced token usage by 98.7% compared to letting agents chain raw tool calls. Cloudflare independently validated the same pattern and called it "Code Mode." **The companies building the models are telling you the same thing — scripts beat autonomy.**

## Lead Notifications Are Table Stakes. Follow-Up Is the Win.

Here's something embarrassing. I set up Discord notifications for when leads come in, calls happen, and users sign up. One channel per project. The agent monitors everything and pings me.

Then I realized most people already have this. Zapier does this. Webhooks do this. You don't need an AI agent to push a notification.

What you do need the agent for is **what happens after the notification**. Following up with the lead. Drafting a response. Pulling context from previous interactions. Flagging which leads are worth my time based on the data. That's where a solopreneur actually gets leverage from an agent. The notification is just plumbing. The follow-up intelligence is the product.

If you're building an agent system and the main thing it does is send you alerts, you built an expensive webhook.

## Enterprise Is Where It Gets Interesting — and Humbling

I've been testing this in a larger company setting. Here's the problem nobody talks about: **you can't buy 400 Claude subscriptions.** The API costs are unpredictable when you don't know how employees will use it. And giving everyone full agentic access to company systems is a security nightmare.

What I landed on is a sandboxed OpenClaw instance with specific scripts that employees can run. Think of it less as "everyone gets their own AI agent" and more as "everyone gets a controlled interface that can do specific things."

Look up this data. Pull this report. Put this file in Google Drive. Summarize this document. That's it. Specific scripts with specific permissions and specific roles. The AI acts as **a utility, not an autonomous agent.** It's more like a really smart internal tool than a digital employee.

This is less exciting than the Twitter demos. It's also the only version that actually works when you have compliance requirements, data sensitivity, and people who will absolutely break anything you give them unsupervised access to.

Anthropic's own recommendation in that same paper: "a secure execution environment with appropriate sandboxing, resource limits, and monitoring." They're not saying give every employee an autonomous agent. They're saying **sandbox it, limit it, and watch it.** That's exactly what I built before I even read their paper.

## Most Agentic Workflow Demos Are Kanban Boards That Don't Do Anything

I need to say this because I keep seeing it. People post these elaborate agent setups with beautiful front-end dashboards showing tasks flowing between agents. Kanban boards with AI workers assigned to each lane. Multi-agent orchestration diagrams that look like NASA mission control.

**Who is using that?** Seriously. Who wakes up, opens their agent Kanban board, and gets actual business value from it?

I've built some of these myself. I know the temptation. It feels productive. It looks impressive in a demo. But when you strip away the UI and ask what the agents actually accomplished, the answer is usually: they moved cards around and generated text that nobody read.

The useful agent work I've done is boring. A script that pulls analytics. A notification followed by a drafted response. A data lookup that saves me 20 minutes. None of it photographs well. All of it saves me real time.

If your agent setup requires a dashboard to prove it's working, it probably isn't.

## You Don't Need a Mac Mini Server Farm

For the local hardware crowd — I respect the instinct to self-host. Privacy matters. Control matters. But if you're buying an expensive machine and still routing requests to Claude, ChatGPT, and Gemini through their APIs, you just bought an expensive router.

My setup runs on a basic server. Not a Mac Mini studio. Not a GPU cluster. A regular machine with decent RAM. I'm calling Claude, ChatGPT, Gemini, and OpenRouter for the model inference. I'm using custom APIs for data gathering. The compute happens in the cloud. The orchestration happens on a cheap box.

You need local hardware when you're running local models. If you're not running local models, save the money. **A computer with some RAM and a stable internet connection is the entire hardware requirement.** Everything else is aesthetics.

## What I'd Actually Recommend

Two weeks in, here's what I'd tell someone starting from zero:

1. **Start with scripts, not agents.** Write five scripts that automate your most repetitive tasks. Test them. Make sure they work perfectly. Then give an agent the ability to call those scripts on command.

2. **Separate the notification from the action.** Webhooks handle notifications. Your agent should handle the thinking that comes after — drafting responses, pulling context, making recommendations.

3. **Sandbox everything for teams.** Don't give employees open-ended AI access. Give them a controlled interface with specific capabilities and clear guardrails. It's less fun and infinitely more practical.

4. **Skip the dashboard.** If you need a visual interface to track what your agent is doing, the agent isn't doing enough to justify itself. The best agent work is invisible — it just shows up as time saved.

5. **Don't overbuild hardware.** Unless you're running local models, a basic machine with API access is all you need. Spend the money on API credits instead. That's where the actual intelligence comes from.

## The Honest Take

AI agents are a great experiment right now. They're worth setting up to understand where the technology is going. Some of the workflows will surprise you with how useful they are. But I've also seen a lot of dumb stuff in two weeks. A lot of building for the sake of building. A lot of demos that wouldn't survive contact with a real business problem.

The people who will get the most value from agents are the ones who treat them like infrastructure — boring, reliable, specific. Not the ones building autonomous empire-running dashboards that look incredible in a screen recording and do nothing when the camera turns off.

Build the scripts. Automate the follow-ups. Sandbox the access. Skip the vanity metrics. That's the actual playbook after two weeks.

What's your agent setup look like right now? Tell me the most useful thing it does — not the flashiest. I want to hear what actually works.

---

#AI #AIAgents #Entrepreneurship #SoftwareEngineering #Automation

---

## Publishing Notes

**First comment (post immediately after publishing):**
> "OpenClaw is open source if anyone wants to try the same setup. DM me 'AGENT' and I'll walk you through the scripts, Discord integration, and the enterprise sandboxing approach."

**Four U's Score:**
- Unique: 4/4 — First-person honest retrospective that pushes back against mainstream agent hype, based on real daily use
- Useful: 4/4 — Five concrete recommendations, clear do/don't framework, immediately actionable
- Ultra-specific: 4/4 — "Two weeks," "400 subscriptions," 98.7% token reduction stat, Anthropic + Cloudflare citations, specific tools named
- Urgent: 4/4 — Everyone is setting up agents right now and most are doing it wrong — intervenes at the decision point
- **Total: 16/16**

**Algorithmic Authorship compliance:**
- [x] Conditions after main clauses
- [x] Instructions start with verbs
- [x] Short declarative sentences
- [x] Numbered lists for steps, bullets for types
- [x] Entities named twice before switching to attributes
- [x] Anchor words connect sentences
- [x] Examples follow declarations
- [x] Answers bolded, not query terms
- [x] No links in first sentence of paragraphs
- [x] No external links in body — Anthropic/Cloudflare cited by name (readers can Google), link in first comment

**Voice match notes:**
- "We're not freeballing everything" — authentic Connor phrasing pulled directly from transcript
- "I've seen a lot of dumb stuff" — kept his exact words, doesn't soften the take
- Honest about his own mistakes ("Then I realized most people already have this")
- Practical over impressive — every section ends with what actually works, not what looks cool
- Pushback on hype without being cynical — acknowledges the experiment has value
- "Expensive webhook" and "expensive router" — punchy analogies that match his style
- CTA asks for "most useful thing, not the flashiest" — filters for real answers
- ~1,500 words — LinkedIn thought leadership sweet spot
