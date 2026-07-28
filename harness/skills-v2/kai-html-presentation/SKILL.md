---
name: kai-html-presentation
description: Client-ready HTML presentation builder for Kai audit and report folders. Converts weekly audits, monthly audits, marketing reports, scorecards, findings, data-source notes, and action plans into a polished single-file HTML deck with sourced metrics, executive slides, speaker notes, and delivery-ready styling. Use when "HTML presentation", "HTML deck", "client-ready audit deck", "turn this audit into slides", "present the weekly audit", "present the monthly audit", or any request to deliver Kai reports as HTML slides.
---

# /kai-html-presentation — Client-Ready Audit Deck

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

A single-file HTML deck a client can be walked through, built entirely from an audit or report folder that already contains sourced findings and data gaps. Every number on a slide carries a source footer; missing data appears as a Data Gaps slide rather than as a blank.

This skill is for delivery, not analysis. It adds presentation, never findings.

## Done when

Work type `audit-report` — floor **E3/C4/O1** (`harness/eco-floors.yaml`). The deck is the client-facing form of an audit and inherits its floor.

- **E3** — a named human approved the exact deck file, and every quantitative claim on a slide resolves to a claim that already exists in the source artifacts with a source.
- **C4** — the Kai Data Provenance Rule holds: `audit_provenance_lint.py` passes on the source folder, the data mode is on the title slide, every number has a source footer, and `_data-gaps.md` is represented as a slide.
- **O1** — the actions slide names, per action, the metric it targets. A deck whose recommendations move nothing nameable is not finished.

## Constraints

- **The source folder must already hold sourced findings and data gaps.** Read `_data-sources.md`, `_data-gaps.md`, `audit-data.json` or `kai-data.json`, and the main report files before building. If there is no clear source folder, ask for the path. Accepted inputs: `workspace/audits/weekly/<YYYY-MM-DD>/`, `workspace/audits/monthly/<YYYY-MM>/`, `workspace/marketing-audit/`, or any SEO/CRO/report folder carrying `_data-sources.md` and `_data-gaps.md`.
- **Run the lint when the source folder is an audit:**
  ```bash
  python scripts/quality_gates/audit_provenance_lint.py <source-folder> --audit-dir
  ```
- **No new quantitative claims.** A number reaches a slide only if it exists in the source artifacts with a source. Every slide carrying a number carries a source footer. Missing data stays visible as a Data Gaps slide.
- **No placeholder text ships.** The template's placeholders are all replaced with real sections from the source folder.
- **Build from the template.** Start from `assets/audit-deck-template.html` in the `kai-html-presentation` skill directory and copy it to `<source-folder>/html-presentation/index.html` before replacing content.
- **Length:** 8-14 slides for weekly audits, 10-18 for monthly audits.
- **Design:** first slide identifies client, audit period, data mode, and retrieval date. Prefer dense, readable operator slides over marketing hero pages. Tables for scorecards, decisions, source inventory, and action plans. Short chart-like HTML blocks for trends only when the values are sourced. Text stays inside its containers at desktop and mobile widths. Restrained color — neutral background, dark text, one accent, status colors. No nested cards or decorative blobs. Key facts never live only inside images or screenshots.
- **Slide shape:**
  ```html
  <section class="slide">
    <header>
      <p class="eyebrow">Audit period</p>
      <h2>Slide title</h2>
    </header>
    <div class="slide-body">
      <!-- source-backed content -->
    </div>
    <footer>Sources: ...</footer>
  </section>
  ```
  Use `data-mode`, `source-tier`, and `retrieved-at` labels where helpful.
- **Approval doctrine:** the deck is a delivery artifact. Nothing here publishes, sends, or mutates a live channel.

## Context

| Need | Load |
|---|---|
| Deck skeleton and styling | `assets/audit-deck-template.html` (in this skill's directory) |
| Source ledgers and collected numbers | `_data-sources.md`, `_data-gaps.md`, `audit-data.json` / `kai-data.json` in the source folder |
| Provenance modes, source tiers, gap handling | `harness/references/audit-data-provenance.md` |
| Dashboard spec or data contract instead of slides | `/kai-data-dashboard` |

**Required slide order — weekly audit:** title and audit scope · executive snapshot · weekly scorecard · what changed this week · red and yellow flags · channel findings · conversion and lead capture · paid/content/SEO highlights when applicable · this week's actions · data sources and gaps.

**Required slide order — monthly audit:** title and audit scope · executive summary · 30-day scorecard · KPI trend summary · channel decisions · conversion and lead capture · search and AEO health · paid media and budget decision when applicable · lifecycle, retention, or reputation findings when applicable · strategic learning · next-month plan · data sources and gaps.

**Output:** `<source-folder>/html-presentation/index.html`, and optionally `<source-folder>/html-presentation/notes.md` for presenter notes that should not appear on client slides. Report the deck path in the final response.

## Escalate when

- The source folder has no `_data-sources.md` / `_data-gaps.md`, or its findings are unsourced — the deck would launder unsourced claims into a client-facing artifact.
- The provenance lint fails and the fix would require inventing or re-deriving a number.
- The client wants a number, trend, or comparison the source folder does not contain.
- The source folder is `internal_demo` but the deck is headed to a real client.
- The ask is analysis rather than delivery — route to the audit skill that owns the finding.
