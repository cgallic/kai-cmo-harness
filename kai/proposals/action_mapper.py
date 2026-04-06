"""Finding-to-action mapping engine for the Kai Marketing OS.

This module is the rule engine that converts audit findings into concrete
marketing actions.  Each ``ActionMapping`` encodes which action(s) to
propose for a given finding category, complete with default configuration
for priority, risk, effort, cost, and a payload template that downstream
execution systems can consume directly.

The main entry point is ``map_finding_to_actions``, which accepts an
``AuditFinding`` (as a dict) and returns a list of ``ProposedAction``
dicts ready for ranking, bundling, and scheduling.

Design principles
-----------------
1. **Complete registry.**  Every audit category has at least two mappings.
2. **KaiCalls rule.**  Speed-to-lead findings and any finding that
   mentions missed calls, after hours, phone, or response time will
   always produce a KaiCalls setup recommendation.
3. **Template-based.**  Titles and descriptions use ``{placeholder}``
   syntax filled from finding data and business profile data.
4. **Pure functions.**  No file I/O, no network, no state mutation.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from kai.models.proposal import (
    assign_risk_tier,
    compute_priority_score,
    generate_action_id,
)


# ============================================================================
# Data model
# ============================================================================


@dataclass
class ActionMapping:
    """One mapping rule: finding category + optional pattern --> action type.

    Each mapping encodes the default configuration for the proposed action
    that will be generated when a matching finding is encountered.
    """

    finding_category: str
    action_type: str
    channel: str
    title_template: str
    description_template: str
    default_priority_score: float
    default_risk_tier: str
    default_effort_hours: float
    default_cost: float
    suggested_payload_template: Dict[str, Any]
    finding_pattern: Optional[str] = None
    archetype_tags: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


# ============================================================================
# Mapping Registry -- 36 mappings across 9 categories
# ============================================================================

MAPPING_REGISTRY: List[ActionMapping] = [
    # ------------------------------------------------------------------
    # Website Conversion (category: conversion_path) -- 5 mappings
    # ------------------------------------------------------------------
    ActionMapping(
        finding_category="conversion_path",
        action_type="website_update",
        channel="website",
        title_template="Update CTA on {page}",
        description_template=(
            "Replace the current call-to-action on {page} with a higher-converting "
            "alternative.  Test button copy, color contrast, and placement to "
            "maximize click-through rate."
        ),
        default_priority_score=65.0,
        default_risk_tier="low",
        default_effort_hours=0.5,
        default_cost=0.0,
        suggested_payload_template={
            "page": "",
            "current_cta": "",
            "new_cta": "",
            "cta_type": "button|link|form",
        },
        archetype_tags=["local_service", "professional_service", "ecommerce"],
        tags=["cta", "conversion", "website", "quick_win"],
    ),
    ActionMapping(
        finding_category="conversion_path",
        action_type="website_update",
        channel="website",
        title_template="Rewrite hero section on {page}",
        description_template=(
            "Rewrite the hero headline, subheadline, and primary CTA on {page} "
            "to clearly communicate the value proposition within 5 seconds of "
            "page load.  Apply perception engineering principles."
        ),
        default_priority_score=70.0,
        default_risk_tier="medium",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "page": "",
            "current_hero": "",
            "new_headline": "",
            "new_subheadline": "",
            "new_cta": "",
        },
        archetype_tags=["local_service", "professional_service"],
        tags=["hero", "conversion", "website", "copy"],
    ),
    ActionMapping(
        finding_category="conversion_path",
        action_type="website_update",
        channel="website",
        title_template="Add trust signals to {page}",
        description_template=(
            "Add a trust block to {page} featuring testimonials, certifications, "
            "or stats that reduce buyer hesitation.  Position the block above the "
            "fold or immediately after the hero section."
        ),
        default_priority_score=60.0,
        default_risk_tier="low",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "page": "",
            "block_type": "testimonials|certifications|stats|guarantees",
            "content": [],
        },
        archetype_tags=["local_service", "professional_service"],
        tags=["trust", "conversion", "website"],
    ),
    ActionMapping(
        finding_category="conversion_path",
        action_type="website_update",
        channel="website",
        title_template="Add prominent phone number to {page}",
        description_template=(
            "Make the business phone number prominently visible on {page} with "
            "click-to-call functionality on mobile.  Phone calls convert at 10-15x "
            "the rate of form submissions for service businesses."
        ),
        default_priority_score=75.0,
        default_risk_tier="low",
        default_effort_hours=0.5,
        default_cost=0.0,
        suggested_payload_template={
            "page": "",
            "placement": "header|hero|sticky_bar|footer",
            "phone_number": "",
            "click_to_call": True,
        },
        archetype_tags=["local_service"],
        tags=["phone", "conversion", "website", "quick_win"],
    ),
    ActionMapping(
        finding_category="conversion_path",
        action_type="website_update",
        channel="website",
        title_template="Simplify lead capture form on {page}",
        description_template=(
            "Reduce the lead capture form on {page} to the minimum fields needed "
            "for qualification.  Every additional form field decreases conversion "
            "rate by approximately 10%."
        ),
        default_priority_score=65.0,
        default_risk_tier="medium",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "page": "",
            "current_fields": [],
            "recommended_fields": [],
            "fields_to_remove": [],
        },
        archetype_tags=["local_service", "professional_service"],
        tags=["form", "conversion", "website"],
    ),

    # ------------------------------------------------------------------
    # Trust and Proof (category: trust_and_proof) -- 5 mappings
    # ------------------------------------------------------------------
    ActionMapping(
        finding_category="trust_and_proof",
        action_type="website_update",
        channel="website",
        title_template="Add testimonials to {page}",
        description_template=(
            "Collect and display customer testimonials on {page}.  Use real names, "
            "specific results, and photos when possible to maximize credibility."
        ),
        default_priority_score=60.0,
        default_risk_tier="low",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "page": "",
            "testimonials": [],
            "display_format": "cards|carousel|grid",
        },
        archetype_tags=["local_service", "professional_service"],
        tags=["testimonials", "trust", "website"],
    ),
    ActionMapping(
        finding_category="trust_and_proof",
        action_type="content_creation",
        channel="website",
        title_template="Create case study: {topic}",
        description_template=(
            "Write a detailed case study about {topic} following the Problem-Solution-"
            "Results structure.  Include specific metrics, timeline, and direct "
            "customer quotes."
        ),
        default_priority_score=55.0,
        default_risk_tier="low",
        default_effort_hours=4.0,
        default_cost=0.0,
        suggested_payload_template={
            "topic": "",
            "client_name": "",
            "problem": "",
            "solution": "",
            "results": "",
            "format": "blog_post|landing_page",
        },
        archetype_tags=["professional_service", "saas"],
        tags=["case_study", "trust", "content"],
    ),
    ActionMapping(
        finding_category="trust_and_proof",
        action_type="website_update",
        channel="website",
        title_template="Add credentials and certifications section",
        description_template=(
            "Create a dedicated credentials section displaying licenses, "
            "certifications, awards, and industry affiliations.  Position on "
            "homepage and about page for maximum visibility."
        ),
        default_priority_score=55.0,
        default_risk_tier="low",
        default_effort_hours=0.5,
        default_cost=0.0,
        suggested_payload_template={
            "certifications": [],
            "licenses": [],
            "awards": [],
            "placement": "homepage|about|footer",
        },
        archetype_tags=["professional_service", "local_service"],
        tags=["credentials", "trust", "website", "quick_win"],
    ),
    ActionMapping(
        finding_category="trust_and_proof",
        action_type="social_post",
        channel="social",
        title_template="Create social proof post: {topic}",
        description_template=(
            "Turn an existing customer testimonial or result into a social media "
            "post optimized for {topic}.  Use a testimonial graphic, before/after, "
            "or results highlight format."
        ),
        default_priority_score=50.0,
        default_risk_tier="low",
        default_effort_hours=0.5,
        default_cost=0.0,
        suggested_payload_template={
            "platform": "",
            "content_type": "testimonial_graphic|before_after|results_highlight",
            "source_testimonial": "",
        },
        archetype_tags=["local_service"],
        tags=["social_proof", "trust", "social", "quick_win"],
    ),
    ActionMapping(
        finding_category="trust_and_proof",
        action_type="website_update",
        channel="website",
        title_template="Add satisfaction guarantee to {page}",
        description_template=(
            "Add a visible satisfaction guarantee on {page} to reduce perceived "
            "risk.  Choose from money-back, satisfaction, or warranty format "
            "depending on service type."
        ),
        default_priority_score=55.0,
        default_risk_tier="low",
        default_effort_hours=0.5,
        default_cost=0.0,
        suggested_payload_template={
            "page": "",
            "guarantee_type": "money_back|satisfaction|warranty",
            "guarantee_text": "",
        },
        archetype_tags=["local_service", "ecommerce"],
        tags=["guarantee", "trust", "website", "quick_win"],
    ),

    # ------------------------------------------------------------------
    # Local SEO (category: local_seo) -- 5 mappings
    # ------------------------------------------------------------------
    ActionMapping(
        finding_category="local_seo",
        action_type="seo_fix",
        channel="website",
        title_template="Add LocalBusiness schema markup",
        description_template=(
            "Implement structured data markup using the LocalBusiness schema type "
            "on key pages.  This helps search engines understand the business "
            "entity, location, and services offered."
        ),
        default_priority_score=65.0,
        default_risk_tier="low",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "schema_type": "LocalBusiness|Service|FAQ|Review",
            "page": "",
            "schema_data": {},
        },
        archetype_tags=["local_service"],
        tags=["schema", "seo", "local", "technical"],
    ),
    ActionMapping(
        finding_category="local_seo",
        action_type="content_creation",
        channel="website",
        title_template="Create service area page: {area}",
        description_template=(
            "Build a dedicated service area page for {area} with locally relevant "
            "content, service descriptions, and LocalBusiness schema markup to "
            "capture geo-specific search traffic."
        ),
        default_priority_score=60.0,
        default_risk_tier="medium",
        default_effort_hours=3.0,
        default_cost=0.0,
        suggested_payload_template={
            "area": "",
            "services": [],
            "local_content": "",
            "schema_type": "Service",
        },
        archetype_tags=["local_service"],
        tags=["service_area", "seo", "local", "content"],
    ),
    ActionMapping(
        finding_category="local_seo",
        action_type="gbp_update",
        channel="gbp",
        title_template="Optimize Google Business Profile",
        description_template=(
            "Complete and optimize the Google Business Profile with accurate "
            "categories, updated photos, service descriptions, and regular posts.  "
            "A fully optimized GBP is the single highest-impact action for local "
            "search visibility."
        ),
        default_priority_score=80.0,
        default_risk_tier="low",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "updates": [],
            "categories_to_add": [],
            "photos_needed": [],
            "posts_to_create": [],
        },
        archetype_tags=["local_service"],
        tags=["gbp", "seo", "local", "quick_win"],
    ),
    ActionMapping(
        finding_category="local_seo",
        action_type="content_creation",
        channel="website",
        title_template="Create dedicated service page: {service}",
        description_template=(
            "Build a dedicated service page for {service} with detailed descriptions, "
            "process overview, pricing guidance, FAQ section, testimonials, and a "
            "strong CTA.  Target the primary keyword for this service."
        ),
        default_priority_score=60.0,
        default_risk_tier="medium",
        default_effort_hours=3.0,
        default_cost=0.0,
        suggested_payload_template={
            "service": "",
            "target_keyword": "",
            "sections": [
                "description",
                "process",
                "pricing",
                "faq",
                "testimonials",
                "cta",
            ],
        },
        archetype_tags=["local_service", "professional_service"],
        tags=["service_page", "seo", "content"],
    ),
    ActionMapping(
        finding_category="local_seo",
        action_type="seo_fix",
        channel="website",
        title_template="Fix NAP consistency across web presence",
        description_template=(
            "Audit and correct Name, Address, Phone (NAP) consistency across the "
            "website, Google Business Profile, and all citation sources.  NAP "
            "inconsistency is a top local ranking penalty."
        ),
        default_priority_score=70.0,
        default_risk_tier="low",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "correct_name": "",
            "correct_address": "",
            "correct_phone": "",
            "citations_to_update": [],
        },
        archetype_tags=["local_service"],
        tags=["nap", "seo", "local", "citations"],
    ),

    # ------------------------------------------------------------------
    # Reviews and Reputation (category: reviews_reputation) -- 4 mappings
    # ------------------------------------------------------------------
    ActionMapping(
        finding_category="reviews_reputation",
        action_type="review_request",
        channel="email",
        title_template="Launch automated review request sequence",
        description_template=(
            "Set up an automated email/SMS sequence that requests reviews after "
            "service completion.  Target Google and Yelp as primary platforms.  "
            "Include a 24-hour delay to allow the customer to experience results."
        ),
        default_priority_score=65.0,
        default_risk_tier="medium",
        default_effort_hours=2.0,
        default_cost=0.0,
        suggested_payload_template={
            "sequence_type": "post_service|post_purchase|periodic",
            "platform_targets": ["google", "yelp"],
            "template": "",
            "delay_hours": 24,
        },
        archetype_tags=["local_service"],
        tags=["reviews", "reputation", "email", "automation"],
    ),
    ActionMapping(
        finding_category="reviews_reputation",
        action_type="reputation_action",
        channel="gbp",
        title_template="Respond to {count} pending reviews",
        description_template=(
            "Write and post responses to all pending Google reviews.  Respond to "
            "positive reviews with gratitude and specificity.  Respond to negative "
            "reviews with empathy, accountability, and a resolution offer."
        ),
        default_priority_score=70.0,
        default_risk_tier="low",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "reviews": [],
            "response_templates": {
                "positive": "",
                "negative": "",
                "neutral": "",
            },
        },
        archetype_tags=["local_service"],
        tags=["reviews", "reputation", "gbp", "quick_win"],
    ),
    ActionMapping(
        finding_category="reviews_reputation",
        action_type="content_creation",
        channel="website",
        title_template="Create review collection landing page",
        description_template=(
            "Build a simple landing page at /review that directs satisfied customers "
            "to leave reviews on the most impactful platforms.  Include direct links "
            "to Google and Yelp review forms."
        ),
        default_priority_score=55.0,
        default_risk_tier="low",
        default_effort_hours=2.0,
        default_cost=0.0,
        suggested_payload_template={
            "review_platforms": [],
            "page_url": "/review",
            "incentive": "",
        },
        archetype_tags=["local_service"],
        tags=["reviews", "reputation", "content", "landing_page"],
    ),
    ActionMapping(
        finding_category="reviews_reputation",
        action_type="analytics_fix",
        channel="analytics",
        title_template="Set up review monitoring alerts",
        description_template=(
            "Configure automated alerts for new reviews across all platforms.  Set "
            "alert threshold to flag any review at 3 stars or below for immediate "
            "operator response."
        ),
        default_priority_score=50.0,
        default_risk_tier="auto",
        default_effort_hours=0.5,
        default_cost=0.0,
        suggested_payload_template={
            "platforms": [],
            "alert_threshold": 3,
            "notification_channels": ["email"],
        },
        archetype_tags=["local_service"],
        tags=["reviews", "reputation", "analytics", "monitoring", "quick_win"],
    ),

    # ------------------------------------------------------------------
    # Lifecycle and Follow-Up (category: follow_up_gaps) -- 4 mappings
    # ------------------------------------------------------------------
    ActionMapping(
        finding_category="follow_up_gaps",
        action_type="email_sequence",
        channel="email",
        title_template="Create welcome email sequence",
        description_template=(
            "Build a 3-email welcome sequence triggered by form submission.  "
            "Email 1 (immediate): welcome and value delivery.  Email 2 (48h): "
            "educational content.  Email 3 (120h): introductory offer."
        ),
        default_priority_score=65.0,
        default_risk_tier="medium",
        default_effort_hours=3.0,
        default_cost=0.0,
        suggested_payload_template={
            "emails": [
                {"type": "welcome", "delay_hours": 0},
                {"type": "value", "delay_hours": 48},
                {"type": "offer", "delay_hours": 120},
            ],
            "trigger": "form_submission",
        },
        archetype_tags=["local_service", "saas", "ecommerce"],
        tags=["email", "lifecycle", "welcome", "automation"],
    ),
    ActionMapping(
        finding_category="follow_up_gaps",
        action_type="email_sequence",
        channel="email",
        title_template="Create post-service review request sequence",
        description_template=(
            "Build a 2-email sequence triggered after job completion.  Email 1 "
            "(2h): thank you and satisfaction check.  Email 2 (72h): review "
            "request with direct link to Google review form."
        ),
        default_priority_score=60.0,
        default_risk_tier="medium",
        default_effort_hours=2.0,
        default_cost=0.0,
        suggested_payload_template={
            "emails": [
                {"type": "thank_you", "delay_hours": 2},
                {"type": "review_ask", "delay_hours": 72},
            ],
            "trigger": "job_completed",
        },
        archetype_tags=["local_service"],
        tags=["email", "lifecycle", "reviews", "automation"],
    ),
    ActionMapping(
        finding_category="follow_up_gaps",
        action_type="email_sequence",
        channel="email",
        title_template="Create dormant customer reactivation sequence",
        description_template=(
            "Build a 3-email reactivation sequence for customers with no activity "
            "in 90+ days.  Email 1: friendly check-in.  Email 2 (7 days): "
            "seasonal/special offer.  Email 3 (14 days): final outreach with urgency."
        ),
        default_priority_score=55.0,
        default_risk_tier="medium",
        default_effort_hours=3.0,
        default_cost=0.0,
        suggested_payload_template={
            "emails": [
                {"type": "check_in", "delay_hours": 0},
                {"type": "offer", "delay_hours": 168},
                {"type": "final", "delay_hours": 336},
            ],
            "trigger": "no_activity_90_days",
        },
        archetype_tags=["local_service", "ecommerce"],
        tags=["email", "lifecycle", "reactivation", "retention"],
    ),
    ActionMapping(
        finding_category="follow_up_gaps",
        action_type="follow_up_sequence",
        channel="email",
        title_template="Create quote follow-up sequence",
        description_template=(
            "Build a 3-email follow-up sequence triggered when a quote is sent.  "
            "Email 1 (immediate): quote received confirmation.  Email 2 (48h): "
            "follow-up with FAQ.  Email 3 (7 days): urgency nudge."
        ),
        default_priority_score=70.0,
        default_risk_tier="low",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "emails": [
                {"type": "quote_received", "delay_hours": 0},
                {"type": "follow_up", "delay_hours": 48},
                {"type": "urgency", "delay_hours": 168},
            ],
            "trigger": "quote_sent",
        },
        archetype_tags=["local_service", "professional_service"],
        tags=["email", "follow_up", "quotes", "sales"],
    ),

    # ------------------------------------------------------------------
    # Speed-to-Lead (category: speed_to_lead) -- 4 mappings
    # ------------------------------------------------------------------
    ActionMapping(
        finding_category="speed_to_lead",
        action_type="kaicalls_setup",
        channel="phone",
        title_template="Set up KaiCalls AI receptionist for {business_name}",
        description_template=(
            "Deploy KaiCalls AI receptionist (kaicalls.com) to handle missed calls, "
            "after-hours answering, lead qualification, and appointment booking.  "
            "Businesses that respond to leads within 5 minutes are 21x more likely "
            "to convert."
        ),
        default_priority_score=85.0,
        default_risk_tier="medium",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "provider": "kaicalls",
            "features": [
                "missed_call_handling",
                "after_hours_answering",
                "lead_qualification",
                "appointment_booking",
            ],
            "kaicalls_url": "https://kaicalls.com",
            "setup_type": "full|after_hours_only",
        },
        archetype_tags=["local_service", "professional_service"],
        tags=["kaicalls", "phone", "speed_to_lead", "ai_receptionist"],
    ),
    ActionMapping(
        finding_category="speed_to_lead",
        action_type="website_update",
        channel="website",
        title_template="Add click-to-call buttons across site",
        description_template=(
            "Add prominent click-to-call buttons on homepage, contact page, and "
            "all service pages.  Place in header for desktop and as a sticky mobile "
            "bar for mobile users."
        ),
        default_priority_score=70.0,
        default_risk_tier="low",
        default_effort_hours=0.5,
        default_cost=0.0,
        suggested_payload_template={
            "pages": ["homepage", "contact", "service_pages"],
            "placement": "header|hero|sticky_mobile",
        },
        archetype_tags=["local_service"],
        tags=["click_to_call", "phone", "website", "quick_win"],
    ),
    ActionMapping(
        finding_category="speed_to_lead",
        action_type="analytics_fix",
        channel="analytics",
        title_template="Set up call tracking with attribution",
        description_template=(
            "Implement call tracking with source attribution so every phone call "
            "can be traced back to the marketing channel that generated it.  "
            "Essential for measuring ROI on marketing spend."
        ),
        default_priority_score=60.0,
        default_risk_tier="auto",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "provider": "",
            "tracking_numbers": [],
            "attribution_source": "website|gbp|ads",
        },
        archetype_tags=["local_service"],
        tags=["call_tracking", "analytics", "attribution"],
    ),
    ActionMapping(
        finding_category="speed_to_lead",
        action_type="content_creation",
        channel="offline",
        title_template="Create speed-to-lead response SOP",
        description_template=(
            "Document a standard operating procedure for lead response across all "
            "channels.  Target: respond to every new lead within 5 minutes during "
            "business hours.  Include escalation rules for missed leads."
        ),
        default_priority_score=55.0,
        default_risk_tier="auto",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "max_response_minutes": 5,
            "channels": ["phone", "form", "chat"],
            "escalation_rules": [],
        },
        archetype_tags=["local_service"],
        tags=["sop", "speed_to_lead", "process"],
    ),

    # ------------------------------------------------------------------
    # Creative / Channel Presence (category: channel_presence) -- 3 mappings
    # ------------------------------------------------------------------
    ActionMapping(
        finding_category="channel_presence",
        action_type="content_creation",
        channel="offline",
        title_template="Schedule professional photo shoot",
        description_template=(
            "Schedule a professional photo session to produce high-quality imagery "
            "for website, social media, and advertising.  Include team photos, "
            "workspace/job-site shots, and before/after documentation."
        ),
        default_priority_score=50.0,
        default_risk_tier="auto",
        default_effort_hours=2.0,
        default_cost=0.0,
        suggested_payload_template={
            "shot_list": [],
            "purpose": "website|social|ads",
            "style": "professional|lifestyle|before_after",
        },
        archetype_tags=["local_service"],
        tags=["photography", "creative", "assets"],
    ),
    ActionMapping(
        finding_category="channel_presence",
        action_type="content_creation",
        channel="social",
        title_template="Create testimonial graphics from existing reviews",
        description_template=(
            "Turn the best existing customer reviews into branded social media "
            "graphics sized for Instagram (1080x1080) and Facebook (1200x630).  "
            "Use consistent brand colors and typography."
        ),
        default_priority_score=50.0,
        default_risk_tier="low",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "testimonials": [],
            "dimensions": {
                "instagram": "1080x1080",
                "facebook": "1200x630",
            },
            "brand_overlay": True,
        },
        archetype_tags=["local_service"],
        tags=["testimonial_graphic", "creative", "social"],
    ),
    ActionMapping(
        finding_category="channel_presence",
        action_type="content_creation",
        channel="social",
        title_template="Create before/after showcase content",
        description_template=(
            "Produce before/after showcase content from completed projects.  Use "
            "side-by-side, slider, or carousel format optimized for Instagram and "
            "Facebook engagement."
        ),
        default_priority_score=50.0,
        default_risk_tier="low",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "format": "side_by_side|slider|carousel",
            "projects": [],
            "platforms": ["instagram", "facebook"],
        },
        archetype_tags=["local_service"],
        tags=["before_after", "creative", "social"],
    ),

    # ------------------------------------------------------------------
    # Paid Media Readiness (category: paid_media_readiness) -- 3 mappings
    # ------------------------------------------------------------------
    ActionMapping(
        finding_category="paid_media_readiness",
        action_type="ad_campaign",
        channel="paid_media",
        title_template="Create Google Search campaign: {campaign_theme}",
        description_template=(
            "Launch a Google Search campaign targeting high-intent keywords for "
            "{campaign_theme}.  Structure with tightly themed ad groups, compelling "
            "ad copy, and a dedicated landing page for each group."
        ),
        default_priority_score=60.0,
        default_risk_tier="high",
        default_effort_hours=4.0,
        default_cost=500.0,
        suggested_payload_template={
            "platform": "google",
            "campaign_type": "search",
            "keywords": [],
            "ad_groups": [],
            "budget_daily": 0,
            "landing_page": "",
        },
        archetype_tags=["local_service", "professional_service"],
        tags=["google_ads", "paid_media", "search", "campaign"],
    ),
    ActionMapping(
        finding_category="paid_media_readiness",
        action_type="ad_campaign",
        channel="paid_media",
        title_template="Create Google Local Services campaign",
        description_template=(
            "Set up a Google Local Services Ads campaign to appear in the top "
            "local results with a Google Guaranteed badge.  LSA leads are among "
            "the highest-converting paid channels for local service businesses."
        ),
        default_priority_score=65.0,
        default_risk_tier="high",
        default_effort_hours=3.0,
        default_cost=300.0,
        suggested_payload_template={
            "platform": "google_lsa",
            "services": [],
            "service_areas": [],
            "budget_weekly": 0,
        },
        archetype_tags=["local_service"],
        tags=["google_lsa", "paid_media", "local", "campaign"],
    ),
    ActionMapping(
        finding_category="paid_media_readiness",
        action_type="ad_campaign",
        channel="paid_media",
        title_template="Create retargeting campaign: {platform}",
        description_template=(
            "Launch a retargeting campaign on {platform} to re-engage website "
            "visitors who did not convert.  Use audience segmentation based on "
            "pages visited and time on site."
        ),
        default_priority_score=55.0,
        default_risk_tier="medium",
        default_effort_hours=3.0,
        default_cost=200.0,
        suggested_payload_template={
            "platform": "",
            "audience_source": "website_visitors|email_list|video_viewers",
            "ad_formats": [],
            "budget_daily": 0,
        },
        archetype_tags=["local_service", "ecommerce"],
        tags=["retargeting", "paid_media", "campaign"],
    ),

    # ------------------------------------------------------------------
    # CRM and Data Hygiene (category: crm_data_hygiene) -- 3 mappings
    # ------------------------------------------------------------------
    ActionMapping(
        finding_category="crm_data_hygiene",
        action_type="analytics_fix",
        channel="email",
        title_template="Clean and segment contact list",
        description_template=(
            "Audit the contact database: remove bounced addresses, purge "
            "unsubscribes, tag inactive contacts (no engagement in 90+ days), "
            "and segment by acquisition source for targeted messaging."
        ),
        default_priority_score=55.0,
        default_risk_tier="auto",
        default_effort_hours=2.0,
        default_cost=0.0,
        suggested_payload_template={
            "list_size": 0,
            "actions": [
                "remove_bounces",
                "remove_unsubscribes",
                "tag_inactive",
                "segment_by_source",
            ],
        },
        archetype_tags=["local_service", "saas"],
        tags=["crm", "email", "data_hygiene", "contacts"],
    ),
    ActionMapping(
        finding_category="crm_data_hygiene",
        action_type="analytics_fix",
        channel="email",
        title_template="Create contact segments for targeted messaging",
        description_template=(
            "Define and build contact segments based on customer lifecycle stage, "
            "service type, geographic area, and engagement level.  Segmented "
            "campaigns produce 760% more revenue than broadcast emails."
        ),
        default_priority_score=50.0,
        default_risk_tier="auto",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "segments": [{"name": "", "criteria": {}}],
        },
        archetype_tags=["local_service", "saas"],
        tags=["crm", "email", "segmentation"],
    ),
    ActionMapping(
        finding_category="crm_data_hygiene",
        action_type="analytics_fix",
        channel="analytics",
        title_template="Fix {tracking_type} tracking",
        description_template=(
            "Diagnose and fix {tracking_type} tracking issues to ensure accurate "
            "marketing attribution.  Verify tag firing, conversion events, and "
            "data flow into reporting dashboards."
        ),
        default_priority_score=65.0,
        default_risk_tier="auto",
        default_effort_hours=1.0,
        default_cost=0.0,
        suggested_payload_template={
            "tracking_type": "ga4|gtm|pixel|conversion",
            "issues": [],
            "fixes": [],
        },
        archetype_tags=["local_service", "ecommerce", "saas"],
        tags=["tracking", "analytics", "data_hygiene"],
    ),
]


# Keywords that trigger a KaiCalls recommendation regardless of category
_KAICALLS_TRIGGER_KEYWORDS = re.compile(
    r"missed\s+calls?|after\s+hours?|phone|response\s+time|"
    r"call\s+handling|unreachable|voicemail|no\s+answer",
    re.IGNORECASE,
)


# ============================================================================
# Public functions
# ============================================================================


def get_mappings_for_category(category: str) -> List[ActionMapping]:
    """Return all mappings whose ``finding_category`` matches *category*.

    Parameters
    ----------
    category:
        The audit category string (e.g., ``"conversion_path"``).

    Returns
    -------
    list[ActionMapping]
        Matching mappings, possibly empty.
    """
    return [m for m in MAPPING_REGISTRY if m.finding_category == category]


def fill_template(template: str, context: Dict[str, Any]) -> str:
    """Replace ``{key}`` placeholders in *template* with values from *context*.

    Placeholders whose key is not present in *context* are left as-is
    (e.g., ``"{page}"`` stays ``"{page}"`` if ``"page"`` is not in the
    context dict).

    Parameters
    ----------
    template:
        A string containing zero or more ``{key}`` placeholders.
    context:
        A dict of replacement values.

    Returns
    -------
    str
        The template with available placeholders filled.
    """
    result = template
    for key, value in context.items():
        placeholder = "{" + str(key) + "}"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    return result


def map_finding_to_actions(
    finding: Dict[str, Any],
    business_profile: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Convert an audit finding into a list of proposed actions.

    This is the main entry point of the mapping engine.  It looks up the
    finding's category in ``MAPPING_REGISTRY``, generates a
    ``ProposedAction`` dict for each matching mapping, fills template
    strings with available data, and computes risk tiers and priority
    scores.

    **KaiCalls rule:** If the finding category is ``speed_to_lead`` or
    the finding summary/title mentions missed calls, after hours, phone,
    or response time, a KaiCalls setup action is always included.

    Parameters
    ----------
    finding:
        An ``AuditFinding``-compatible dict with at minimum ``id``,
        ``category``, ``severity``, ``priority``, ``title``, and
        ``description`` keys.
    business_profile:
        Optional business profile dict for template filling.  Can
        contain ``business_name``, ``services``, ``service_areas``, etc.

    Returns
    -------
    list[dict]
        A list of ``ProposedAction``-compatible dicts.
    """
    if business_profile is None:
        business_profile = {}

    category = finding.get("category", "")
    finding_id = finding.get("id", "")
    severity = finding.get("severity", "medium")
    finding_priority = finding.get("priority", "P2")
    finding_title = finding.get("title", "")
    finding_description = finding.get("description", "")
    finding_tags = finding.get("tags", [])
    archetype_relevance = finding.get("archetype_relevance", [])

    # Build a template context from finding + business profile data
    template_context: Dict[str, Any] = {
        "finding_title": finding_title,
        "business_name": business_profile.get("business_name", "{business_name}"),
        "page": "{page}",
        "topic": finding_title,
        "area": "{area}",
        "service": "{service}",
        "platform": "{platform}",
        "campaign_theme": "{campaign_theme}",
        "count": "{count}",
        "tracking_type": "{tracking_type}",
    }

    # Extract additional context from finding metadata
    metadata = finding.get("metadata", {})
    for key in ("page", "area", "service", "platform", "campaign_theme",
                "count", "tracking_type", "topic"):
        if key in metadata:
            template_context[key] = metadata[key]

    # Extract from business profile
    if "identity" in business_profile:
        identity = business_profile["identity"]
        if "business_name" in identity:
            template_context["business_name"] = identity["business_name"]
    if "business_name" in business_profile:
        template_context["business_name"] = business_profile["business_name"]

    # Get matching mappings for this category
    mappings = get_mappings_for_category(category)

    # Filter by pattern if the mapping has one
    filtered_mappings: List[ActionMapping] = []
    for mapping in mappings:
        if mapping.finding_pattern:
            combined_text = f"{finding_title} {finding_description}"
            if re.search(mapping.finding_pattern, combined_text, re.IGNORECASE):
                filtered_mappings.append(mapping)
        else:
            filtered_mappings.append(mapping)

    # KaiCalls rule: check if we need to force-include KaiCalls
    kaicalls_needed = category == "speed_to_lead"
    if not kaicalls_needed:
        combined_text = f"{finding_title} {finding_description}"
        if _KAICALLS_TRIGGER_KEYWORDS.search(combined_text):
            kaicalls_needed = True

    # If KaiCalls is needed, ensure the kaicalls_setup mapping is present
    kaicalls_mapping_present = any(
        m.action_type == "kaicalls_setup" for m in filtered_mappings
    )
    if kaicalls_needed and not kaicalls_mapping_present:
        # Pull the KaiCalls mapping from the registry
        kaicalls_mappings = [
            m for m in MAPPING_REGISTRY if m.action_type == "kaicalls_setup"
        ]
        if kaicalls_mappings:
            filtered_mappings.append(kaicalls_mappings[0])

    # Check whether the finding's archetype list overlaps with any mapping
    def _archetype_match(mapping: ActionMapping) -> bool:
        if not archetype_relevance or not mapping.archetype_tags:
            return False
        return bool(set(archetype_relevance) & set(mapping.archetype_tags))

    # Generate ProposedAction dicts
    actions: List[Dict[str, Any]] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for mapping in filtered_mappings:
        action_id = generate_action_id()

        # Fill title and description templates
        title = fill_template(mapping.title_template, template_context)
        description = fill_template(mapping.description_template, template_context)

        # Determine if this action is public-facing
        is_public_facing = mapping.channel in ("website", "social", "gbp", "paid_media")

        # Compute risk tier
        risk_tier = assign_risk_tier(
            action_type=mapping.action_type,
            estimated_cost=mapping.default_cost,
            channel=mapping.channel,
            is_public_facing=is_public_facing,
        )

        # Compute priority score
        archetype_match = _archetype_match(mapping)
        priority_score = compute_priority_score(
            severity=severity,
            finding_priority=finding_priority,
            estimated_effort_hours=mapping.default_effort_hours,
            estimated_cost=mapping.default_cost,
            archetype_match=archetype_match,
        )

        # Build effort string
        if mapping.default_effort_hours < 1:
            effort_str = f"{int(mapping.default_effort_hours * 60)} minutes"
        else:
            effort_str = (
                f"{int(mapping.default_effort_hours)} hour"
                + ("s" if mapping.default_effort_hours != 1 else "")
            )

        # Build suggested payload by filling template values
        suggested_payload = _fill_payload_template(
            mapping.suggested_payload_template,
            template_context,
        )

        # Merge tags from finding and mapping
        combined_tags = list(set(mapping.tags + finding_tags))

        action_dict: Dict[str, Any] = {
            "id": action_id,
            "source_finding_id": finding_id,
            "action_type": mapping.action_type,
            "channel": mapping.channel,
            "title": title,
            "description": description,
            "reason": (
                f"Identified during audit: {finding_title}"
            ),
            "business_impact": "",
            "expected_outcome": "",
            "risk_tier": risk_tier,
            "approval_requirement": "operator_review",
            "suggested_payload": suggested_payload,
            "estimated_effort": effort_str,
            "estimated_effort_hours": mapping.default_effort_hours,
            "estimated_cost": mapping.default_cost,
            "priority_score": priority_score,
            "archetype_relevance": mapping.archetype_tags,
            "tags": combined_tags,
            "depends_on": [],
            "status": "proposed",
            "created_at": now_iso,
            "metadata": {
                "mapping_action_type": mapping.action_type,
                "finding_category": category,
                "finding_severity": severity,
            },
        }

        actions.append(action_dict)

    return actions


# ============================================================================
# Internal helpers
# ============================================================================


def _fill_payload_template(
    template: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Recursively fill string values in a payload template dict.

    Non-string values (lists, dicts, bools, numbers) are preserved as-is.
    String values containing ``{key}`` placeholders are filled from
    *context* where possible.

    Parameters
    ----------
    template:
        The payload template dict from an ``ActionMapping``.
    context:
        The template context for placeholder replacement.

    Returns
    -------
    dict
        A new dict with string placeholders filled.
    """
    result: Dict[str, Any] = {}
    for key, value in template.items():
        if isinstance(value, str):
            result[key] = fill_template(value, context)
        elif isinstance(value, dict):
            result[key] = _fill_payload_template(value, context)
        elif isinstance(value, list):
            result[key] = [
                fill_template(item, context) if isinstance(item, str) else
                _fill_payload_template(item, context) if isinstance(item, dict) else
                item
                for item in value
            ]
        else:
            result[key] = value
    return result
