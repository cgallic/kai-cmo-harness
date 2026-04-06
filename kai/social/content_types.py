"""Social content type taxonomy, per-platform format rules, and cross-product templates.

Provides the structured layer that downstream features (caption generation,
scheduling, proof-of-life monitoring) use to produce platform-compliant posts.
Every content type is mapped to every platform where it makes sense, with
specific constraints, hooks, CTA options, and caption templates.
"""

from __future__ import annotations

import copy
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import with fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:  # type: ignore[no-redef]
        """Minimal pydantic-like fallback."""

        def __init__(self, **data: Any) -> None:
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in data:
                    value = data.pop(name)
                elif hasattr(self.__class__, name):
                    value = copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self) -> Dict[str, Any]:
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self) -> str:
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel  # type: ignore[assignment,misc]
    Field = _PydanticField  # type: ignore[assignment,misc]


# ============================================================================
# Enums
# ============================================================================


_CONTENT_TYPE_DESCRIPTIONS: Dict[str, str] = {
    "proof_post": (
        "Before/after, project completion, or results showcase — "
        "best for showing work quality and building trust."
    ),
    "testimonial_post": (
        "Customer quote with photo or graphic — "
        "social proof that converts."
    ),
    "local_tip_post": (
        "Helpful advice related to service area — "
        "positions the business as the local expert."
    ),
    "offer_post": (
        "Promotional with urgency and a clear CTA — "
        "direct response content."
    ),
    "behind_the_scenes_post": (
        "Team, process, or workspace authenticity — "
        "humanizes the brand."
    ),
    "educational_post": (
        "How-to, myth-busting, or FAQ answer — "
        "value-first content that earns trust."
    ),
    "community_post": (
        "Local events, partnerships, or sponsorships — "
        "community connection content."
    ),
    "seasonal_post": (
        "Holiday, weather, or seasonal service reminders — "
        "timely relevance that keeps you top of mind."
    ),
}


class SocialContentType(str, Enum):
    """Taxonomy of social media content types for local service businesses."""

    proof_post = "proof_post"
    testimonial_post = "testimonial_post"
    local_tip_post = "local_tip_post"
    offer_post = "offer_post"
    behind_the_scenes_post = "behind_the_scenes_post"
    educational_post = "educational_post"
    community_post = "community_post"
    seasonal_post = "seasonal_post"

    @classmethod
    def get_description(cls, content_type: str) -> str:
        """Return a one-sentence description for *content_type*.

        Accepts both the enum member name and its value string.
        """
        key = content_type.value if isinstance(content_type, cls) else content_type
        return _CONTENT_TYPE_DESCRIPTIONS.get(key, "Unknown content type.")


class SocialPlatform(str, Enum):
    """Supported social media platforms."""

    instagram = "instagram"
    facebook = "facebook"
    linkedin = "linkedin"
    tiktok = "tiktok"
    x_twitter = "x_twitter"
    youtube = "youtube"


# ============================================================================
# Models
# ============================================================================


class PlatformFormatRules(BaseModel):
    """Per-platform posting constraints, best practices, and tone guidance."""

    platform: str = Field(..., description="SocialPlatform value")
    max_caption_length: int = Field(..., description="Absolute maximum caption characters")
    recommended_caption_length: int = Field(
        ..., description="Engagement sweet-spot caption length"
    )
    max_hashtags: int = Field(..., description="Platform-enforced hashtag ceiling")
    recommended_hashtags: int = Field(..., description="Optimal hashtag count for reach")
    max_media_items: int = Field(
        ..., description="Max images/videos per post (carousel limit)"
    )
    preferred_aspect_ratios: List[str] = Field(
        default_factory=list, description='e.g., ["1:1", "4:5"]'
    )
    supports_scheduling: bool = Field(False)
    supports_link_in_post: bool = Field(False)
    supports_carousel: bool = Field(False)
    supports_video: bool = Field(False)
    supports_stories: bool = Field(False)
    supports_reels_shorts: bool = Field(False)
    tone_guidance: str = Field("", description="Brief tone direction for the platform")
    best_practices: List[str] = Field(
        default_factory=list, description="3-5 key best practices"
    )
    posting_frequency_max_per_day: int = Field(1)
    posting_frequency_recommended_per_day: float = Field(1.0)


class ContentTypeTemplate(BaseModel):
    """Cross-product template mapping a content type to a platform's constraints."""

    content_type: str = Field(..., description="SocialContentType value")
    platform: str = Field(..., description="SocialPlatform value")
    structure: List[str] = Field(
        default_factory=list,
        description="Ordered list of structural elements",
    )
    required_elements: List[str] = Field(default_factory=list)
    optional_elements: List[str] = Field(default_factory=list)
    suggested_hooks: List[str] = Field(
        default_factory=list,
        description="3-5 example opening lines or hooks",
    )
    cta_options: List[str] = Field(
        default_factory=list,
        description="3-5 appropriate CTAs",
    )
    caption_template: str = Field(
        "",
        description="Fill-in-the-blank caption string with {placeholders}",
    )
    media_guidance: str = Field("", description="What media to use")
    notes: str = Field("", description="Special notes for this combination")


# ============================================================================
# PLATFORM_RULES — one entry per SocialPlatform
# ============================================================================

PLATFORM_RULES: Dict[str, PlatformFormatRules] = {
    # ------------------------------------------------------------------
    # Instagram
    # ------------------------------------------------------------------
    SocialPlatform.instagram.value: PlatformFormatRules(
        platform=SocialPlatform.instagram.value,
        max_caption_length=2200,
        recommended_caption_length=150,
        max_hashtags=30,
        recommended_hashtags=8,
        max_media_items=10,
        preferred_aspect_ratios=["1:1", "4:5", "9:16"],
        supports_scheduling=True,
        supports_link_in_post=False,
        supports_carousel=True,
        supports_video=True,
        supports_stories=True,
        supports_reels_shorts=True,
        tone_guidance=(
            "Visual-first, authentic, slightly casual. "
            "Lead with the image, support with caption."
        ),
        best_practices=[
            "First line is the hook — must stop the scroll",
            "Use line breaks for readability",
            "Put hashtags in first comment or at end",
            "Carousel posts get 3x engagement vs single image",
            "Reels reach 2x more non-followers than feed posts",
        ],
        posting_frequency_max_per_day=3,
        posting_frequency_recommended_per_day=1.0,
    ),
    # ------------------------------------------------------------------
    # Facebook
    # ------------------------------------------------------------------
    SocialPlatform.facebook.value: PlatformFormatRules(
        platform=SocialPlatform.facebook.value,
        max_caption_length=63206,
        recommended_caption_length=250,
        max_hashtags=30,
        recommended_hashtags=3,
        max_media_items=10,
        preferred_aspect_ratios=["1:1", "4:5", "16:9"],
        supports_scheduling=True,
        supports_link_in_post=True,
        supports_carousel=True,
        supports_video=True,
        supports_stories=True,
        supports_reels_shorts=True,
        tone_guidance=(
            "Conversational, community-oriented. "
            "Questions and stories perform best."
        ),
        best_practices=[
            "Native video outperforms YouTube links by 10x",
            "Posts with questions get 2x comments",
            "Share to relevant local groups for organic reach",
            "Link posts get less reach than photo/video posts",
            "Facebook prioritizes content that sparks conversation",
        ],
        posting_frequency_max_per_day=2,
        posting_frequency_recommended_per_day=1.0,
    ),
    # ------------------------------------------------------------------
    # LinkedIn
    # ------------------------------------------------------------------
    SocialPlatform.linkedin.value: PlatformFormatRules(
        platform=SocialPlatform.linkedin.value,
        max_caption_length=3000,
        recommended_caption_length=1300,
        max_hashtags=30,
        recommended_hashtags=4,
        max_media_items=9,
        preferred_aspect_ratios=["1:1", "1.91:1", "4:5"],
        supports_scheduling=True,
        supports_link_in_post=True,
        supports_carousel=True,
        supports_video=True,
        supports_stories=False,
        supports_reels_shorts=False,
        tone_guidance=(
            "Professional, thought-leadership oriented. "
            "Share expertise and industry insights."
        ),
        best_practices=[
            "Open with a hook line, then line break for 'see more' click",
            "Document carousels get 3x engagement",
            "Comment on your own post to boost reach",
            "Tag relevant people and companies",
            "Post between 7-9 AM or 12-1 PM local time",
        ],
        posting_frequency_max_per_day=2,
        posting_frequency_recommended_per_day=1.0,
    ),
    # ------------------------------------------------------------------
    # TikTok
    # ------------------------------------------------------------------
    SocialPlatform.tiktok.value: PlatformFormatRules(
        platform=SocialPlatform.tiktok.value,
        max_caption_length=2200,
        recommended_caption_length=150,
        max_hashtags=100,
        recommended_hashtags=4,
        max_media_items=35,
        preferred_aspect_ratios=["9:16"],
        supports_scheduling=True,
        supports_link_in_post=False,
        supports_carousel=True,
        supports_video=True,
        supports_stories=False,
        supports_reels_shorts=True,
        tone_guidance=(
            "Authentic, unpolished, trend-aware. "
            "Educational content in entertainment wrapper."
        ),
        best_practices=[
            "Hook in first 1-3 seconds or lose them",
            "Trending sounds boost discovery 2-3x",
            "Show don't tell — demonstrate expertise visually",
            "Reply to comments with video for engagement loop",
            "Post 1-3x daily for growth phase, 3-5x/week for maintenance",
        ],
        posting_frequency_max_per_day=3,
        posting_frequency_recommended_per_day=1.0,
    ),
    # ------------------------------------------------------------------
    # X / Twitter
    # ------------------------------------------------------------------
    SocialPlatform.x_twitter.value: PlatformFormatRules(
        platform=SocialPlatform.x_twitter.value,
        max_caption_length=280,
        recommended_caption_length=260,
        max_hashtags=10,
        recommended_hashtags=2,
        max_media_items=4,
        preferred_aspect_ratios=["16:9", "1:1"],
        supports_scheduling=True,
        supports_link_in_post=True,
        supports_carousel=False,
        supports_video=True,
        supports_stories=False,
        supports_reels_shorts=False,
        tone_guidance=(
            "Punchy, opinionated, concise. "
            "Hot takes and thread format for depth."
        ),
        best_practices=[
            "Threads get 5x engagement of single tweets",
            "Tweet without links gets more reach than with links",
            "Reply to your own tweet to add links below",
            "Post contrarian or spicy takes for engagement",
            "Quote tweets > retweets for reach",
        ],
        posting_frequency_max_per_day=5,
        posting_frequency_recommended_per_day=2.0,
    ),
    # ------------------------------------------------------------------
    # YouTube
    # ------------------------------------------------------------------
    SocialPlatform.youtube.value: PlatformFormatRules(
        platform=SocialPlatform.youtube.value,
        max_caption_length=5000,
        recommended_caption_length=200,
        max_hashtags=15,
        recommended_hashtags=4,
        max_media_items=1,
        preferred_aspect_ratios=["16:9", "9:16"],
        supports_scheduling=True,
        supports_link_in_post=True,
        supports_carousel=False,
        supports_video=True,
        supports_stories=False,
        supports_reels_shorts=True,
        tone_guidance=(
            "Educational, helpful, personality-driven. "
            "First 30 seconds determine retention."
        ),
        best_practices=[
            "Title and thumbnail are 80% of success",
            "First 30 seconds must hook — ask a question or show the payoff",
            "Include Shorts in every long-form video with #Shorts tag",
            "Chapters improve watch time and SEO",
            "End screen and cards drive subscriber growth",
        ],
        posting_frequency_max_per_day=2,
        posting_frequency_recommended_per_day=0.3,
    ),
}


# ============================================================================
# CONTENT_TYPE_TEMPLATES — cross-product of (content_type, platform)
# ============================================================================

def _tkey(content_type: str, platform: str) -> str:
    """Build the canonical lookup key for the templates dict."""
    return f"{content_type}::{platform}"


CONTENT_TYPE_TEMPLATES: Dict[str, ContentTypeTemplate] = {}

# ------------------------------------------------------------------
# 1. ProofPost (4 templates: Instagram, Facebook, LinkedIn, TikTok)
# ------------------------------------------------------------------

CONTENT_TYPE_TEMPLATES[_tkey("proof_post", "instagram")] = ContentTypeTemplate(
    content_type="proof_post",
    platform="instagram",
    structure=[
        "hook_line",
        "before_photo",
        "after_photo",
        "result_description",
        "process_summary",
        "cta",
        "hashtags",
    ],
    required_elements=["hook_line", "before_photo", "after_photo", "result_description", "cta"],
    optional_elements=["process_summary", "client_tag", "location_tag"],
    suggested_hooks=[
        "Swipe to see the difference 7 days made.",
        "This is what {service} actually looks like when it's done right.",
        "Our client couldn't believe this was the same {location}.",
        "Before you hire anyone, look at slide 3.",
        "Same space. Completely different experience.",
    ],
    cta_options=[
        "DM 'RESULTS' for a free estimate.",
        "Tap the link in bio to book your consultation.",
        "Save this for when you're ready to upgrade.",
        "Tag someone who needs this transformation.",
        "Comment your ZIP code and we'll tell you if we serve your area.",
    ],
    caption_template=(
        "{hook}\n\n"
        "This {service} project in {location} took {timeline} from start to finish.\n\n"
        "Here's what changed:\n"
        "- {result_1}\n"
        "- {result_2}\n"
        "- {result_3}\n\n"
        "{cta}\n\n"
        "{hashtags}"
    ),
    media_guidance=(
        "Before/after side-by-side carousel — first slide teases the after, "
        "slide 2 shows the before, slide 3+ shows process and detail shots. "
        "Minimum 4 slides, maximum 10. 4:5 aspect ratio for feed."
    ),
    notes="Carousel outperforms single image for proof posts by 3x on Instagram.",
)

CONTENT_TYPE_TEMPLATES[_tkey("proof_post", "facebook")] = ContentTypeTemplate(
    content_type="proof_post",
    platform="facebook",
    structure=[
        "story_hook",
        "problem_context",
        "solution_narrative",
        "result_reveal",
        "social_proof_element",
        "cta",
    ],
    required_elements=["story_hook", "result_reveal", "cta"],
    optional_elements=["problem_context", "solution_narrative", "social_proof_element"],
    suggested_hooks=[
        "The homeowner said they'd tried everything before calling us.",
        "We almost turned this job down. Here's why we're glad we didn't.",
        "See what {service} looks like when it's done by a team that actually cares.",
        "Our crew spent {timeline} on this one. Worth every hour.",
        "The neighbors started asking questions after this project wrapped.",
    ],
    cta_options=[
        "Click the link below to get a free quote for your project.",
        "Call us at {phone} — we answer 24/7 with KaiCalls.",
        "Share this with someone who's been putting off their {service}.",
        "Drop a comment and we'll send you a before/after gallery.",
        "Message us directly for a same-week estimate.",
    ],
    caption_template=(
        "{hook}\n\n"
        "This {location} homeowner had been dealing with {problem} for months. "
        "After {timeline} of work, here's the result.\n\n"
        "{result}\n\n"
        "We've completed {project_count}+ projects like this in the {location} area.\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Single side-by-side before/after image or a 30-60 second video showing "
        "the transformation. Native video performs 10x better than image on Facebook."
    ),
    notes=(
        "Facebook favors storytelling. Frame the proof post as a mini customer "
        "story, not just a photo dump."
    ),
)

CONTENT_TYPE_TEMPLATES[_tkey("proof_post", "linkedin")] = ContentTypeTemplate(
    content_type="proof_post",
    platform="linkedin",
    structure=[
        "industry_hook",
        "business_challenge",
        "approach_overview",
        "measurable_outcomes",
        "key_takeaway",
        "cta",
    ],
    required_elements=["industry_hook", "measurable_outcomes", "cta"],
    optional_elements=["business_challenge", "approach_overview", "key_takeaway"],
    suggested_hooks=[
        "Most {industry} companies overlook this. It cost our client $X/month.",
        "We tracked the numbers on this project for 90 days. Here's what happened.",
        "A case study in doing {service} the right way.",
        "The ROI on this project surprised even us.",
        "Here's proof that {service} isn't just a cost — it's an investment.",
    ],
    cta_options=[
        "Want to see similar results? Connect and DM me.",
        "Follow for more real-world {industry} case studies.",
        "Download the full case study (link in first comment).",
        "What's the biggest {service} challenge you're facing? Tell me in the comments.",
        "Tag a business owner who needs to see these numbers.",
    ],
    caption_template=(
        "{hook}\n\n"
        "The challenge:\n{business_challenge}\n\n"
        "What we did:\n{approach}\n\n"
        "The results:\n"
        "- {metric_1}\n"
        "- {metric_2}\n"
        "- {metric_3}\n\n"
        "Key insight: {takeaway}\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Professional before/after photo with metrics overlay, or a "
        "document carousel (PDF slides) walking through the case study. "
        "1:1 or 1.91:1 aspect ratio."
    ),
    notes=(
        "Frame everything through a business-outcome lens. "
        "LinkedIn proof posts should read like mini case studies, not show-off reels."
    ),
)

CONTENT_TYPE_TEMPLATES[_tkey("proof_post", "tiktok")] = ContentTypeTemplate(
    content_type="proof_post",
    platform="tiktok",
    structure=[
        "text_overlay_hook",
        "before_reveal",
        "process_timelapse",
        "after_reveal",
        "results_text",
        "cta_comment_or_bio",
    ],
    required_elements=["text_overlay_hook", "before_reveal", "after_reveal"],
    optional_elements=["process_timelapse", "results_text", "cta_comment_or_bio"],
    suggested_hooks=[
        "POV: You hired us and THIS is what happened.",
        "Watch this {service} transformation in 15 seconds.",
        "Day 1 vs. Day Done.",
        "They said it couldn't be fixed. We said hold our tools.",
        "This was the most satisfying {service} project we've done all year.",
    ],
    cta_options=[
        "Follow for more transformations like this.",
        "Comment 'HOW' and we'll explain our process.",
        "Link in bio for a free estimate in {location}.",
        "Duet this with your own before/after!",
        "Save this for when you need a {service} pro.",
    ],
    caption_template=(
        "{hook} {hashtags}\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Timelapse or speed-up transformation video, 15-30 seconds, 9:16 vertical. "
        "Use text overlays for context (before/during/after labels). "
        "Trending sound strongly recommended — boosts discovery 2-3x."
    ),
    notes="Keep caption short. The video IS the content on TikTok. All detail goes in text overlays.",
)

# ------------------------------------------------------------------
# 2. TestimonialPost (3 templates: Instagram, Facebook, LinkedIn)
# ------------------------------------------------------------------

CONTENT_TYPE_TEMPLATES[_tkey("testimonial_post", "instagram")] = ContentTypeTemplate(
    content_type="testimonial_post",
    platform="instagram",
    structure=[
        "quote_highlight",
        "customer_context",
        "result_or_outcome",
        "business_response",
        "cta",
        "hashtags",
    ],
    required_elements=["quote_highlight", "customer_context", "cta"],
    optional_elements=["result_or_outcome", "business_response", "customer_tag"],
    suggested_hooks=[
        '"I wish I\'d called them six months ago." — {customer_name}, {location}',
        "This Google review stopped us in our tracks this morning.",
        "When your client texts you this the day after a job, you know you nailed it.",
        '"Best money we\'ve spent on our home this year."',
        "We don't write our own reviews. Our clients do. Here's the latest.",
    ],
    cta_options=[
        "DM us to become our next success story.",
        "Tap the link in bio to read all our reviews.",
        "Tag someone who needs {service} they can actually trust.",
        "Save this post — you'll want it when you're ready to hire.",
        "Comment 'BOOK' and we'll send you our availability.",
    ],
    caption_template=(
        '"{customer_quote}"\n\n'
        "— {customer_name}, {location}\n\n"
        "{context}\n\n"
        "We're grateful for every client who trusts {business_name} with their {service}.\n\n"
        "{cta}\n\n"
        "{hashtags}"
    ),
    media_guidance=(
        "Quote graphic with customer photo (with permission) or branded quote card. "
        "Alternatively, short 15-second video clip of the customer speaking. "
        "4:5 for feed, 9:16 for stories. Create a story version with poll sticker."
    ),
    notes="Always get explicit permission before using customer names or photos.",
)

CONTENT_TYPE_TEMPLATES[_tkey("testimonial_post", "facebook")] = ContentTypeTemplate(
    content_type="testimonial_post",
    platform="facebook",
    structure=[
        "review_callout",
        "full_quote",
        "project_context",
        "thank_you",
        "cta_with_link",
    ],
    required_elements=["review_callout", "full_quote", "cta_with_link"],
    optional_elements=["project_context", "thank_you", "review_link"],
    suggested_hooks=[
        "Another 5-star review just came in and we had to share it.",
        "We asked {customer_name} what they thought after the job was done. This is what they said.",
        "This review reminded us exactly why we do what we do.",
        "Feedback like this makes early mornings and long days worth it.",
        "Our {review_count}th 5-star review — and every one of them means the world to us.",
    ],
    cta_options=[
        "Read all our reviews here: {review_link}",
        "Call us at {phone} — we'd love to earn your 5-star review too.",
        "Share this with someone looking for a {service} provider they can trust.",
        "Leave us a review if we've worked on your home!",
        "Message us for a free consultation.",
    ],
    caption_template=(
        "{hook}\n\n"
        '"{customer_quote}"\n\n'
        "— {customer_name}\n\n"
        "{project_context}\n\n"
        "Thank you, {customer_name}. We appreciate you trusting {business_name}.\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Customer photo at the completed project site, or a branded quote graphic. "
        "Link to the full review page (Google, Yelp, or Facebook). "
        "16:9 or 1:1 aspect ratio."
    ),
    notes="Facebook allows links in post body — link directly to the review page for credibility.",
)

CONTENT_TYPE_TEMPLATES[_tkey("testimonial_post", "linkedin")] = ContentTypeTemplate(
    content_type="testimonial_post",
    platform="linkedin",
    structure=[
        "professional_framing",
        "client_endorsement",
        "business_outcome",
        "lesson_or_takeaway",
        "cta",
    ],
    required_elements=["professional_framing", "client_endorsement", "cta"],
    optional_elements=["business_outcome", "lesson_or_takeaway"],
    suggested_hooks=[
        "A client sent this unsolicited after we wrapped a 6-month engagement.",
        "The best business development? Letting your clients speak for you.",
        "We don't pitch. We let results talk. Here's what our latest client said.",
        "This client feedback is the reason we invested in {process_or_approach}.",
        "When a client renews before their contract is up, you know you delivered.",
    ],
    cta_options=[
        "Want to see similar results for your business? Let's connect.",
        "Follow for more real client stories from the {industry} space.",
        "Download our client results overview (link in first comment).",
        "What's the best compliment a client has given your team? Drop it below.",
        "DM me if you want to discuss how we can help your team.",
    ],
    caption_template=(
        "{hook}\n\n"
        '"{client_quote}"\n'
        "— {client_name}, {client_title} at {client_company}\n\n"
        "The background:\n{business_outcome}\n\n"
        "What we learned: {takeaway}\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Professional headshot of the client (with permission), or a clean quote card "
        "with company logo. Document carousel with case study summary is ideal. "
        "1:1 or 4:5 aspect ratio."
    ),
    notes="Frame as a professional endorsement or mini case study. Avoid sounding like a sales pitch.",
)

# ------------------------------------------------------------------
# 3. LocalTipPost (4 templates: Instagram, Facebook, TikTok, YouTube)
# ------------------------------------------------------------------

CONTENT_TYPE_TEMPLATES[_tkey("local_tip_post", "instagram")] = ContentTypeTemplate(
    content_type="local_tip_post",
    platform="instagram",
    structure=[
        "hook_question_or_statement",
        "numbered_tips",
        "expert_context",
        "save_cta",
        "hashtags",
    ],
    required_elements=["hook_question_or_statement", "numbered_tips", "save_cta"],
    optional_elements=["expert_context", "bonus_tip"],
    suggested_hooks=[
        "3 signs your {equipment} is about to fail (most people ignore #2).",
        "Stop doing this to your {asset} — it's costing you hundreds.",
        "{location} homeowners: here's what your {service_provider} won't tell you.",
        "Save this before your next {service} appointment.",
        "The #1 mistake {location} residents make with their {system}.",
    ],
    cta_options=[
        "Save this post — you'll need it.",
        "Share with a neighbor who needs to see this.",
        "Follow @{handle} for weekly {industry} tips.",
        "DM 'CHECKLIST' for our free {topic} guide.",
        "Comment with your biggest {topic} question and we'll answer it.",
    ],
    caption_template=(
        "{hook}\n\n"
        "1. {tip_1}\n"
        "2. {tip_2}\n"
        "3. {tip_3}\n\n"
        "Pro tip from {business_name}: {expert_insight}\n\n"
        "{cta}\n\n"
        "{hashtags}"
    ),
    media_guidance=(
        "Carousel with one tip per slide — use bold text overlays on brand-colored backgrounds. "
        "First slide is the hook, last slide is the CTA. "
        "Minimum 5 slides, 1:1 or 4:5 aspect ratio. Carousel tips posts are the #1 save-worthy format."
    ),
    notes="Tip posts drive saves, which is Instagram's strongest algorithm signal in 2026.",
)

CONTENT_TYPE_TEMPLATES[_tkey("local_tip_post", "facebook")] = ContentTypeTemplate(
    content_type="local_tip_post",
    platform="facebook",
    structure=[
        "question_hook",
        "relatable_scenario",
        "detailed_tip",
        "why_it_matters",
        "conversation_starter",
    ],
    required_elements=["question_hook", "detailed_tip", "conversation_starter"],
    optional_elements=["relatable_scenario", "why_it_matters"],
    suggested_hooks=[
        "Quick question for {location} homeowners: when was the last time you checked your {system}?",
        "Raise your hand if you've ever made this {service} mistake.",
        "We get asked this question at least 3 times a week.",
        "Here's something most people don't know about {topic} in {location}.",
        "Before you spend $500 on {service}, try this first.",
    ],
    cta_options=[
        "What's your biggest {topic} frustration? Tell us in the comments.",
        "Share this with someone who could use this tip.",
        "Call {phone} if you need help — we answer every call with KaiCalls.",
        "Has this happened to you? Drop your story below.",
        "Like this page for weekly tips from a local {industry} pro.",
    ],
    caption_template=(
        "{hook}\n\n"
        "{scenario}\n\n"
        "Here's what we recommend:\n{tip}\n\n"
        "This matters because {reason}.\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Single photo demonstrating the tip, or a 60-second native video walkthrough. "
        "Video will significantly outperform static images. 1:1 or 16:9."
    ),
    notes=(
        "Facebook tip posts work best when framed as a conversation starter. "
        "Ask a question at the end to trigger comments."
    ),
)

CONTENT_TYPE_TEMPLATES[_tkey("local_tip_post", "tiktok")] = ContentTypeTemplate(
    content_type="local_tip_post",
    platform="tiktok",
    structure=[
        "text_hook_overlay",
        "visual_demo",
        "key_point_reveal",
        "cta_overlay",
    ],
    required_elements=["text_hook_overlay", "visual_demo", "key_point_reveal"],
    optional_elements=["cta_overlay", "trending_sound"],
    suggested_hooks=[
        "Your {service_provider} doesn't want you to know this.",
        "POV: You just saved $300 with this one tip.",
        "3 things to check on your {equipment} right now.",
        "Stop scrolling if you own a home in {location}.",
        "I've been a {trade} for {years} years — here's what I'd check first.",
    ],
    cta_options=[
        "Follow for more tips that save you money.",
        "Comment 'SAVE' and I'll send the full checklist.",
        "Share this with a homeowner who needs it.",
        "Link in bio for more {topic} help.",
        "Duet this with your own pro tip!",
    ],
    caption_template=(
        "{hook} #LocalBusiness #{location} #{industry} {hashtags}\n\n"
        "{cta}"
    ),
    media_guidance=(
        "15-30 second vertical video showing the tip in action. "
        "Use text overlays for each step. Face-to-camera or hands-only POV. "
        "Trending sound is a strong boost."
    ),
    notes="TikTok local tips go viral when they feel like insider knowledge, not a lecture.",
)

CONTENT_TYPE_TEMPLATES[_tkey("local_tip_post", "youtube")] = ContentTypeTemplate(
    content_type="local_tip_post",
    platform="youtube",
    structure=[
        "title_hook",
        "visual_demo",
        "step_by_step",
        "result_preview",
        "subscribe_cta",
    ],
    required_elements=["title_hook", "visual_demo", "step_by_step"],
    optional_elements=["result_preview", "subscribe_cta"],
    suggested_hooks=[
        "This 60-second fix will save you a service call.",
        "Every {location} homeowner should know this.",
        "Here's what a {trade} checks first — and you can too.",
        "The mistake that costs homeowners $200+ every year.",
        "Quick tip: do this BEFORE you call a {service_provider}.",
    ],
    cta_options=[
        "Subscribe for weekly home maintenance tips.",
        "Comment what you want us to cover next.",
        "Check the description for our free checklist.",
        "Share this Short with a homeowner friend.",
        "Hit the bell so you never miss a tip.",
    ],
    caption_template=(
        "{title}\n\n"
        "{tip_summary}\n\n"
        "Looking for {service} help in {location}? Visit {website}.\n\n"
        "#{industry} #{location} #Shorts #HomeTips"
    ),
    media_guidance=(
        "YouTube Short: 15-60 second vertical video demonstrating the tip. "
        "Show the problem, then the fix. Text overlay for key callouts. "
        "Thumbnail should show the result."
    ),
    notes="YouTube Shorts reach a different audience than long-form. Post tips as Shorts, deep dives as long-form.",
)

# ------------------------------------------------------------------
# 4. OfferPost (3 templates: Instagram, Facebook, X/Twitter)
# ------------------------------------------------------------------

CONTENT_TYPE_TEMPLATES[_tkey("offer_post", "instagram")] = ContentTypeTemplate(
    content_type="offer_post",
    platform="instagram",
    structure=[
        "urgency_hook",
        "offer_details",
        "social_proof",
        "deadline_reminder",
        "cta",
        "hashtags",
    ],
    required_elements=["urgency_hook", "offer_details", "cta"],
    optional_elements=["social_proof", "deadline_reminder", "story_version"],
    suggested_hooks=[
        "48 hours only: {offer} for {location} homeowners.",
        "We're opening {number} spots this week at {discount}% off.",
        "Spring is here and your {system} isn't ready. We can fix that — at a discount.",
        "Our busiest season starts in {timeframe}. Book now and save {amount}.",
        "This deal ends {deadline}. Not a day later.",
    ],
    cta_options=[
        "DM 'DEAL' to claim your spot.",
        "Tap the link in bio to book at this price.",
        "Comment your ZIP code — we'll confirm if we serve you.",
        "Tag a friend who needs this deal.",
        "Screenshot this and call us at {phone}.",
    ],
    caption_template=(
        "{hook}\n\n"
        "Here's the deal:\n"
        "{offer_details}\n\n"
        "Why now?\n"
        "{urgency_reason}\n\n"
        "Only {spots} spots left at this price.\n\n"
        "{cta}\n\n"
        "{hashtags}"
    ),
    media_guidance=(
        "Eye-catching graphic with the offer amount/percentage in large text. "
        "Use brand colors with high contrast. Create a matching story with "
        "countdown sticker and link sticker. 1:1 for feed, 9:16 for story."
    ),
    notes="Always create both a feed post and a story version. Stories with countdown stickers create urgency.",
)

CONTENT_TYPE_TEMPLATES[_tkey("offer_post", "facebook")] = ContentTypeTemplate(
    content_type="offer_post",
    platform="facebook",
    structure=[
        "pain_point_hook",
        "offer_intro",
        "offer_details",
        "trust_signal",
        "deadline",
        "cta_with_link",
    ],
    required_elements=["pain_point_hook", "offer_details", "cta_with_link"],
    optional_elements=["trust_signal", "deadline"],
    suggested_hooks=[
        "Tired of calling {service} companies that never show up? We're different.",
        "{location} homeowners: we're running our biggest sale of the year.",
        "Your {system} is working overtime this season. Let us help — at {discount}% off.",
        "We only run this promotion once a year. Here it is.",
        "First {number} callers this week get {offer}.",
    ],
    cta_options=[
        "Click here to claim your offer: {link}",
        "Call us now at {phone} — we answer every call.",
        "Message this page to book your discounted appointment.",
        "Share this deal with a {location} neighbor who needs it.",
        "Book online in 60 seconds: {link}",
    ],
    caption_template=(
        "{hook}\n\n"
        "{offer_details}\n\n"
        "This offer is available to the first {spots} customers who book before {deadline}.\n\n"
        "We've served {customer_count}+ happy customers in {location}.\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Offer graphic with clear price/discount, deadline, and phone number. "
        "Link directly to booking page. Video version showing the service "
        "in action with offer overlay will outperform static image."
    ),
    notes="Facebook allows clickable links — always include a direct booking link.",
)

CONTENT_TYPE_TEMPLATES[_tkey("offer_post", "x_twitter")] = ContentTypeTemplate(
    content_type="offer_post",
    platform="x_twitter",
    structure=[
        "punchy_hook",
        "offer_one_liner",
        "deadline",
        "link",
    ],
    required_elements=["punchy_hook", "offer_one_liner", "link"],
    optional_elements=["deadline", "reply_thread"],
    suggested_hooks=[
        "{discount}% off {service} this week. {location} only.",
        "We're booking {service} at our lowest price this year.",
        "First {number} to reply get {offer}.",
        "{location}: your {equipment} needs help. We've got a deal.",
        "Limited spots. {offer}. Ends {deadline}.",
    ],
    cta_options=[
        "Book here: {link}",
        "Reply for details.",
        "DM us your address for a quote.",
        "RT + follow for a chance at a free {service}.",
        "Call {phone} — mention this tweet.",
    ],
    caption_template=(
        "{hook}\n\n"
        "{offer_one_liner}\n\n"
        "{cta} {link}"
    ),
    media_guidance=(
        "Single image with offer details in large, readable text. "
        "16:9 aspect ratio. Keep text minimal — the tweet is the message. "
        "Add the link in a reply to the main tweet for better reach."
    ),
    notes="X penalizes tweets with links. Post the offer text first, then reply with the link.",
)

# ------------------------------------------------------------------
# 5. BehindTheScenesPost (3 templates: Instagram, TikTok, YouTube)
# ------------------------------------------------------------------

CONTENT_TYPE_TEMPLATES[_tkey("behind_the_scenes_post", "instagram")] = ContentTypeTemplate(
    content_type="behind_the_scenes_post",
    platform="instagram",
    structure=[
        "casual_hook",
        "scene_description",
        "team_highlight",
        "personality_element",
        "cta",
        "hashtags",
    ],
    required_elements=["casual_hook", "scene_description", "cta"],
    optional_elements=["team_highlight", "personality_element", "team_tags"],
    suggested_hooks=[
        "No filters. No staging. Just a Tuesday at {business_name}.",
        "Here's what 6 AM looks like when you actually love your job.",
        "Meet the crew that makes the magic happen.",
        "This is the part of {service} nobody posts about.",
        "Behind every finished project is a morning that started like this.",
    ],
    cta_options=[
        "Follow for more real looks at life in the {industry}.",
        "Drop a comment if you want to see more behind-the-scenes.",
        "Tag someone who'd love this job.",
        "What do you want to see next? Tell us in the comments.",
        "DM us if you want to join the team.",
    ],
    caption_template=(
        "{hook}\n\n"
        "{scene_description}\n\n"
        "The {business_name} crew: {team_description}\n\n"
        "{personality_note}\n\n"
        "{cta}\n\n"
        "{hashtags}"
    ),
    media_guidance=(
        "Casual, authentic photos or short video clips. Phone-quality is fine — "
        "overly polished kills the vibe. Show the workspace, the van, the tools, "
        "the coffee run. 4:5 or 1:1 for feed, 9:16 for reels."
    ),
    notes="Authenticity is everything. These posts should feel spontaneous, not produced.",
)

CONTENT_TYPE_TEMPLATES[_tkey("behind_the_scenes_post", "tiktok")] = ContentTypeTemplate(
    content_type="behind_the_scenes_post",
    platform="tiktok",
    structure=[
        "trend_format_hook",
        "day_in_the_life_sequence",
        "satisfying_moment",
        "personality_punch",
    ],
    required_elements=["trend_format_hook", "day_in_the_life_sequence"],
    optional_elements=["satisfying_moment", "personality_punch"],
    suggested_hooks=[
        "Day in the life of a {trade} in {location}.",
        "POV: You're riding along on a {service} call.",
        "Things that just hit different when you work in {industry}.",
        "The 5 AM alarm hits different when this is your office.",
        "Nobody talks about this part of running a {industry} business.",
    ],
    cta_options=[
        "Follow for the daily reality of running a small business.",
        "Comment what you want to see on the next ride-along.",
        "Would you survive a day doing this? Drop your answer.",
        "Like if you respect the trades.",
        "Share with someone who thinks this job is easy.",
    ],
    caption_template=(
        "{hook} #{industry} #DayInTheLife #{location} #SmallBusiness {hashtags}\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Day-in-the-life style video, 30-60 seconds, 9:16 vertical. "
        "Show the morning routine, the drive, the job site, the satisfying result. "
        "Use a trending sound and quick cuts. Raw phone footage preferred."
    ),
    notes="TikTok BTS content should feel like a friend's story, not a corporate video.",
)

CONTENT_TYPE_TEMPLATES[_tkey("behind_the_scenes_post", "youtube")] = ContentTypeTemplate(
    content_type="behind_the_scenes_post",
    platform="youtube",
    structure=[
        "title_hook",
        "intro_scene",
        "process_walkthrough",
        "team_personality",
        "subscribe_cta",
    ],
    required_elements=["title_hook", "process_walkthrough"],
    optional_elements=["intro_scene", "team_personality", "subscribe_cta"],
    suggested_hooks=[
        "What a real day in {industry} looks like (no sugarcoating).",
        "Watch us handle the hardest {service} job of the month.",
        "From 5 AM to final walkthrough — a full day with {business_name}.",
        "The tool everyone asks us about (and how we actually use it).",
        "This is why we love this job. And sometimes hate it.",
    ],
    cta_options=[
        "Subscribe to see more of the daily grind.",
        "Comment what job you want to see us tackle next.",
        "Check the description for our gear list.",
        "Share this Short with someone in the trades.",
        "Hit the bell for weekly behind-the-scenes content.",
    ],
    caption_template=(
        "{title}\n\n"
        "A real look at what {service} work involves. "
        "No script, no edits, just the job.\n\n"
        "Follow {business_name} for honest content from the field.\n\n"
        "#{industry} #BehindTheScenes #SmallBusiness #Shorts"
    ),
    media_guidance=(
        "YouTube Short: 30-60 second vertical clip of a real job or process. "
        "Quick cuts, natural audio, text overlays for context. "
        "End with a clean shot of the finished result."
    ),
    notes="YouTube BTS Shorts build subscriber trust. Post weekly for consistent growth.",
)

# ------------------------------------------------------------------
# 6. EducationalPost (6 templates: all platforms)
# ------------------------------------------------------------------

CONTENT_TYPE_TEMPLATES[_tkey("educational_post", "instagram")] = ContentTypeTemplate(
    content_type="educational_post",
    platform="instagram",
    structure=[
        "myth_or_question_hook",
        "educational_content",
        "expert_credibility",
        "save_and_share_cta",
        "hashtags",
    ],
    required_elements=["myth_or_question_hook", "educational_content", "save_and_share_cta"],
    optional_elements=["expert_credibility", "bonus_fact"],
    suggested_hooks=[
        "MYTH: {common_belief}. FACT: {actual_truth}.",
        "You've been {task} wrong your whole life. Here's proof.",
        "The {topic} mistake that 80% of homeowners make.",
        "Everything your {service_provider} should have told you (but didn't).",
        "If you only learn one thing about {topic} this year, let it be this.",
    ],
    cta_options=[
        "Save this for later — you'll need it.",
        "Share this with someone who still believes the myth.",
        "Follow @{handle} for weekly {industry} myth-busters.",
        "Comment with YOUR biggest {topic} question.",
        "DM 'GUIDE' for our free {topic} resource.",
    ],
    caption_template=(
        "{hook}\n\n"
        "Here's what's actually true:\n\n"
        "{point_1}\n\n"
        "{point_2}\n\n"
        "{point_3}\n\n"
        "Source: {years}+ years of {industry} experience at {business_name}.\n\n"
        "{cta}\n\n"
        "{hashtags}"
    ),
    media_guidance=(
        "Carousel with one myth/fact or step per slide. Bold headline + short "
        "explanation per slide. Last slide is CTA. 1:1 or 4:5, brand colors."
    ),
    notes="Educational carousels are the highest-saving format on Instagram. Saves drive algorithmic reach.",
)

CONTENT_TYPE_TEMPLATES[_tkey("educational_post", "facebook")] = ContentTypeTemplate(
    content_type="educational_post",
    platform="facebook",
    structure=[
        "relatable_question",
        "short_answer",
        "detailed_explanation",
        "practical_takeaway",
        "discussion_prompt",
    ],
    required_elements=["relatable_question", "short_answer", "discussion_prompt"],
    optional_elements=["detailed_explanation", "practical_takeaway"],
    suggested_hooks=[
        "Someone asked us: '{question}' — great question. Here's the answer.",
        "We see this mistake in {location} homes every single week.",
        "TRUE or FALSE: {statement}. (Answer in the comments, then read ours.)",
        "The {number} most common questions we get about {topic} — answered.",
        "Here's what a {trade} actually thinks when they walk into your home.",
    ],
    cta_options=[
        "What's YOUR {topic} question? Drop it in the comments.",
        "Share this if you learned something new.",
        "Call {phone} if you need professional help with this.",
        "Tag someone who needs this info.",
        "Like this page for weekly {industry} knowledge.",
    ],
    caption_template=(
        "{hook}\n\n"
        "Short answer: {short_answer}\n\n"
        "Longer explanation:\n{detailed_explanation}\n\n"
        "What you should do: {practical_takeaway}\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Infographic or short video (60-90 seconds) explaining the concept. "
        "Native video is best. If using an image, make it an infographic "
        "with the key points visualized."
    ),
    notes="Frame educational content as Q&A. Facebook users engage most when they feel like they're in a conversation.",
)

CONTENT_TYPE_TEMPLATES[_tkey("educational_post", "linkedin")] = ContentTypeTemplate(
    content_type="educational_post",
    platform="linkedin",
    structure=[
        "counterintuitive_hook",
        "industry_context",
        "data_or_evidence",
        "frameworks_or_steps",
        "thought_leadership_cta",
    ],
    required_elements=["counterintuitive_hook", "frameworks_or_steps", "thought_leadership_cta"],
    optional_elements=["industry_context", "data_or_evidence"],
    suggested_hooks=[
        "Most {industry} advice is wrong. Here's what the data actually shows.",
        "I've managed {count}+ {service} projects. Here are the {number} patterns that predict success.",
        "Unpopular opinion: {contrarian_take}.",
        "We tracked this metric for 12 months. The results changed how we operate.",
        "The framework that cut our {metric} in half (steal it).",
    ],
    cta_options=[
        "Repost if this resonated with your experience.",
        "Follow for more data-backed {industry} insights.",
        "What framework does your team use? Share in the comments.",
        "Connect with me if you want to discuss this further.",
        "Download the full framework (link in first comment).",
    ],
    caption_template=(
        "{hook}\n\n"
        "Here's the context:\n{industry_context}\n\n"
        "What we found:\n"
        "1. {step_1}\n"
        "2. {step_2}\n"
        "3. {step_3}\n\n"
        "The takeaway: {key_insight}\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Document carousel (PDF slides) with framework visualization, "
        "or a clean data chart. Infographics perform well. "
        "1:1 aspect ratio. No stock photos."
    ),
    notes="LinkedIn rewards depth and original thinking. Bring data or a unique framework — never generic advice.",
)

CONTENT_TYPE_TEMPLATES[_tkey("educational_post", "tiktok")] = ContentTypeTemplate(
    content_type="educational_post",
    platform="tiktok",
    structure=[
        "shock_or_curiosity_hook",
        "visual_explanation",
        "proof_or_demo",
        "key_takeaway_overlay",
    ],
    required_elements=["shock_or_curiosity_hook", "visual_explanation"],
    optional_elements=["proof_or_demo", "key_takeaway_overlay"],
    suggested_hooks=[
        "Wait — that's NOT how you're supposed to do that.",
        "I've been a {trade} for {years} years and most people get this wrong.",
        "This one thing could save you $1,000 on {service}.",
        "POV: Your {service_provider} sees this and just shakes their head.",
        "The internet told you to do this. Here's why that's bad advice.",
    ],
    cta_options=[
        "Follow for {industry} tips that actually help.",
        "Comment 'MORE' if you want a deep dive on this.",
        "Stitch this with your own {industry} myth.",
        "Send this to someone before they make this mistake.",
        "Save this — you'll need it someday.",
    ],
    caption_template=(
        "{hook} #{industry} #LearnOnTikTok #{topic} {hashtags}\n\n"
        "{cta}"
    ),
    media_guidance=(
        "15-45 second vertical video. Face to camera or hands-on demo. "
        "Use text overlays for key facts. Quick hook in first 2 seconds. "
        "Trending sound or original audio both work for educational content."
    ),
    notes="TikTok education = entertainment first. Wrap the lesson in a hook that makes them NEED to watch.",
)

CONTENT_TYPE_TEMPLATES[_tkey("educational_post", "x_twitter")] = ContentTypeTemplate(
    content_type="educational_post",
    platform="x_twitter",
    structure=[
        "provocative_statement",
        "thread_body",
        "key_points",
        "summary",
    ],
    required_elements=["provocative_statement", "key_points"],
    optional_elements=["thread_body", "summary"],
    suggested_hooks=[
        "Most {industry} advice on here is recycled garbage. Here's what actually works:",
        "Thread: {number} things I learned from {count}+ {service} projects.",
        "{topic} explained in 60 seconds (thread).",
        "Stop paying for {service} until you've checked these {number} things yourself.",
        "Hot take: {contrarian_opinion}. Let me explain.",
    ],
    cta_options=[
        "Retweet the first post if this was useful.",
        "Follow for more {industry} threads.",
        "Reply with your #1 question about {topic}.",
        "Bookmark this thread — you'll want it later.",
        "Quote tweet with your own experience.",
    ],
    caption_template=(
        "{hook}\n\n"
        "{point_1}"
    ),
    media_guidance=(
        "No media on the first tweet for maximum reach. "
        "Add images or infographics in thread replies. "
        "If single tweet (not thread), add one clean data image."
    ),
    notes=(
        "Threads are the highest-engagement educational format on X. "
        "First tweet is the hook, no links. Add links in the final reply."
    ),
)

CONTENT_TYPE_TEMPLATES[_tkey("educational_post", "youtube")] = ContentTypeTemplate(
    content_type="educational_post",
    platform="youtube",
    structure=[
        "title_question",
        "hook_payoff_preview",
        "step_by_step_demo",
        "key_takeaway",
        "subscribe_cta",
    ],
    required_elements=["title_question", "step_by_step_demo"],
    optional_elements=["hook_payoff_preview", "key_takeaway", "subscribe_cta"],
    suggested_hooks=[
        "How to {task} in {time} (even if you've never done it before).",
        "The ${cost} mistake almost every homeowner makes with {system}.",
        "{number} things your {service_provider} checks (and you should too).",
        "Why your {system} keeps failing (and the 2-minute fix).",
        "I asked {number} {trade} pros for their #1 tip. Here's what they said.",
    ],
    cta_options=[
        "Subscribe for weekly how-to videos.",
        "Comment what topic you want covered next.",
        "Check the description for timestamps and links.",
        "Share this with someone tackling a {topic} project.",
        "Hit the bell and never miss a tutorial.",
    ],
    caption_template=(
        "{title}\n\n"
        "In this video, you'll learn:\n"
        "- {point_1}\n"
        "- {point_2}\n"
        "- {point_3}\n\n"
        "Need professional {service} help in {location}? "
        "Visit {website} or call {phone}.\n\n"
        "Chapters:\n"
        "0:00 Intro\n"
        "{chapters}\n\n"
        "#{industry} #{topic} #HowTo"
    ),
    media_guidance=(
        "For Shorts: 30-60 second vertical demo with text overlays. "
        "For long-form: 5-12 minute tutorial, 16:9, with chapters. "
        "Thumbnail must show the end result or pose the question visually."
    ),
    notes="YouTube educational content has the longest shelf life of any platform. Optimize titles for search.",
)

# ------------------------------------------------------------------
# 7. CommunityPost (3 templates: Facebook, Instagram, LinkedIn)
# ------------------------------------------------------------------

CONTENT_TYPE_TEMPLATES[_tkey("community_post", "facebook")] = ContentTypeTemplate(
    content_type="community_post",
    platform="facebook",
    structure=[
        "community_connection_hook",
        "event_or_partnership_details",
        "why_it_matters",
        "invitation_or_involvement",
        "engagement_question",
    ],
    required_elements=["community_connection_hook", "event_or_partnership_details", "engagement_question"],
    optional_elements=["why_it_matters", "invitation_or_involvement"],
    suggested_hooks=[
        "Proud to support {event} in {location} this weekend!",
        "Big news: {business_name} is teaming up with {partner} for {cause}.",
        "This Saturday, you'll find the {business_name} team at {event}.",
        "We've called {location} home for {years} years. Here's how we're giving back.",
        "Shoutout to {partner} for an incredible partnership this month.",
    ],
    cta_options=[
        "Will we see you there? Drop a comment!",
        "Tag a friend who should come to {event}.",
        "Share this to help spread the word.",
        "What community events should we sponsor next? Tell us below.",
        "Like this page to stay updated on our {location} involvement.",
    ],
    caption_template=(
        "{hook}\n\n"
        "{event_details}\n\n"
        "Why this matters to us: {reason}\n\n"
        "Come find us at {booth_or_location}!\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Photos from the event or partnership — real, unposed. "
        "Group photos with the team and community members. "
        "Event flyer if promoting an upcoming event. Tag partner pages."
    ),
    notes="Community posts build local loyalty. Facebook groups are the best distribution channel for local community content.",
)

CONTENT_TYPE_TEMPLATES[_tkey("community_post", "instagram")] = ContentTypeTemplate(
    content_type="community_post",
    platform="instagram",
    structure=[
        "community_pride_hook",
        "event_or_partnership_story",
        "team_involvement",
        "cta",
        "hashtags",
    ],
    required_elements=["community_pride_hook", "event_or_partnership_story", "cta"],
    optional_elements=["team_involvement", "partner_tags"],
    suggested_hooks=[
        "This is why we love calling {location} home.",
        "The {business_name} crew showed up for {event} — and it was incredible.",
        "Supporting local means more than a bumper sticker. Here's what we did.",
        "Grateful to partner with {partner} on {initiative}.",
        "Our community showed up today. We showed up right back.",
    ],
    cta_options=[
        "Tag your favorite local {location} business.",
        "Share this if you support local businesses.",
        "Follow us for more {location} community stories.",
        "Comment with YOUR favorite {location} event.",
        "DM us about sponsorship or partnership opportunities.",
    ],
    caption_template=(
        "{hook}\n\n"
        "{story}\n\n"
        "Thanks to {partner} and everyone who made this happen.\n\n"
        "{business_name} is proud to be part of the {location} community.\n\n"
        "{cta}\n\n"
        "#{location} #SupportLocal #Community {hashtags}"
    ),
    media_guidance=(
        "Carousel of event photos — the team, the crowd, the setup. "
        "Authentic, candid shots. Tag partner accounts and event pages. "
        "Story with location sticker and mention stickers."
    ),
    notes="Instagram community posts drive local discovery when paired with location and local hashtags.",
)

CONTENT_TYPE_TEMPLATES[_tkey("community_post", "linkedin")] = ContentTypeTemplate(
    content_type="community_post",
    platform="linkedin",
    structure=[
        "values_driven_hook",
        "partnership_or_initiative",
        "business_impact",
        "call_to_action",
    ],
    required_elements=["values_driven_hook", "partnership_or_initiative", "call_to_action"],
    optional_elements=["business_impact", "team_involvement"],
    suggested_hooks=[
        "Community investment isn't a line item — it's a business strategy.",
        "Here's what happened when we partnered with {partner} in {location}.",
        "Our team volunteered {hours} hours this quarter. Here's why it matters.",
        "Local businesses that invest in community outperform those that don't. Here's how we do it.",
        "Announcing our partnership with {partner} to support {cause}.",
    ],
    cta_options=[
        "How does your company give back locally? Share in the comments.",
        "Follow for more on building community-driven businesses.",
        "Connect with {partner} if you want to get involved.",
        "Tag a business doing great community work.",
        "Repost if you agree that community investment is good business.",
    ],
    caption_template=(
        "{hook}\n\n"
        "{partnership_details}\n\n"
        "The impact so far:\n"
        "- {impact_1}\n"
        "- {impact_2}\n"
        "- {impact_3}\n\n"
        "At {business_name}, community isn't an afterthought — it's core to how we operate.\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Professional photo of the team at the event or with partners. "
        "Impact infographic if numbers are available. "
        "Tag all partner companies and individuals. 1:1 aspect ratio."
    ),
    notes="LinkedIn community posts build employer brand and B2B credibility. Lead with the business case.",
)

# ------------------------------------------------------------------
# 8. SeasonalPost (3 templates: Instagram, Facebook, TikTok)
# ------------------------------------------------------------------

CONTENT_TYPE_TEMPLATES[_tkey("seasonal_post", "instagram")] = ContentTypeTemplate(
    content_type="seasonal_post",
    platform="instagram",
    structure=[
        "seasonal_hook",
        "timely_tip_or_reminder",
        "service_tie_in",
        "offer_if_applicable",
        "cta",
        "hashtags",
    ],
    required_elements=["seasonal_hook", "timely_tip_or_reminder", "cta"],
    optional_elements=["service_tie_in", "offer_if_applicable"],
    suggested_hooks=[
        "Spring is here. Your {system} isn't ready. Here's the checklist.",
        "It's {holiday} weekend — {number} things to check before you relax.",
        "The first freeze of the season is coming. Is your {system} protected?",
        "Summer heat is no joke in {location}. Here's how to stay ahead of it.",
        "{season} maintenance window closes in {timeframe}. Don't miss it.",
    ],
    cta_options=[
        "Save this seasonal checklist for later.",
        "Book your {season} {service} before slots fill up — DM 'SEASON'.",
        "Share with a {location} homeowner who needs this reminder.",
        "Follow for seasonal maintenance reminders all year.",
        "Tap the link in bio for our full {season} prep guide.",
    ],
    caption_template=(
        "{hook}\n\n"
        "Here's your {season} {service} checklist:\n"
        "1. {item_1}\n"
        "2. {item_2}\n"
        "3. {item_3}\n\n"
        "Need help? {business_name} is booking {season} appointments now.\n\n"
        "{offer}\n\n"
        "{cta}\n\n"
        "#{season} #{service} #{location} {hashtags}"
    ),
    media_guidance=(
        "Seasonal branded graphic with checklist items, or a carousel "
        "with one checklist item per slide. Use seasonal colors and imagery. "
        "4:5 for feed, 9:16 for story version with poll sticker."
    ),
    notes="Seasonal posts are high-save, high-share content. Post 2-3 weeks before peak season for each service.",
)

CONTENT_TYPE_TEMPLATES[_tkey("seasonal_post", "facebook")] = ContentTypeTemplate(
    content_type="seasonal_post",
    platform="facebook",
    structure=[
        "seasonal_urgency_hook",
        "why_now",
        "practical_advice",
        "offer_tie_in",
        "cta_with_link",
    ],
    required_elements=["seasonal_urgency_hook", "practical_advice", "cta_with_link"],
    optional_elements=["why_now", "offer_tie_in"],
    suggested_hooks=[
        "Every year we see {location} homeowners wait too long for {service}. Don't be that person.",
        "Happy {holiday}! Quick reminder: your {system} needs attention before {season}.",
        "{season} is coming fast. Here are {number} things to do this weekend.",
        "We booked 40 appointments last {season} in the first week. Slots go fast.",
        "The {weather_event} last week damaged more {systems} than people realize.",
    ],
    cta_options=[
        "Click here to schedule your {season} {service}: {link}",
        "Call {phone} to book before our schedule fills up.",
        "Share this with a {location} homeowner before it's too late.",
        "Comment 'BOOK' and we'll send you our availability.",
        "Message us for a {season} special rate.",
    ],
    caption_template=(
        "{hook}\n\n"
        "Why now: {urgency_reason}\n\n"
        "What to do:\n"
        "1. {advice_1}\n"
        "2. {advice_2}\n"
        "3. {advice_3}\n\n"
        "{season} special: {offer}\n\n"
        "{cta}"
    ),
    media_guidance=(
        "Seasonal scene photo with service context (e.g., fall leaves on gutters, "
        "frost on equipment). Video showing seasonal prep steps outperforms static. "
        "Include booking link directly in the post."
    ),
    notes="Facebook seasonal posts with urgency and a direct booking link convert the highest of any organic content type.",
)

CONTENT_TYPE_TEMPLATES[_tkey("seasonal_post", "tiktok")] = ContentTypeTemplate(
    content_type="seasonal_post",
    platform="tiktok",
    structure=[
        "seasonal_trend_hook",
        "visual_seasonal_problem",
        "quick_fix_or_tip",
        "service_mention",
    ],
    required_elements=["seasonal_trend_hook", "visual_seasonal_problem"],
    optional_elements=["quick_fix_or_tip", "service_mention"],
    suggested_hooks=[
        "It's that time of year in {location}... and your {system} knows it.",
        "POV: You forgot to do this before {season} and now you're panicking.",
        "Things that hit different in {season} when you work in {industry}.",
        "Your {equipment} right now vs. what it should look like.",
        "{season} prep speedrun for {location} homeowners.",
    ],
    cta_options=[
        "Follow for seasonal tips all year long.",
        "Comment 'PREP' for our {season} checklist.",
        "Save this before {season} catches you off guard.",
        "Tag someone who needs this reminder.",
        "Link in bio for {season} booking.",
    ],
    caption_template=(
        "{hook} #{season} #{location} #{industry} #SeasonalTips {hashtags}\n\n"
        "{cta}"
    ),
    media_guidance=(
        "15-30 second vertical video showing the seasonal issue or prep process. "
        "Use a trending seasonal sound. Text overlays for each step. "
        "Show the problem first, then the solution."
    ),
    notes="Seasonal TikTok content should ride existing seasonal trends and sounds for maximum discovery.",
)


# ============================================================================
# Lookup Functions
# ============================================================================


def get_platform_rules(platform: str) -> Optional[PlatformFormatRules]:
    """Return the ``PlatformFormatRules`` for *platform*, or ``None``."""
    return PLATFORM_RULES.get(platform)


def get_content_type_template(
    content_type: str, platform: str
) -> Optional[ContentTypeTemplate]:
    """Return the ``ContentTypeTemplate`` for the (content_type, platform) pair.

    Returns ``None`` if the combination is not defined.
    """
    return CONTENT_TYPE_TEMPLATES.get(_tkey(content_type, platform))


def get_supported_content_types(platform: str) -> List[str]:
    """Return the list of content types that have templates for *platform*."""
    suffix = f"::{platform}"
    return sorted(
        {
            key.split("::")[0]
            for key in CONTENT_TYPE_TEMPLATES
            if key.endswith(suffix)
        }
    )


def validate_post_for_platform(
    content_text: str,
    platform: str,
    media_count: int = 0,
    hashtag_count: int = 0,
) -> List[str]:
    """Validate a post's text, media count, and hashtag count against platform rules.

    Returns a list of warning/error strings.  An empty list means everything
    passes.
    """
    rules = get_platform_rules(platform)
    if rules is None:
        return [f"Unknown platform: {platform}"]

    warnings: List[str] = []
    caption_length = len(content_text)

    # Hard limit: caption length
    if caption_length > rules.max_caption_length:
        warnings.append(
            f"Caption exceeds {platform} limit of {rules.max_caption_length} "
            f"characters (currently {caption_length})"
        )

    # Soft recommendation: caption length
    if caption_length > rules.recommended_caption_length:
        warnings.append(
            f"Caption length ({caption_length}) exceeds recommended "
            f"({rules.recommended_caption_length}) for {platform} "
            f"— consider shortening for engagement"
        )

    # Hard limit: hashtags
    if hashtag_count > rules.max_hashtags:
        warnings.append(
            f"Too many hashtags for {platform}: "
            f"{hashtag_count} used, {rules.max_hashtags} allowed"
        )

    # Soft recommendation: hashtags
    if hashtag_count > rules.recommended_hashtags:
        warnings.append(
            f"Hashtag count ({hashtag_count}) exceeds recommended "
            f"({rules.recommended_hashtags}) for {platform}"
        )

    # Hard limit: media
    if media_count > rules.max_media_items:
        warnings.append(
            f"Media count ({media_count}) exceeds {platform} maximum "
            f"of {rules.max_media_items}"
        )

    return warnings
