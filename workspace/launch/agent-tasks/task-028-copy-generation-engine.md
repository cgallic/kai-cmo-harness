# Task 028: Build copy generation engine

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 5. Creative and Asset Generation
**Priority:** P1
**Depends on:** 027
**Estimated complexity:** Large

## Context

The copy generation engine is the creative production center of Kai. Given a CreativeBrief, it produces copy for any marketing format — web sections, landing pages, ad copy, social posts, emails, and scripts. Each format has its own structural rules, length constraints, and quality requirements. The engine applies the right framework from `knowledge/frameworks/` for each format, respects platform constraints, and integrates with the quality gate pipeline (four U's scoring, banned word check, SEO lint). This is where the marketing knowledge base becomes actionable output.

The engine does NOT call an LLM directly — it produces structured prompts, templates, and output schemas that an LLM (Claude Code or similar) can fill. Think of it as the "recipe generator" that knows exactly what ingredients and structure each piece of content needs.

## Scope

Build `kai/creative/copy_engine.py` with format-specific generator functions that take a CreativeBrief and produce structured content templates, prompts, and output schemas. Also define the quality gate integration points and retry logic.

## Detailed Requirements

### File: `kai/creative/copy_engine.py`

**Data model: CopyOutput**
- `id: str` — unique identifier, format `cpy_{uuid_hex[:12]}`
- `brief_id: str` — links back to the CreativeBrief
- `format: str` — ContentFormat value
- `sections: List[Dict[str, Any]]` — ordered list of content sections, each with: `section_type`, `content`, `word_count`, `notes`
- `full_text: str` — the complete copy as a single string
- `word_count: int` — total word count
- `quality_scores: Dict[str, Any]` — quality gate results (populated after checking), default empty dict
- `quality_status: str` — "pending", "passed", "failed", "retry_1", "retry_2", default "pending"
- `revision_notes: List[str]` — notes for revision if quality gates fail, default empty list
- `metadata: Dict[str, Any]` — catch-all, default empty dict
- `created_at: Optional[str]` — ISO timestamp

**Web section generators — each returns a Dict with section content:**

1. `generate_hero_section(brief: Dict[str, Any]) -> Dict[str, Any]`
   - Output: `{"section_type": "hero", "headline": "", "subheadline": "", "cta_text": "", "cta_url": "", "supporting_text": "", "trust_indicator": ""}`
   - Headline: max 10 words, action-oriented, includes primary benefit
   - Subheadline: max 20 words, expands on headline with specificity
   - Trust indicator: years in business, review count, or certification (from brief.proof_available)
   - Apply perception engineering layer 3 (permission) — CTA removes friction

2. `generate_value_prop_section(brief: Dict[str, Any]) -> Dict[str, Any]`
   - Output: `{"section_type": "value_props", "heading": "", "props": [{"icon_suggestion": "", "title": "", "description": ""}], "layout": "3-column|4-column"}`
   - 3-4 value propositions, each with a short title (3-5 words) and description (1-2 sentences)
   - Props should be specific to the business, not generic

3. `generate_testimonial_block(brief: Dict[str, Any]) -> Dict[str, Any]`
   - Output: `{"section_type": "testimonials", "heading": "", "testimonials": [{"quote": "", "name": "", "title": "", "rating": 5, "photo_placeholder": ""}], "layout": "cards|carousel|grid"}`
   - Uses trust signals from business profile
   - If no testimonials available, output a placeholder with instructions for collecting them

4. `generate_cta_block(brief: Dict[str, Any]) -> Dict[str, Any]`
   - Output: `{"section_type": "cta_block", "heading": "", "body": "", "cta_text": "", "cta_url": "", "urgency_element": "", "trust_element": ""}`
   - Urgency element: time-limited offer, scarcity, or consequence of inaction
   - Trust element: guarantee, review count, or certification

5. `generate_faq_section(brief: Dict[str, Any]) -> Dict[str, Any]`
   - Output: `{"section_type": "faq", "heading": "", "faqs": [{"question": "", "answer": ""}], "schema_markup": {}}`
   - 5-8 FAQs derived from persona objections and common questions
   - Answers follow algorithmic authorship rules (conditions after main clause, instructions start with verbs)
   - Include FAQ schema.org markup template

6. `generate_service_description(brief: Dict[str, Any]) -> Dict[str, Any]`
   - Output: `{"section_type": "service_description", "heading": "", "intro": "", "features": [{"name": "", "description": ""}], "process_steps": [{"step": 1, "title": "", "description": ""}], "cta": ""}`
   - Process steps as numbered list (algorithmic authorship rule 4)
   - Features as bullet list

**Landing page generator:**

7. `generate_landing_page(brief: Dict[str, Any]) -> Dict[str, Any]`
   - Assembles a full landing page by calling section generators in order:
     1. Hero section
     2. Social proof bar (review count, years, certifications — single line)
     3. Problem statement (perception engineering layer 1 — destabilize cached beliefs)
     4. Value props
     5. How it works (3-step process)
     6. Testimonials
     7. Offer section (if applicable)
     8. FAQ
     9. Final CTA block
   - Output: `{"format": "landing_page", "sections": [...], "meta": {"title": "", "description": ""}, "schema_markup": {}}`
   - Apply perception engineering throughout: perception → context → permission
   - Include meta title and description

**Ad copy generators:**

8. `generate_google_ads_copy(brief: Dict[str, Any]) -> Dict[str, Any]`
   - Output: `{"format": "google_ads", "headlines": [...], "descriptions": [...], "sitelinks": [...], "callouts": [...]}`
   - 15 headlines (max 30 chars each), 4 descriptions (max 90 chars each)
   - Pin headline 1 to include primary keyword, headline 2 to include CTA
   - Include 4 sitelink suggestions and 4 callout suggestions
   - Note: compliance check against `harness/references/google-ads-policy-reference.md` needed

9. `generate_meta_ads_copy(brief: Dict[str, Any]) -> Dict[str, Any]`
   - Output: `{"format": "meta_ads", "variants": [{"primary_text": "", "headline": "", "description": "", "cta_button": ""}]}`
   - 3 variants with different angles (benefit, social proof, urgency)
   - Primary text max 125 chars for above-fold visibility
   - Note: compliance check against `harness/references/meta-ads-rules.md` needed
   - Include Special Ad Category notice if applicable (housing, employment, credit)

10. `generate_social_ad_copy(brief: Dict[str, Any], platform: str) -> Dict[str, Any]`
    - Platform-aware ad copy generation (linkedin, tiktok, pinterest, snapchat, etc.)
    - Output varies by platform but always includes: primary text, headline/title, CTA
    - Respects PLATFORM_CONSTRAINTS from brief.py

**Social post generators:**

11. `generate_social_post(brief: Dict[str, Any], platform: str) -> Dict[str, Any]`
    - Output: `{"format": "social_post", "platform": "", "caption": "", "hashtags": [], "cta": "", "post_type": "text|image|carousel|reel"}`
    - Platform-specific formatting:
      - Instagram: emoji-friendly, hashtag-heavy (up to 30), visual-first language
      - LinkedIn: professional tone, thought leadership angle, 3-5 hashtags
      - Facebook: conversational, community-oriented, question hooks
      - TikTok: hook in first line, trending language, minimal hashtags
      - X/Twitter: concise, punchy, max 280 chars
    - Hook in first line always (algorithmic authorship principle)

**Email generators:**

12. `generate_email(brief: Dict[str, Any], email_type: str) -> Dict[str, Any]`
    - Output: `{"format": "email", "email_type": "", "subject_line": "", "preview_text": "", "body_sections": [{"type": "greeting|body|cta|signature", "content": ""}], "cta_text": "", "cta_url": ""}`
    - Email types and their characteristics:
      - `welcome`: warm, sets expectations, delivers promised value, 150-300 words
      - `nurture`: educational, builds trust, positions expertise, 200-500 words
      - `cold_outreach`: ultra-concise, personalized first line, clear ask, 75-150 words. Must follow CAN-SPAM rules from `harness/references/cold-email-rules.md`
      - `review_request`: grateful, specific, easy link, 75-150 words
      - `reactivation`: reminder of value, special offer, low-pressure, 100-250 words
      - `quote_followup`: helpful, addresses concerns, provides additional value, 100-200 words
    - Subject line: max 60 chars, no spam trigger words, personalization token where possible
    - Preview text: max 90 chars, complements (does not repeat) subject line

13. `generate_email_sequence(brief: Dict[str, Any], sequence_type: str) -> Dict[str, Any]`
    - Output: `{"format": "email_sequence", "sequence_type": "", "emails": [{"email_number": 1, "delay_hours": 0, "subject": "", "preview": "", "body": "", "cta": ""}]}`
    - Generates the full sequence of emails for a given type
    - Sequence types match ProposedAction payload templates: welcome (3 emails), review_request (2 emails), reactivation (3 emails), quote_followup (3 emails)

**Script generators:**

14. `generate_call_script(brief: Dict[str, Any]) -> Dict[str, Any]`
    - Output: `{"format": "call_script", "greeting": "", "qualification_questions": [...], "pitch": "", "objection_handlers": [...], "close": "", "voicemail_script": ""}`
    - Include 3-5 qualification questions
    - Include 3-5 common objection handlers with responses
    - Include a voicemail script (30 seconds max, ~80 words)

15. `generate_video_script(brief: Dict[str, Any]) -> Dict[str, Any]`
    - Output: `{"format": "video_script", "hook": "", "hook_duration_seconds": 3, "main_content": [{"timestamp": "", "visual": "", "narration": "", "text_overlay": ""}], "cta": "", "total_duration_seconds": 0}`
    - Hook must grab attention in first 3 seconds
    - Structure: hook → problem → solution → proof → CTA
    - Include text overlay suggestions for each segment

**Quality gate integration:**

16. `check_quality(output: Dict[str, Any], brief: Dict[str, Any]) -> Dict[str, Any]`
    - Defines the quality check pipeline for a CopyOutput:
      - Read thresholds from brief.quality_gate_thresholds
      - Define which checks apply: four_us (always), banned_words (always), seo_lint (only if brief.target_keyword is set)
      - Return a quality check plan: `{"checks": [{"name": "four_us", "threshold": 12, "script": "scripts/quality_gates/four_us_score.py"}, ...], "applies_seo_lint": bool}`
    - NOTE: This function does NOT execute the scripts. It returns the check plan for the execution layer to run.

17. `plan_revision(output: Dict[str, Any], quality_results: Dict[str, Any]) -> Dict[str, Any]`
    - Given quality gate results, produce revision instructions:
      - If four_us score < threshold: identify which U's scored lowest and suggest specific improvements
      - If banned words found: list the words and suggest replacements
      - If SEO lint failures: list specific rule violations with fix instructions
    - Return: `{"revision_needed": bool, "revision_instructions": [...], "retry_number": int, "max_retries": 2}`

**Main orchestrator:**

18. `generate_copy(brief: Dict[str, Any]) -> Dict[str, Any]`
    - Dispatches to the correct generator based on brief.format
    - Wraps output in CopyOutput structure
    - Attaches quality check plan
    - Returns CopyOutput dict

**Helper: `_apply_algorithmic_authorship(text: str) -> str`**
    - Placeholder function that defines the rules to apply:
      - Conditions after main clause
      - Instructions start with verbs
      - Sentences under 20 words
      - Bold the answer, not query terms
    - Returns the text (actual transformation would be done by the LLM following these rules as instructions)
    - Include the rules as a docstring/comment block for the LLM to reference

**Helper: `_apply_perception_engineering(brief: Dict[str, Any]) -> Dict[str, Any]`**
    - Returns perception engineering layer instructions for the brief:
      - Layer 1 (Perception): what belief to destabilize
      - Layer 2 (Context): what frame shift to apply
      - Layer 3 (Permission): how to remove consequences
    - These are instructions, not executed transformations

## Output Files

- `kai/creative/copy_engine.py`

## Acceptance Criteria

- [ ] `copy_engine.py` contains all 18 functions listed above
- [ ] CopyOutput model has all specified fields with correct types and defaults
- [ ] Web section generators produce correctly structured dicts with all required fields
- [ ] Landing page generator assembles all sections in the correct order with perception engineering
- [ ] Google Ads generator produces 15 headlines (30 char max) and 4 descriptions (90 char max)
- [ ] Meta Ads generator produces 3 variants with above-fold character limits
- [ ] Social post generator handles all 5 platforms with platform-specific formatting
- [ ] Email generator handles all 6 email types with correct word count ranges
- [ ] Email sequence generator produces complete multi-email sequences
- [ ] Script generators include qualification questions, objection handlers, and hooks
- [ ] check_quality returns a plan (does NOT execute scripts)
- [ ] plan_revision produces specific fix instructions for each type of quality failure
- [ ] generate_copy dispatches to correct generator by format
- [ ] Algorithmic authorship rules are documented as comments/docstrings for LLM reference
- [ ] Perception engineering layers are structured as instructions, not executed transformations
- [ ] All functions are pure — no file I/O, no network calls, no script execution

## Reference Materials

- `kai/creative/brief.py` (created by Task 027) — CreativeBrief schema and PLATFORM_CONSTRAINTS
- `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` — 48 SEO writing rules to reference
- `knowledge/frameworks/content-copywriting/perception-engineering.md` — 3-layer persuasion framework
- `knowledge/frameworks/content-copywriting/four-us-framework.md` — quality scoring framework
- `harness/skill-contracts/` — format-specific contracts (blog-post.yaml, meta-ads.yaml, etc.)
- `harness/references/cold-email-rules.md` — CAN-SPAM compliance for cold outreach
- `harness/references/google-ads-policy-reference.md` — Google Ads policy rules
- `harness/references/meta-ads-rules.md` — Meta ads policy rules
- `scripts/quality_gates/` — quality gate scripts (reference paths only, do not execute)
- `CLAUDE.md` — quality gate rules, framework map, algorithmic authorship top 10
