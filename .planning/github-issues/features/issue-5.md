---
issue: 5
title: "Add agent-readiness / AEO audit for public docs and pages"
state: OPEN
labels: [documentation, enhancement]
assignees: []
created: 2026-04-17T21:13:40Z
updated: 2026-04-17T21:13:40Z
author: cgallic
url: https://github.com/cgallic/kai-cmo-harness/issues/5
comments_count: 0
reactions_count: 0
---

# #5: Add agent-readiness / AEO audit for public docs and pages

## Description

## Summary
Add an Agentic SEO / Agentic Engine Optimization audit pass for Kai CMO harness docs and any public-facing app/docs pages.

Reference: https://github.com/addyosmani/agentic-seo

## Why
If we expect AI coding agents and research agents to discover and correctly use the harness, our docs should be optimized for machine consumption as well as human consumption.

The `agentic-seo` repo is a lightweight checklist/linter for this. Even if we do not adopt the tool directly, it gives us a concrete rubric.

## Proposed scope
- Audit the repo/docs against agent-readiness basics:
  - `robots.txt` policy is explicit
  - `llms.txt` exists (or we intentionally decide not to ship one)
  - key docs are available in markdown / agent-readable form
  - page size / token cost is reasonable for core entry pages
  - capability signaling is explicit (what the harness does, APIs, auth model, approvals, run lifecycle)
  - docs avoid hiding critical usage information only behind JS-heavy UI
- Decide whether to:
  - vendor or invoke `agentic-seo` in CI, or
  - implement a smaller internal check tailored to Kai CMO harness
- If useful, publish a minimal `llms.txt` / machine-readable entrypoint pointing agents to:
  - core overview
  - runtime concepts
  - API docs
  - approval / human-review flow
  - local setup / auth

## Deliverables
- Recommendation memo: adopt `agentic-seo` vs custom checks
- Initial audit report with failures / gaps
- Follow-up fixes for the highest-value issues
- Optional CI check to prevent regressions

## Acceptance criteria
- We have a clear answer on whether Kai CMO harness is discoverable and legible to agents
- At least one machine-oriented entrypoint exists (`llms.txt`, equivalent page, or explicit decision not to add it)
- Top-level docs clearly expose the harness' capabilities and constraints to both humans and agents
