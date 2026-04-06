"""Caption, hashtag, and geo-tag generation for social media posts.

Takes a content type, platform, and business profile and produces
ready-to-post captions with curated hashtags and geo-tag recommendations.
Downstream modules (proof-of-life automation, scheduling) call into this
engine so that every post follows platform best practices without manual
writing.
"""

from __future__ import annotations

import copy
import hashlib
import random
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

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
# Models
# ============================================================================


class CaptionRequest(BaseModel):
    """All inputs needed to generate a social media caption."""

    content_type: str = Field(..., description="SocialContentType value")
    platform: str = Field(..., description="SocialPlatform value")
    business_name: str = Field(..., description="Name of the business")
    service_or_product: Optional[str] = Field(None, description="What was done or promoted")
    result_or_outcome: Optional[str] = Field(None, description="Measurable result or transformation")
    customer_name: Optional[str] = Field(None, description="Customer name for testimonials")
    customer_quote: Optional[str] = Field(None, description="Customer testimonial text")
    location: Optional[str] = Field(None, description="City/area for local businesses")
    offer_details: Optional[str] = Field(None, description="Promotional offer details")
    offer_deadline: Optional[str] = Field(None, description="Offer expiration date")
    seasonal_context: Optional[str] = Field(None, description="Seasonal hook, e.g. spring, back to school")
    topic: Optional[str] = Field(None, description="Educational/tip topic")
    event_name: Optional[str] = Field(None, description="Community event name")
    tone_override: Optional[str] = Field(None, description="Override default platform tone")
    include_emoji: bool = Field(True, description="Whether to suggest emoji usage")
    include_cta: bool = Field(True, description="Whether to include a call-to-action")
    custom_cta: Optional[str] = Field(None, description="Specific CTA to use instead of generated one")
    additional_context: Optional[str] = Field(None, description="Freeform additional context")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CaptionResult(BaseModel):
    """Complete generated caption with all components."""

    caption_text: str = Field(..., description="Full generated caption text")
    hook_line: str = Field(..., description="First line / scroll-stopping hook")
    body_text: str = Field(..., description="Main body after the hook")
    cta_text: str = Field(..., description="Call-to-action portion")
    hashtags: List[str] = Field(default_factory=list, description="Recommended hashtags without # prefix")
    hashtag_string: str = Field("", description="Formatted hashtag string with # prefix, space-separated")
    full_text_with_hashtags: str = Field("", description="Caption + hashtag string combined")
    character_count: int = Field(0, description="Length of full_text_with_hashtags")
    platform: str = Field(..., description="Target platform")
    warnings: List[str] = Field(default_factory=list, description="Any warnings about length, etc.")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HashtagSet(BaseModel):
    """A single hashtag with categorization and performance metadata."""

    hashtag: str = Field(..., description="Hashtag text without # prefix")
    category: str = Field(
        ...,
        description="One of: branded, industry, local, trending, niche, community",
    )
    reach_estimate: Optional[str] = Field(
        None, description="Qualitative: high (>1M), medium (100K-1M), low (<100K)"
    )
    competition_level: Optional[str] = Field(None, description="high, medium, low")
    recommended_for: List[str] = Field(
        default_factory=list, description="Platform names this hashtag works best on"
    )


class HashtagStrategy(BaseModel):
    """Full hashtag strategy with categorized sets."""

    branded_hashtags: List[HashtagSet] = Field(default_factory=list)
    industry_hashtags: List[HashtagSet] = Field(default_factory=list)
    local_hashtags: List[HashtagSet] = Field(default_factory=list)
    trending_hashtags: List[HashtagSet] = Field(default_factory=list)
    niche_hashtags: List[HashtagSet] = Field(default_factory=list)
    total_count: int = Field(0, description="Total hashtags across all categories")
    platform_optimized: bool = Field(
        False, description="Whether count has been trimmed to platform recommendation"
    )


class GeoTagRecommendation(BaseModel):
    """A single geo-tag recommendation for a post."""

    location_name: str = Field(..., description="Display name of the location")
    location_id: Optional[str] = Field(None, description="Platform-specific location ID")
    platform: str = Field(..., description="Target platform")
    relevance: str = Field(..., description="high, medium, or low")
    reason: str = Field(..., description="Why this location was recommended")


# ============================================================================
# HOOK_TEMPLATES — scroll-stopping hooks by content type
# ============================================================================

HOOK_TEMPLATES: Dict[str, List[str]] = {
    "proof_post": [
        "This {service_or_product} transformation took {timeframe}. Here's what happened.",
        "Before and after: {location} {service_or_product} that speaks for itself.",
        "{result_or_outcome} — and it started with one phone call.",
        "Our client couldn't believe the difference. Neither could we.",
        "RESULTS: {result_or_outcome} for our {location} client.",
        "What a difference. Swipe to see the before.",
        "This is what {service_or_product} should look like.",
        "The transformation our {location} client didn't think was possible.",
        "We love a good before and after. This one's special.",
        "Real results. Real client. {location}.",
    ],
    "testimonial_post": [
        "'{customer_quote}' — {customer_name}",
        "Here's what {customer_name} had to say about working with us.",
        "We don't write our own reviews. {customer_name} did.",
        "This review made our whole week.",
        "Our clients say it better than we ever could.",
        "5 stars from {customer_name} in {location}.",
        "Read what {customer_name} said about our {service_or_product}.",
        "When you get a review like this, you screenshot it immediately.",
        "THIS is why we do what we do.",
        "Real words from a real customer.",
    ],
    "local_tip_post": [
        "3 signs your home needs {service_or_product}. (Number 3 surprises most people.)",
        "Most {location} homeowners don't know this about {topic}.",
        "Quick tip from our {service_or_product} team that could save you hundreds.",
        "Here's what we tell every customer about {topic}.",
        "The question we get asked most: {topic}",
        "Stop making this {topic} mistake. Here's what to do instead.",
        "Pro tip: {topic} — from our team with 15+ years experience.",
        "You asked, we answered: {topic}",
        "Before you try to DIY your {service_or_product}, read this.",
        "The 5 {topic} myths we hear every week.",
    ],
    "offer_post": [
        "LIMITED: {offer_details}. Ends {offer_deadline}.",
        "For {location} only: {offer_details}",
        "We're running our biggest {seasonal_context} deal ever.",
        "{offer_details} — but only until {offer_deadline}.",
        "First 10 callers get {offer_details}.",
        "This deal won't last. {offer_details}",
        "Our {seasonal_context} special is HERE.",
        "{offer_details}. DM us or call now.",
        "If you've been waiting for the right time, this is it.",
        "DEAL ALERT for {location}:",
    ],
    "behind_the_scenes_post": [
        "A day in the life of our {service_or_product} team.",
        "Here's what goes into a typical {service_or_product} job.",
        "Behind the scenes at {business_name}.",
        "Meet the team that makes it happen.",
        "What you don't see: the prep behind every {service_or_product}.",
        "This is what 6 AM looks like at {business_name}.",
        "The tools of the trade. Here's what we use.",
        "Teamwork in action on today's {service_or_product} job.",
        "A peek behind the curtain.",
        "The part of {service_or_product} nobody talks about.",
    ],
    "educational_post": [
        "How to {topic} in 3 easy steps.",
        "{topic}: what most people get wrong.",
        "MYTH vs. FACT about {topic}.",
        "The 5 things you need to know about {topic}.",
        "Save this for later: {topic} guide.",
        "Why does {topic} matter? Here's the answer.",
        "Everything you need to know about {topic}.",
        "You asked about {topic}. Here's our answer.",
        "If your home does this, here's what it means.",
        "Expert answer: {topic}",
    ],
    "community_post": [
        "Proud to support {event_name} in {location}!",
        "We love being part of the {location} community.",
        "Great time at {event_name} today.",
        "Shoutout to our neighbors in {location}.",
        "{business_name} + {location} = home.",
        "Giving back to {location}: {event_name}",
        "See you at {event_name} this weekend!",
        "Thank you {location} for years of trust.",
        "Community is everything. Here's why.",
        "Our favorite part of working in {location}:",
    ],
    "seasonal_post": [
        "It's {seasonal_context} in {location} — time to think about {service_or_product}.",
        "{seasonal_context} is here. Is your home ready?",
        "Don't wait until it's too late: {seasonal_context} {service_or_product} reminder.",
        "{seasonal_context} special from {business_name}!",
        "Every {seasonal_context}, we see the same {service_or_product} issue. Here's how to avoid it.",
        "Your {seasonal_context} {service_or_product} checklist:",
        "{seasonal_context} is peak {service_or_product} season. Book now before we're full.",
        "Happy {seasonal_context} from the {business_name} family!",
        "The {seasonal_context} {service_or_product} question we get every year:",
        "{seasonal_context} prep: 5 things to do for your home this week.",
    ],
}


# ============================================================================
# CTA_LIBRARY — calls-to-action by content type and platform
# ============================================================================

# Platform-level CTAs used as defaults when no content-type-specific CTA exists.
_PLATFORM_CTAS: Dict[str, List[str]] = {
    "instagram": [
        "Link in bio",
        "DM us for details",
        "Save this for later",
        "Tag someone who needs this",
        "Double tap if you agree",
    ],
    "facebook": [
        "Click the link below",
        "Comment below",
        "Share with a friend",
        "Call us today",
        "Message us",
    ],
    "linkedin": [
        "What's your experience with this?",
        "Follow for more insights",
        "Comment your thoughts",
        "Connect with us",
        "Read the full article (link in comments)",
    ],
    "tiktok": [
        "Follow for more tips",
        "Comment your question",
        "Save this",
        "Share with someone who needs this",
        "Link in bio",
    ],
    "x_twitter": [
        "RT if you agree",
        "Reply with your take",
        "Follow for daily tips",
        "Link in thread",
        "Bookmark this",
    ],
    "youtube": [
        "Subscribe for more",
        "Drop a comment",
        "Like if this helped",
        "Watch the full video (link in bio)",
        "Share with someone",
    ],
}

CTA_LIBRARY: Dict[str, Dict[str, List[str]]] = {
    "proof_post": {
        "instagram": [
            "Want results like this? DM us to get started.",
            "Ready for your transformation? Link in bio.",
            "Your home could look like this too. Tap the link in bio.",
        ],
        "facebook": [
            "Want results like this? Click the link below to book.",
            "Ready for your transformation? Call us today.",
            "Your home could look like this too. Message us.",
        ],
        "linkedin": [
            "Want results like this for your property? Connect with us.",
            "Ready for your transformation? Comment below.",
            "See more of our work — follow for daily results.",
        ],
        "tiktok": [
            "Want results like this? Follow for more.",
            "Ready for your transformation? Link in bio.",
            "Your space could look like this. Save this for later.",
        ],
        "x_twitter": [
            "Want results like this? Reply and we'll help.",
            "Ready for your transformation? Link in thread.",
            "Your home could look like this. Bookmark this.",
        ],
        "youtube": [
            "Want results like this? Subscribe and watch the full process.",
            "Ready for your transformation? Drop a comment.",
            "Like this video if you want to see more results.",
        ],
    },
    "testimonial_post": {
        "instagram": [
            "See why our clients love us. Link in bio.",
            "Ready to be our next success story? DM us.",
            "Read more reviews — link in bio.",
        ],
        "facebook": [
            "See why our clients love us. Click below.",
            "Ready to be our next success story? Message us.",
            "Read more reviews on our page.",
        ],
        "linkedin": [
            "See why our clients trust us. Connect with us.",
            "Ready to be our next success story? Comment below.",
            "Follow us for more client results.",
        ],
        "tiktok": [
            "See why our clients love us. Follow for more.",
            "Ready to be our next success story? Link in bio.",
            "Save this and share with someone.",
        ],
        "x_twitter": [
            "See why our clients love us. Reply to learn more.",
            "Ready to be our next success story? Link in thread.",
            "Bookmark this for when you need us.",
        ],
        "youtube": [
            "See why our clients love us. Subscribe for more stories.",
            "Ready to be our next success story? Comment below.",
            "Like if this review made your day.",
        ],
    },
    "local_tip_post": {
        "instagram": [
            "Save this for when you need it.",
            "Share with a neighbor who needs to see this.",
            "Follow for more tips from our team.",
        ],
        "facebook": [
            "Save this for when you need it.",
            "Share with a friend who needs to see this.",
            "Follow our page for weekly tips.",
        ],
        "linkedin": [
            "Save this for your next project.",
            "What tips would you add? Comment below.",
            "Follow for more professional insights.",
        ],
        "tiktok": [
            "Save this for later.",
            "Share with someone who needs this tip.",
            "Follow for more tips every week.",
        ],
        "x_twitter": [
            "Bookmark this for later.",
            "Reply with your own tip.",
            "Follow for daily tips from pros.",
        ],
        "youtube": [
            "Subscribe for weekly how-to videos.",
            "Drop a comment with your questions.",
            "Like if this tip was helpful.",
        ],
    },
    "offer_post": {
        "instagram": [
            "Claim this offer before it's gone. Link in bio.",
            "DM us to book your spot.",
            "Limited spots — act now. Link in bio.",
        ],
        "facebook": [
            "Claim this offer before it's gone. Click below.",
            "Call us to book your spot.",
            "Limited spots — comment DEAL to claim yours.",
        ],
        "linkedin": [
            "Claim this offer — connect with us for details.",
            "Comment below if you're interested.",
            "Limited availability — reach out today.",
        ],
        "tiktok": [
            "Claim this offer. Link in bio.",
            "Comment DEAL and we'll send details.",
            "Limited spots — act now. Follow us.",
        ],
        "x_twitter": [
            "Claim this offer. Link in thread.",
            "Reply DEAL and we'll send details.",
            "Limited spots — act now.",
        ],
        "youtube": [
            "Claim this offer. Link in description.",
            "Comment DEAL to get started.",
            "Subscribe and don't miss our next deal.",
        ],
    },
    "behind_the_scenes_post": {
        "instagram": [
            "Follow for more behind-the-scenes content.",
            "DM us if you want to learn more about our process.",
            "Tag someone who'd love to see this.",
        ],
        "facebook": [
            "Follow our page for more behind-the-scenes.",
            "Comment below — what do you want to see next?",
            "Share this with someone who'd find it interesting.",
        ],
        "linkedin": [
            "Follow us for a look inside the business.",
            "What does your process look like? Comment below.",
            "Connect with our team.",
        ],
        "tiktok": [
            "Follow for more behind-the-scenes.",
            "Comment what you want to see next.",
            "Share with someone who'd enjoy this.",
        ],
        "x_twitter": [
            "Follow for more behind-the-scenes.",
            "Reply — what do you want to see next?",
            "Bookmark this thread.",
        ],
        "youtube": [
            "Subscribe for more behind-the-scenes videos.",
            "Comment what you want to see next.",
            "Like if you enjoyed this look inside.",
        ],
    },
    "educational_post": {
        "instagram": [
            "Save this for when you need it.",
            "Share with someone who needs to see this.",
            "Follow for more tips every week.",
        ],
        "facebook": [
            "Save this for when you need it.",
            "Share with a friend who'd find this useful.",
            "Follow for more educational content.",
        ],
        "linkedin": [
            "Save this post for reference.",
            "What would you add? Comment your thoughts.",
            "Follow for more industry knowledge.",
        ],
        "tiktok": [
            "Save this for later.",
            "Share with someone who needs to know this.",
            "Follow for more educational content.",
        ],
        "x_twitter": [
            "Bookmark this for later.",
            "Reply with your own experience.",
            "Follow for daily knowledge drops.",
        ],
        "youtube": [
            "Subscribe for more educational videos.",
            "Drop a comment with your questions.",
            "Like if you learned something new.",
        ],
    },
    "community_post": {
        "instagram": [
            "Tag us in your community photos.",
            "DM us about local events we should know about.",
            "Follow for more community stories.",
        ],
        "facebook": [
            "Tag us in your community photos.",
            "Comment if you were there.",
            "Share with someone in the neighborhood.",
        ],
        "linkedin": [
            "How does your company give back? Comment below.",
            "Connect with us to collaborate.",
            "Follow for more community updates.",
        ],
        "tiktok": [
            "Follow for more community content.",
            "Comment if you were there.",
            "Share with your local crew.",
        ],
        "x_twitter": [
            "Reply with your favorite local spot.",
            "RT to spread the word.",
            "Follow for more community updates.",
        ],
        "youtube": [
            "Subscribe for more community stories.",
            "Comment your favorite local event.",
            "Like if you love this community too.",
        ],
    },
    "seasonal_post": {
        "instagram": [
            "Book your seasonal service now. Link in bio.",
            "Save this checklist for later.",
            "DM us to schedule before we're booked up.",
        ],
        "facebook": [
            "Book your seasonal service now. Click below.",
            "Save this checklist.",
            "Call us to schedule before we're booked up.",
        ],
        "linkedin": [
            "Is your business ready for the season? Comment below.",
            "Follow for timely industry reminders.",
            "Connect with us for seasonal planning.",
        ],
        "tiktok": [
            "Book now before we're full. Link in bio.",
            "Save this seasonal checklist.",
            "Follow for more seasonal tips.",
        ],
        "x_twitter": [
            "Book now before we're full. Link in thread.",
            "Bookmark this seasonal checklist.",
            "Follow for timely reminders.",
        ],
        "youtube": [
            "Subscribe for seasonal how-to content.",
            "Comment what you need help with this season.",
            "Like if this reminder saved you headaches.",
        ],
    },
}


# ============================================================================
# INDUSTRY_HASHTAG_MAP — industry to hashtag mapping
# ============================================================================

INDUSTRY_HASHTAG_MAP: Dict[str, List[str]] = {
    "plumbing": [
        "plumber", "plumbing", "plumbinglife", "plumbersofinstagram",
        "plumbingrepair", "waterheater", "drainservice",
    ],
    "hvac": [
        "hvac", "hvaclife", "hvactech", "heating", "cooling",
        "airconditioning", "hvacservice",
    ],
    "roofing": [
        "roofing", "roofer", "roofrepair", "newroof",
        "roofingcontractor", "roofinglife",
    ],
    "landscaping": [
        "landscaping", "landscape", "lawncare", "gardening",
        "outdoorliving", "landscapedesign",
    ],
    "cleaning": [
        "cleaning", "cleaningservice", "housecleaning", "deepclean",
        "cleaningtips", "cleanhome",
    ],
    "electrician": [
        "electrician", "electrical", "electricalwork", "sparklife",
        "wiringexperts",
    ],
    "dental": [
        "dentist", "dental", "dentistry", "oralhealth", "smile",
        "dentalcare",
    ],
    "legal": [
        "lawyer", "attorney", "legaladvice", "lawfirm", "justice",
        "legalhelp",
    ],
    "real_estate": [
        "realestate", "realtor", "homesale", "househunting",
        "dreamhome", "realtorlife",
    ],
    "restaurant": [
        "restaurant", "foodie", "localfood", "eatlocal", "chef",
        "foodlover",
    ],
    "automotive": [
        "autorepair", "mechanic", "carrepair", "automotive",
        "autoservice",
    ],
    "salon": [
        "salon", "hairstylist", "beauty", "haircare", "hairdresser",
        "beautysalon",
    ],
    "fitness": [
        "fitness", "personaltrainer", "gym", "workout", "fitlife",
        "healthylifestyle",
    ],
    "accounting": [
        "accountant", "accounting", "taxseason", "smallbusiness",
        "bookkeeping", "cpa",
    ],
    "photography": [
        "photographer", "photography", "photoshoot", "portrait",
        "weddingphotography",
    ],
}

# Niche hashtags by content type (appended after industry hashtags).
_CONTENT_TYPE_HASHTAGS: Dict[str, List[str]] = {
    "proof_post": ["beforeandafter", "transformation", "results", "clientwork"],
    "testimonial_post": ["testimonial", "clientreview", "happycustomer", "fivestarreview"],
    "local_tip_post": ["protip", "diytips", "homeownertips", "localexpert"],
    "offer_post": ["specialoffer", "limitedtime", "deal", "promotion"],
    "behind_the_scenes_post": ["behindthescenes", "bts", "dayinthelife", "teamwork"],
    "educational_post": ["didyouknow", "funfact", "howto", "learnwithus"],
    "community_post": ["community", "supportlocal", "shoplocal", "localbusiness"],
    "seasonal_post": ["seasonal", "seasonaltips", "homeprep", "readyforthis"],
}

# Platform-recommended hashtag counts (mirrors PLATFORM_RULES from content_types).
_PLATFORM_HASHTAG_LIMITS: Dict[str, int] = {
    "instagram": 8,
    "facebook": 3,
    "linkedin": 4,
    "tiktok": 4,
    "x_twitter": 2,
    "youtube": 4,
}

# Platform max caption length for truncation.
_PLATFORM_MAX_LENGTH: Dict[str, int] = {
    "instagram": 2200,
    "facebook": 63206,
    "linkedin": 3000,
    "tiktok": 2200,
    "x_twitter": 280,
    "youtube": 5000,
}

# Recommended caption length for warnings.
_PLATFORM_RECOMMENDED_LENGTH: Dict[str, int] = {
    "instagram": 150,
    "facebook": 250,
    "linkedin": 1300,
    "tiktok": 150,
    "x_twitter": 260,
    "youtube": 200,
}


# ============================================================================
# CaptionGenerator
# ============================================================================


class CaptionGenerator:
    """Generates complete, platform-optimized captions from structured requests."""

    def __init__(self) -> None:
        self.hook_templates = HOOK_TEMPLATES
        self.cta_library = CTA_LIBRARY
        # Internal round-robin counters per content type.
        self._hook_index: Dict[str, int] = {}
        self._cta_index: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_caption(self, request: CaptionRequest) -> CaptionResult:
        """Main generation method.

        1. Select and fill a hook template.
        2. Build body text from request context.
        3. Select and personalize a CTA.
        4. Combine and format for the target platform.
        5. Validate against platform character limits.
        6. Return a fully populated CaptionResult.
        """
        hook = self._select_hook(request.content_type, request)
        body = self._build_body(request.content_type, request)
        cta = self._select_cta(request.content_type, request.platform, request)

        caption_text = self._format_for_platform(
            hook, body, cta, request.platform, request.include_emoji,
        )

        caption_text, warnings = self._truncate_for_platform(caption_text, request.platform)

        # Generate hashtags via a co-located HashtagGenerator.
        hashtag_gen = HashtagGenerator()
        industry = request.metadata.get("industry") if request.metadata else None
        strategy = hashtag_gen.generate_hashtags(
            business_name=request.business_name,
            industry=industry,
            location=request.location,
            content_type=request.content_type,
            platform=request.platform,
        )
        all_hashtags = (
            strategy.branded_hashtags
            + strategy.industry_hashtags
            + strategy.local_hashtags
            + strategy.niche_hashtags
            + strategy.trending_hashtags
        )
        hashtag_words = [h.hashtag for h in all_hashtags]
        hashtag_string = " ".join(f"#{tag}" for tag in hashtag_words)

        # Build full text with hashtags per platform convention.
        if request.platform == "instagram":
            full_text = f"{caption_text}\n\n{hashtag_string}" if hashtag_string else caption_text
        elif request.platform == "x_twitter":
            # Hashtags inline or appended tightly.
            if hashtag_string:
                tentative = f"{caption_text} {hashtag_string}"
                max_len = _PLATFORM_MAX_LENGTH.get("x_twitter", 280)
                if len(tentative) > max_len:
                    full_text = caption_text
                    warnings.append(
                        "Hashtags omitted from X post to stay within 280 characters."
                    )
                else:
                    full_text = tentative
            else:
                full_text = caption_text
        else:
            full_text = f"{caption_text}\n\n{hashtag_string}" if hashtag_string else caption_text

        char_count = len(full_text)

        return CaptionResult(
            caption_text=caption_text,
            hook_line=hook,
            body_text=body,
            cta_text=cta,
            hashtags=hashtag_words,
            hashtag_string=hashtag_string,
            full_text_with_hashtags=full_text,
            character_count=char_count,
            platform=request.platform,
            warnings=warnings,
            metadata=request.metadata,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _select_hook(self, content_type: str, request: CaptionRequest) -> str:
        """Pick the most appropriate hook template and fill placeholders.

        Uses round-robin selection to avoid repeating the same hook
        for successive calls within the same content type.
        """
        templates = self.hook_templates.get(content_type, [])
        if not templates:
            return f"Check out {request.business_name}!"

        idx = self._hook_index.get(content_type, 0)
        template = templates[idx % len(templates)]
        self._hook_index[content_type] = idx + 1

        return self._fill_placeholders(template, request)

    def _build_body(self, content_type: str, request: CaptionRequest) -> str:
        """Construct the body paragraph based on content type and available fields."""
        parts: List[str] = []

        if content_type == "proof_post":
            if request.service_or_product:
                parts.append(f"Our {request.service_or_product} team delivered for this client.")
            if request.result_or_outcome:
                parts.append(f"The result: {request.result_or_outcome}.")
            if request.location:
                parts.append(f"Another satisfied customer in {request.location}.")
            if request.additional_context:
                parts.append(request.additional_context)

        elif content_type == "testimonial_post":
            if request.customer_quote and request.customer_name:
                parts.append(
                    f'"{request.customer_quote}" — {request.customer_name}'
                )
            elif request.customer_quote:
                parts.append(f'"{request.customer_quote}"')
            if request.service_or_product:
                parts.append(
                    f"Thank you for trusting {request.business_name} with your {request.service_or_product}."
                )
            if request.additional_context:
                parts.append(request.additional_context)

        elif content_type == "local_tip_post":
            if request.topic:
                parts.append(f"Here's what our team recommends about {request.topic}.")
            if request.service_or_product:
                parts.append(
                    f"As {request.location or 'local'} {request.service_or_product} pros, "
                    f"we see this come up all the time."
                )
            if request.additional_context:
                parts.append(request.additional_context)

        elif content_type == "offer_post":
            if request.offer_details:
                parts.append(request.offer_details)
            if request.offer_deadline:
                parts.append(f"This offer ends {request.offer_deadline}. Don't wait.")
            if request.location:
                parts.append(f"Available for {request.location} customers.")
            if request.additional_context:
                parts.append(request.additional_context)

        elif content_type == "behind_the_scenes_post":
            if request.service_or_product:
                parts.append(
                    f"A look at how our {request.service_or_product} team gets it done."
                )
            parts.append(
                f"At {request.business_name}, every job gets our full attention."
            )
            if request.additional_context:
                parts.append(request.additional_context)

        elif content_type == "educational_post":
            if request.topic:
                parts.append(f"Let's talk about {request.topic}.")
            if request.service_or_product:
                parts.append(
                    f"Our {request.service_or_product} team breaks it down for you."
                )
            if request.additional_context:
                parts.append(request.additional_context)

        elif content_type == "community_post":
            if request.event_name:
                parts.append(f"We had a great time at {request.event_name}.")
            if request.location:
                parts.append(
                    f"{request.business_name} is proud to be part of the {request.location} community."
                )
            if request.additional_context:
                parts.append(request.additional_context)

        elif content_type == "seasonal_post":
            if request.seasonal_context and request.service_or_product:
                parts.append(
                    f"{request.seasonal_context.capitalize()} is the right time to think about "
                    f"{request.service_or_product}."
                )
            if request.location:
                parts.append(
                    f"Here in {request.location}, we see this every year."
                )
            if request.offer_details:
                parts.append(f"Special: {request.offer_details}")
            if request.additional_context:
                parts.append(request.additional_context)

        else:
            # Generic fallback
            if request.service_or_product:
                parts.append(
                    f"{request.business_name} offers expert {request.service_or_product}."
                )
            if request.additional_context:
                parts.append(request.additional_context)

        if not parts:
            parts.append(
                f"{request.business_name} — trusted by the community."
            )

        return " ".join(parts)

    def _select_cta(
        self, content_type: str, platform: str, request: CaptionRequest,
    ) -> str:
        """Select and personalize a CTA."""
        if not request.include_cta:
            return ""

        if request.custom_cta:
            return request.custom_cta

        # Try content-type + platform specific CTAs first.
        ctas = (
            self.cta_library.get(content_type, {}).get(platform, [])
            or _PLATFORM_CTAS.get(platform, [])
        )

        if not ctas:
            return ""

        key = f"{content_type}_{platform}"
        idx = self._cta_index.get(key, 0)
        cta = ctas[idx % len(ctas)]
        self._cta_index[key] = idx + 1

        return self._fill_placeholders(cta, request)

    def _format_for_platform(
        self,
        hook: str,
        body: str,
        cta: str,
        platform: str,
        include_emoji: bool,
    ) -> str:
        """Apply platform-specific formatting and line break conventions."""
        # Optional emoji prefix for certain content types.
        emoji_hook = hook
        if include_emoji and hook and not hook[0] in ("'", '"', "{"):
            # Add a simple attention-grabber for visual platforms.
            if platform in ("instagram", "tiktok", "facebook"):
                emoji_hook = hook  # Keep the hook as-is; emojis in templates are explicit.

        if platform == "instagram":
            # Hook + double line break + body + double line break + CTA
            segments = [emoji_hook]
            if body:
                segments.append(body)
            if cta:
                segments.append(cta)
            return "\n\n".join(segments)

        elif platform == "facebook":
            # Hook + single line break + body + single line break + CTA
            segments = [emoji_hook]
            if body:
                segments.append(body)
            if cta:
                segments.append(cta)
            return "\n".join(segments)

        elif platform == "linkedin":
            # Hook + line break (triggers "see more") + body + line break + CTA
            segments = [emoji_hook]
            if body:
                segments.append(body)
            if cta:
                segments.append(cta)
            return "\n".join(segments)

        elif platform == "tiktok":
            # All compact — single spaces
            segments = [s for s in (emoji_hook, body, cta) if s]
            return " ".join(segments)

        elif platform == "x_twitter":
            # Hook + CTA only (body may be omitted to stay under 280)
            segments = [s for s in (emoji_hook, cta) if s]
            tentative = " ".join(segments)
            max_len = _PLATFORM_MAX_LENGTH.get("x_twitter", 280)
            if len(tentative) <= max_len:
                return tentative
            # If hook + cta alone exceeds, try hook only
            if len(emoji_hook) <= max_len:
                return emoji_hook
            return emoji_hook[:max_len]

        elif platform == "youtube":
            # Description format: hook + body + CTA
            segments = [emoji_hook]
            if body:
                segments.append(body)
            if cta:
                segments.append(cta)
            return "\n\n".join(segments)

        else:
            # Default formatting
            segments = [s for s in (emoji_hook, body, cta) if s]
            return "\n\n".join(segments)

    def _truncate_for_platform(
        self, text: str, platform: str,
    ) -> Tuple[str, List[str]]:
        """Truncate text if it exceeds platform max length.

        Preserves the hook (first line) and CTA (last line), trimming
        body text from the middle.  Returns (text, warnings).
        """
        max_len = _PLATFORM_MAX_LENGTH.get(platform, 5000)
        rec_len = _PLATFORM_RECOMMENDED_LENGTH.get(platform, max_len)
        warnings: List[str] = []

        if len(text) > max_len:
            lines = text.split("\n")
            hook_line = lines[0] if lines else ""
            cta_line = lines[-1] if len(lines) > 1 else ""
            # Budget for hook + cta + separators.
            budget = max_len - len(hook_line) - len(cta_line) - 4  # 4 for \n\n separators
            if budget <= 0:
                # Even hook + cta exceeds; truncate hook.
                truncated = text[:max_len - 3] + "..."
            else:
                middle = "\n".join(lines[1:-1]) if len(lines) > 2 else ""
                if len(middle) > budget:
                    middle = middle[: budget - 3] + "..."
                truncated = f"{hook_line}\n\n{middle}\n\n{cta_line}".strip()
            warnings.append(
                f"Caption truncated to {max_len} characters for {platform}."
            )
            text = truncated

        elif len(text) > rec_len:
            warnings.append(
                f"Caption exceeds recommended length for {platform} "
                f"({len(text)} chars vs {rec_len} recommended). "
                f"Consider shortening for higher engagement."
            )

        return text, warnings

    # ------------------------------------------------------------------
    # Placeholder helpers
    # ------------------------------------------------------------------

    def _fill_placeholders(self, template: str, request: CaptionRequest) -> str:
        """Replace ``{field_name}`` placeholders with values from *request*.

        Missing or ``None`` values are replaced with sensible defaults so
        that no raw ``{placeholder}`` text leaks into the output.
        """
        replacements: Dict[str, str] = {
            "business_name": request.business_name or "",
            "service_or_product": request.service_or_product or "our services",
            "result_or_outcome": request.result_or_outcome or "amazing results",
            "customer_name": request.customer_name or "our customer",
            "customer_quote": request.customer_quote or "",
            "location": request.location or "our area",
            "offer_details": request.offer_details or "a special offer",
            "offer_deadline": request.offer_deadline or "soon",
            "seasonal_context": request.seasonal_context or "this season",
            "topic": request.topic or "this topic",
            "event_name": request.event_name or "the event",
            "timeframe": request.metadata.get("timeframe", "a short time") if request.metadata else "a short time",
            "service": request.service_or_product or "our services",
            "number": request.metadata.get("number", "5") if request.metadata else "5",
            "years": request.metadata.get("years", "10") if request.metadata else "10",
            "item": request.metadata.get("item", "property") if request.metadata else "property",
            "season": request.seasonal_context or "this season",
            "holiday": request.metadata.get("holiday", "the holidays") if request.metadata else "the holidays",
            "time": request.metadata.get("time", "6") if request.metadata else "6",
            "day": request.metadata.get("day", "Saturday") if request.metadata else "Saturday",
            "partner_name": request.metadata.get("partner_name", "our partners") if request.metadata else "our partners",
            "myth": request.metadata.get("myth", "a common myth") if request.metadata else "a common myth",
            "fact": request.metadata.get("fact", "the real answer") if request.metadata else "the real answer",
            "phone": request.metadata.get("phone", "") if request.metadata else "",
            "url": request.metadata.get("url", "") if request.metadata else "",
            "deadline": request.offer_deadline or "soon",
        }
        result = template
        for key, value in replacements.items():
            result = result.replace(f"{{{key}}}", value)
        return result


# ============================================================================
# HashtagGenerator
# ============================================================================


class HashtagGenerator:
    """Generates categorized, platform-optimized hashtag strategies."""

    def __init__(self) -> None:
        self._used_sets: List[str] = []

    def generate_hashtags(
        self,
        business_name: str,
        industry: Optional[str] = None,
        location: Optional[str] = None,
        content_type: Optional[str] = None,
        platform: str = "instagram",
        custom_hashtags: Optional[List[str]] = None,
    ) -> HashtagStrategy:
        """Build a full HashtagStrategy for a post.

        1. Generate branded hashtags from business name.
        2. Generate industry hashtags from INDUSTRY_HASHTAG_MAP.
        3. Generate local hashtags from location.
        4. Trending hashtags (empty — requires live API data).
        5. Niche hashtags from content-type-specific lists.
        6. Trim to platform-recommended count.
        7. Add any custom hashtags.
        """
        all_platforms = [
            "instagram", "facebook", "linkedin", "tiktok", "x_twitter", "youtube",
        ]

        # 1. Branded hashtags
        branded: List[HashtagSet] = []
        sanitized_name = self._sanitize_hashtag(business_name)
        if sanitized_name:
            branded.append(
                HashtagSet(
                    hashtag=sanitized_name,
                    category="branded",
                    reach_estimate="low",
                    competition_level="low",
                    recommended_for=all_platforms,
                )
            )
        if location and sanitized_name:
            sanitized_loc = self._sanitize_hashtag(location)
            branded.append(
                HashtagSet(
                    hashtag=f"{sanitized_name}{sanitized_loc}",
                    category="branded",
                    reach_estimate="low",
                    competition_level="low",
                    recommended_for=all_platforms,
                )
            )

        # 2. Industry hashtags
        industry_tags: List[HashtagSet] = []
        if industry and industry.lower() in INDUSTRY_HASHTAG_MAP:
            for tag in INDUSTRY_HASHTAG_MAP[industry.lower()]:
                industry_tags.append(
                    HashtagSet(
                        hashtag=tag,
                        category="industry",
                        reach_estimate="high",
                        competition_level="high",
                        recommended_for=all_platforms,
                    )
                )

        # 3. Local hashtags
        local_tags: List[HashtagSet] = []
        if location:
            sanitized_loc = self._sanitize_hashtag(location)
            local_tags.append(
                HashtagSet(
                    hashtag=sanitized_loc,
                    category="local",
                    reach_estimate="medium",
                    competition_level="low",
                    recommended_for=["instagram", "facebook", "tiktok"],
                )
            )
            if industry:
                local_tags.append(
                    HashtagSet(
                        hashtag=f"{sanitized_loc}{self._sanitize_hashtag(industry)}",
                        category="local",
                        reach_estimate="low",
                        competition_level="low",
                        recommended_for=["instagram", "facebook"],
                    )
                )
            local_tags.append(
                HashtagSet(
                    hashtag=f"{sanitized_loc}business",
                    category="local",
                    reach_estimate="low",
                    competition_level="low",
                    recommended_for=["instagram", "facebook"],
                )
            )

        # 4. Trending hashtags — empty by default (needs live API)
        trending_tags: List[HashtagSet] = []

        # 5. Niche hashtags from content type
        niche_tags: List[HashtagSet] = []
        if content_type and content_type in _CONTENT_TYPE_HASHTAGS:
            for tag in _CONTENT_TYPE_HASHTAGS[content_type]:
                niche_tags.append(
                    HashtagSet(
                        hashtag=tag,
                        category="niche",
                        reach_estimate="medium",
                        competition_level="medium",
                        recommended_for=all_platforms,
                    )
                )

        # Add custom hashtags as niche
        if custom_hashtags:
            for tag in custom_hashtags:
                sanitized = self._sanitize_hashtag(tag)
                if sanitized:
                    niche_tags.append(
                        HashtagSet(
                            hashtag=sanitized,
                            category="niche",
                            reach_estimate=None,
                            competition_level=None,
                            recommended_for=all_platforms,
                        )
                    )

        # Deduplicate across all categories.
        all_tags = branded + industry_tags + local_tags + niche_tags + trending_tags
        all_tags = self._deduplicate(all_tags)

        # Re-split into categories after dedup.
        branded = [t for t in all_tags if t.category == "branded"]
        industry_tags = [t for t in all_tags if t.category == "industry"]
        local_tags = [t for t in all_tags if t.category == "local"]
        niche_tags = [t for t in all_tags if t.category == "niche"]
        trending_tags = [t for t in all_tags if t.category == "trending"]

        # 6. Trim to platform count
        combined = branded + local_tags + industry_tags + niche_tags + trending_tags
        trimmed = self._trim_to_platform(combined, platform)
        platform_optimized = len(trimmed) < len(combined)

        # Re-split trimmed into categories.
        branded_final = [t for t in trimmed if t.category == "branded"]
        industry_final = [t for t in trimmed if t.category == "industry"]
        local_final = [t for t in trimmed if t.category == "local"]
        niche_final = [t for t in trimmed if t.category == "niche"]
        trending_final = [t for t in trimmed if t.category == "trending"]

        total_count = len(trimmed)

        return HashtagStrategy(
            branded_hashtags=branded_final,
            industry_hashtags=industry_final,
            local_hashtags=local_final,
            trending_hashtags=trending_final,
            niche_hashtags=niche_final,
            total_count=total_count,
            platform_optimized=platform_optimized,
        )

    def _sanitize_hashtag(self, text: str) -> str:
        """Remove spaces, special characters; ensure lowercase; limit to 100 chars."""
        import re

        sanitized = re.sub(r"[^a-zA-Z0-9]", "", text)
        sanitized = sanitized.lower()
        return sanitized[:100]

    def _deduplicate(self, hashtags: List[HashtagSet]) -> List[HashtagSet]:
        """Remove duplicate hashtags, keeping the first occurrence."""
        seen: set = set()
        unique: List[HashtagSet] = []
        for h in hashtags:
            key = h.hashtag.lower()
            if key not in seen:
                seen.add(key)
                unique.append(h)
        return unique

    def _trim_to_platform(
        self, hashtags: List[HashtagSet], platform: str,
    ) -> List[HashtagSet]:
        """Reduce to recommended count for platform.

        Priority order: branded > local > industry > niche > trending.
        """
        limit = _PLATFORM_HASHTAG_LIMITS.get(platform, 8)
        if len(hashtags) <= limit:
            return list(hashtags)

        priority_order = ["branded", "local", "industry", "niche", "trending"]
        result: List[HashtagSet] = []
        for category in priority_order:
            for h in hashtags:
                if h.category == category and len(result) < limit:
                    result.append(h)
            if len(result) >= limit:
                break

        return result


# ============================================================================
# GeoTagRecommender
# ============================================================================


class GeoTagRecommender:
    """Recommends geo-tags based on content type, business location, and service area."""

    def __init__(self) -> None:
        pass

    def recommend_geo_tags(
        self,
        business_name: str,
        service_areas: List[str],
        post_content_type: str,
        platform: str,
    ) -> List[GeoTagRecommendation]:
        """Recommend 1-3 geo-tags sorted by relevance.

        Selection logic varies by content type:
        - proof_post / behind_the_scenes: specific job location + business location
        - offer_post / seasonal_post: primary service area city
        - community_post: event/community location
        - educational / testimonial / local_tip: business primary city
        - Always includes business primary location.
        """
        if not service_areas:
            return []

        primary = service_areas[0]
        recommendations: List[GeoTagRecommendation] = []

        if post_content_type in ("proof_post", "behind_the_scenes_post"):
            # Specific job location (second area if available) + primary.
            recommendations.append(
                GeoTagRecommendation(
                    location_name=self._format_location_name(primary),
                    location_id=None,
                    platform=platform,
                    relevance="high",
                    reason=f"Primary business location for {business_name}.",
                )
            )
            if len(service_areas) > 1:
                secondary = service_areas[1]
                recommendations.append(
                    GeoTagRecommendation(
                        location_name=self._format_location_name(secondary),
                        location_id=None,
                        platform=platform,
                        relevance="high",
                        reason="Job site location for this specific project.",
                    )
                )

        elif post_content_type in ("offer_post", "seasonal_post"):
            # Primary service area city.
            recommendations.append(
                GeoTagRecommendation(
                    location_name=self._format_location_name(primary),
                    location_id=None,
                    platform=platform,
                    relevance="high",
                    reason="Primary service area — target audience is here.",
                )
            )

        elif post_content_type == "community_post":
            # Event/community location (use primary as proxy).
            recommendations.append(
                GeoTagRecommendation(
                    location_name=self._format_location_name(primary),
                    location_id=None,
                    platform=platform,
                    relevance="high",
                    reason="Community event location.",
                )
            )

        elif post_content_type in ("educational_post", "testimonial_post", "local_tip_post"):
            # Business primary city.
            recommendations.append(
                GeoTagRecommendation(
                    location_name=self._format_location_name(primary),
                    location_id=None,
                    platform=platform,
                    relevance="high",
                    reason="Business primary location — establishes local authority.",
                )
            )

        else:
            # Default: primary location.
            recommendations.append(
                GeoTagRecommendation(
                    location_name=self._format_location_name(primary),
                    location_id=None,
                    platform=platform,
                    relevance="medium",
                    reason="Default business location tag.",
                )
            )

        # For local businesses, add additional service areas (up to 3 total).
        for area in service_areas[1:]:
            if len(recommendations) >= 3:
                break
            already_listed = {r.location_name for r in recommendations}
            formatted = self._format_location_name(area)
            if formatted not in already_listed:
                recommendations.append(
                    GeoTagRecommendation(
                        location_name=formatted,
                        location_id=None,
                        platform=platform,
                        relevance="medium",
                        reason=f"Additional service area for {business_name}.",
                    )
                )

        # Sort by relevance (high first).
        relevance_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: relevance_order.get(r.relevance, 3))

        return recommendations[:3]

    def _format_location_name(self, area: str) -> str:
        """Clean up location string for use as a geo-tag.

        Title-cases the string and removes trailing state abbreviations
        like ", CA" or ", TX".
        """
        import re

        cleaned = area.strip()
        # Remove trailing state abbreviations (e.g., ", CA", ", TX").
        cleaned = re.sub(r",\s*[A-Z]{2}\s*$", "", cleaned)
        return cleaned.title()
