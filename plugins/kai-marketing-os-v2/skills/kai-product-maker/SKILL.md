---
name: kai-product-maker
description: Build a Gumroad-ready digital product from scratch — ebook, card deck, playbook, Notion template, or flipbook. Walks from concept → content outline → design brief → per-item markdown → images → multi-format build (PDF, HTML flipbook, Notion, card deck) → Gumroad sales page + email blast + launch assets. Use when "make a digital product", "build an ebook", "create a playbook", "card deck", "notion template product", "gumroad product", "make a pdf to sell", or any request to ship a sellable information product.
---

## Objective

A Gumroad-ready digital product a buyer would pay $7–$97 for, plus the assets that sell it: the finished deliverable (PDF, HTML flipbook, Notion deck, or card set), a sales page, a three-email launch sequence, launch video scripts, and a customer-facing package containing only what the buyer should receive.

The product is built from `content/*.md` and `images/`, assembled by a build script, and governed by a design brief locked before any content is written. Design inconsistency is the single largest reason an information product reads as cheap.

**Use this** when the user has a topic and an audience and wants a sellable artifact, or has drafts but no structure, images, or sales page. **Do not use it** for a free lead magnet (`/kai-write`, `/kai-landing-page`), for a sales page on a finished PDF (`/kai-write`), or for anything that is software rather than a static digital good.

## Done when

Work type `campaign` — floor **E5/C3/O4** (`harness/eco-floors.yaml`), composite. A product launch is a multi-asset work item: the deliverable, the sales page, the email sequence, and the launch video each carry their own child floor, and the campaign is CLOSED only when every child is CLOSED and the campaign threshold is met. One unshipped asset keeps it open.

- **E5** — the Gumroad listing exists with thumbnail, sales copy, and uploaded files; the live listing reads back matching the approved bundle; the downloaded package opens and the PDF or flipbook renders end to end with working navigation.
- **C3** — sales copy scores **12+/16** on Four U's with zero banned words and a clear CTA; content passes a Four U's check at **12+/16**; a non-producer read the finished deliverable end to end. The brief matches the shipped product with no design drift, and images hold to the character reference.
- **O4** — units sold, revenue, and conversion rate against a threshold declared before launch, read from Gumroad at the declared window. Baseline and threshold are set before the listing goes live.

Launch evidence checklist: every content file referenced by the build lives in `content/`; the zip contains only customer-facing files (no research, no old drafts); three launch emails queued; one launch video scripted.

## Constraints

- **Approval gates twice before production.** The one-paragraph concept is approved before the brief; `PRODUCT_BRIEF.md` is approved before any content is written. Skipping either produces a product that gets rebuilt.
- **Content lives only in `content/*.md`.** The build is downstream. Never edit assembled HTML or PDF directly — the next build overwrites it.
- **Every unit is structured identically.** Chapters share a shape, cards share a shape. Structural drift across items is what makes a product read as amateur.
- **Images come last** among production assets, after content and brief are locked, because iteration on them is the most expensive step. Pin the character reference in every image prompt; kill style drift before generating more.
- **Sales copy comes after the product is finished.** Writing it earlier means writing about a product that does not exist yet.
- **Facts carry sources.** Statistics, patent numbers, and quotes go in a `Research/` folder beside `content/` with the source cited. An unsourceable number does not ship in a paid product.
- **Quality gate every five units.** Run `/kai-gate` for a Four U's score and fix before producing more; a batch of twenty bad units costs twenty rewrites.
- **Ship examples, not theory** — real screenshots, real numbers, real scripts.
- **Scope is locked at the unit count set in the concept.** A tenth chapter when nine was the plan is a 1.1 release, not this release.
- **No launch video means no traffic.** A Gumroad listing without launch content is a dead listing.

## Context

| Need | Load |
|---|---|
| Product, ICP, voice, positioning | `MARKETING.md` (project root); run `/kai-start` if absent |
| Ground truth for a finished 9-chapter PDF ebook ($47–67) | `E:\Dev2\DigitalProduct\AlgoProduct\` |
| Ground truth for a 30-card mobile-first Notion deck ($37) | `E:\Dev2\DigitalProduct\ApprovalEngine\` |
| Ground truth for an HTML flipbook + PDF, 20 workflows ($37) | `E:\Dev2\DigitalProduct\CommentConnorPlaybook\` |
| Design brief structure to copy | `CommentConnorPlaybook/PRODUCT_BRIEF.md` |
| Build prompt structure to copy | `CommentConnorPlaybook/BUILD_PROMPT.md` |
| Sales page structure to copy | `AlgoProduct/GUMROAD_SALES_COPY.md` |
| Customer package structure | `AlgoProduct/CUSTOMER_PACKAGE_STRUCTURE.md` |
| Production checklist structure (priority, time estimates, why-it-matters) | `AlgoProduct/PRODUCTION_CHECKLIST.md` |
| Batch image generation pattern | `CommentConnorPlaybook/generate_images.py` |

All three examples share the same scaffolding — numbered `content/*.md`, `images/`, `PRODUCT_BRIEF.md`, `BUILD_PROMPT.md`, a build script, sales copy, and a production checklist.

**Six concept decisions**, made before the scaffold exists: working title and subtitle; the one-sentence promise (what changes for the reader); format; price point ($7 / $17 / $27 / $37 / $47 / $67 / $97 — a higher price buys more production polish, not more pages); unit count (chapters, workflows, cards, templates — this sizes everything downstream); and source material.

**Format choice drives everything downstream:**

| Format | Shape | Build tool |
|---|---|---|
| PDF ebook | Linear read, 30–80 pages | pandoc + xelatex, or `AlgoProduct/merge_pdfs.py` + `AlgoProduct/HOW_TO_COMBINE_PDFS.md` |
| HTML flipbook + PDF | Illustrated, page-by-page, designed | `CommentConnorPlaybook/build_html.py` (self-contained HTML, base64 images, keyboard + touch nav) |
| HTML print version | Same content, `@page` + print CSS, browser-to-PDF | `CommentConnorPlaybook/build.py` |
| Notion card deck | Mobile-first, scannable, 20–50 cards | `ApprovalEngine/setup_notion.py` + `NOTION_IMPORT.csv` |
| Template pack | Fill-in worksheets and prompts | Usually a bolt-on, not standalone |

**Folder scaffold** at `E:\Dev2\DigitalProduct\<ProductName>\`:

```
<ProductName>/
├── PRODUCT_BRIEF.md              # design + spec, locked before content
├── BUILD_PROMPT.md               # how a fresh session assembles deliverables
├── content/                      # 00_ front matter, 01_-NN_ in reading order, zero-padded
├── images/                       # character_reference.png, cover.png, dividers, per-item art
├── Research/                     # source notes (optional)
├── GUMROAD_SALES_COPY.md
├── EMAIL_BLAST.md
├── COVER_IMAGE_PROMPT.md
├── PRODUCTION_CHECKLIST.md
├── VIDEO_SCRIPTS.md
└── <ProductName>_Package/        # customer zip: START_HERE.txt, MAIN.pdf, bonuses, README.md
```

**`PRODUCT_BRIEF.md` minimum sections:** what you are building (one paragraph, tone matched to the product); aesthetic direction (one named mood plus 3–5 references); color palette (bg / surface / border / primary text / dim text / accent / danger / success, 6–8 hex codes); typography (headline, body, code — Google Fonts for HTML with system fallbacks, plus italics, stamps, letter-spacing rules); page or card layout with a per-page element list; full page sequence front to back; image specs (character reference, cover dimensions, per-item style, consistency rules); distribution formats.

**Unit structure.** An ebook chapter: H2 title, one-paragraph setup, numbered or bulleted body, a "watch out for" callout, a "why this works" callout, a forward link. A card or workflow: `## Situation`, `## Goal`, `## What NOT to say`, `## Use this instead` (script or prompt in a code block), `## Why this works`, then tags.

**Image set:** `character_reference.png` (consistency sheet, not shipped), `cover.png` (1600×900 Gumroad, 2:3 portrait for PDF), `cat_<name>.png` per section cluster, `01_<slug>.png` per item, `Product_Thumbnail.png` (400×400).

**`BUILD_PROMPT.md`** is self-contained for a fresh session: what exists (content, images, brief files to read), what to build (one section per deliverable), and what not to regenerate.

**Sales assets, in order:** `GUMROAD_SALES_COPY.md` (headline and subheadline; hook framing the problem painfully; the reveal; proof with screenshots, numbers, case study; what's inside; who it is and is not for; price anchor and CTA; guarantee and PS), `EMAIL_BLAST.md` (tease → launch → last-call, mirroring the sales page hook), `COVER_IMAGE_PROMPT.md` (the exact prompt used), `VIDEO_SCRIPTS.md` (1–2 hook-first 30–60s scripts, composed with `/kai-video`).

**Composes with:** `/kai-brand` (voice), `/kai-write` (any single file), `/kai-gate` (scoring), `/kai-video` and `/kai-video-production` (launch video), `/kai-email-system` (sequence), `/kai-repurpose` (product → 15+ social assets), `/kai-competitors` (who else sells this).

## Escalate when

- The source material does not contain enough substance for the declared unit count — a padded product refunds.
- A statistic, quote, or screenshot central to the pitch cannot be sourced.
- The price point and the production polish disagree and the user wants the higher price anyway.
- Images drift from the character reference and re-generation would exceed the agreed budget.
- The build produces a deliverable that does not render cleanly and the fix requires changing the locked brief.
- A testimonial or customer result would appear in the sales copy without written permission — route to `/kai-proof-builder` first.
