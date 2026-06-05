# CloudTalk — Tech Stack Deep Dive

> Compiled 2026-05-30. Sources: CloudTalk job postings (Workable/startup.jobs), StackShare-derived listing, CloudTalk Help Center, Deepgram/DEV vendor write-ups. Anything not directly stated is marked **(inference)**.

## The headline finding
**CloudTalk's CeTe AI voice agent runs the exact same component vendors as KaiCalls:** Deepgram (STT) + GPT‑4o/Claude (LLM) + ElevenLabs (TTS). The voice-AI layer is commoditized — *neither product has a voice-quality moat.* The fight is productization, distribution, and pricing, not the model. Don't try to out-voice them.

---

## 1. Application / web platform

| Layer | Tech |
|---|---|
| **Backend** | **Node.js + TypeScript**, **GraphQL** APIs (billing systems explicitly built on Node) |
| **Frontend (web)** | **Angular** |
| **Mobile** | **React Native** |
| **Primary DB** | **MySQL / MariaDB** |
| **Other data** | **PostgreSQL**, **MongoDB**, **Redis** (cache), **Elasticsearch** (search/analytics) |
| **Cloud / orchestration** | **AWS**, **Kubernetes (EKS)**, **Docker** |
| **IaC / config** | **Terraform**, **Ansible**, **Helm** |
| **Observability** | **Prometheus**, **Datadog** |
| **Tooling / process** | Git, Jira; ~56-person engineering org in a **Spotify squad model**; ~200 staff from 30 countries; eng hubs in **Bratislava + Prague** (100% remote-friendly across Europe) |

Source: [Node.js Developer posting](https://startup.jobs/nodejs-developer-remote-in-europe-cloudtalk-4284581), [Senior SWE (Node.js + Angular)](https://apply.workable.com/cloudtalk/j/4219848AC5), [DevOps posting](https://startup.jobs/devops-engineer-remote-in-europe-cloudtalk-4519908), [Careers](https://www.cloudtalk.io/careers/).

## 2. Telephony / voice infrastructure

- **WebRTC** for browser calling — *officially Chrome-only* ([Help Center](https://help.cloudtalk.io/en/articles/2144647-system-network-requirements)).
- **SIP** support — bring-your-own SIP devices via `<Username>@<Server>`, no auth proxy ([SIP devices doc](https://help.cloudtalk.io/en/articles/5361606-using-sip-devices-with-cloudtalk)).
- Full **cloud PBX**: ACD, IVR, call queuing/recording, ring groups, VIP queues, call masking.
- **Carrier reach:** local numbers in **160 countries**, claimed **99.999% uptime** (homepage).
- **(inference)** Category-standard architecture would be SIP-ingress edge proxies (Kamailio/FreeSWITCH-class) feeding K8s-orchestrated media pipelines into WebRTC gateways — consistent with their EKS footprint, but *not confirmed for CloudTalk specifically*.
- **Key point:** CloudTalk **owns its telephony carrier stack end-to-end.** That's the genuine moat — it's expensive and slow to replicate, and it powers the 160-country numbers and the all-in-one platform.

## 3. CeTe AI voice agent stack (the overlap with KaiCalls)

| Function | CloudTalk CeTe | KaiCalls |
|---|---|---|
| **Speech-to-text** | **Deepgram** | Deepgram / OpenAI (via Vapi) |
| **LLM** | **GPT‑4o or Claude** (user-selectable) | OpenRouter → Claude 3 Opus / OpenAI |
| **Text-to-speech** | **ElevenLabs** | ElevenLabs |
| **Orchestration** | **In-house**, on top of owned telephony | **Vapi** (third-party orchestrator) |
| **Builder** | No-code wizard, 60+ languages, persona templates | Prompt/agent templates, setup-by-phone |

Source: [Deepgram buyer's guide](https://deepgram.com/learn/best-voice-ai-agents-2026-buyers-guide), [CloudTalk AI Voice Agents](https://www.cloudtalk.io/ai-voice-agents/), [eesel AI features](https://www.eesel.ai/blog/cloudtalk-ai-features).

### What this means strategically
1. **Same voice vendors → no quality moat for either side.** Demos will sound comparable. Stop any positioning that implies KaiCalls has uniquely better-sounding AI; it's the same ElevenLabs/Deepgram pipe.
2. **CloudTalk's orchestration is in-house + on owned telephony.** Better unit economics at scale (no Vapi markup) — yet they price CeTe at €350/mo + seats. They are *choosing* margin over down-market price, which is exactly the gap KaiCalls exploits at $69 flat.
3. **KaiCalls' Vapi dependency is a margin/risk flag.** At scale, the Vapi orchestration markup compresses KaiCalls' per-minute economics and is a single-vendor dependency. CloudTalk's owned stack is the long-game advantage if KaiCalls ever grows into volume. *Worth a roadmap note: own more of the orchestration layer eventually.*
4. **The real moats are asymmetric:** CloudTalk = owned carrier infra + 160-country numbers + 100+ integrations. KaiCalls = product/UX (phone-first "just call Kai" secretary), flat pricing, vertical+geo go-to-market. **Compete where you're moated; don't fight on the commoditized middle.**

## 4. One-line takeaway
> CloudTalk and KaiCalls build the AI agent from the *same* Lego bricks (Deepgram + GPT‑4o/Claude + ElevenLabs). CloudTalk wraps them in an owned global call-center platform sold by the seat; KaiCalls wraps them in a $69 phone-first secretary. The bricks aren't the battle — the wrapper and the price are.
