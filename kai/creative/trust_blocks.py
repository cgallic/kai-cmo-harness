"""Trust and social-proof block templates with review rendering.

Provides reusable, structured templates for common trust-building page
sections (credentials bars, review aggregates, testimonial cards, case
study snippets, team showcases, guarantee badges, media mentions, and
numbers bars) plus a ``ReviewRenderer`` that transforms raw review data
into website testimonials, social proof graphics, aggregate displays,
and review response templates.

Uses the ``dataclass`` + ``SerializableModel`` pattern from
``kai/runtime/models.py``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from kai.runtime.models import SerializableModel


# ============================================================================
# Enums
# ============================================================================


class TrustBlockType(str, Enum):
    """Canonical trust block type identifiers."""

    credentials_bar = "credentials_bar"
    review_aggregate = "review_aggregate"
    testimonial_card = "testimonial_card"
    case_study_snippet = "case_study_snippet"
    team_showcase = "team_showcase"
    guarantee_badge = "guarantee_badge"
    media_mentions = "media_mentions"
    numbers_bar = "numbers_bar"
    trust_seal_row = "trust_seal_row"
    client_logos = "client_logos"


# ============================================================================
# Data models
# ============================================================================


@dataclass
class TrustBlockTemplate(SerializableModel):
    """A single trust/proof block template ready for rendering."""

    block_type: str
    name: str
    description: str
    required_data: List[str] = field(default_factory=list)
    optional_data: List[str] = field(default_factory=list)
    html_structure: str = ""
    copy_template: str = ""
    schema_markup: Optional[str] = None
    placement_guidance: str = "mid_page"
    archetype_relevance: List[str] = field(default_factory=list)


@dataclass
class ReviewData(SerializableModel):
    """A single review from any platform."""

    reviewer_name: str = ""
    rating: int = 5
    review_text: str = ""
    platform: str = "google"
    date: str = ""
    response: Optional[str] = None
    service_type: Optional[str] = None
    verified: bool = False


@dataclass
class ReviewAggregate(SerializableModel):
    """Aggregate review statistics across one or more platforms."""

    total_reviews: int = 0
    average_rating: float = 0.0
    platform: str = "google"
    rating_distribution: Dict[int, int] = field(default_factory=dict)
    recent_reviews: List[ReviewData] = field(default_factory=list)
    multi_platform_totals: Optional[Dict[str, Dict[str, Any]]] = None


# ============================================================================
# Trust block template builders
# ============================================================================


def build_credentials_bar() -> TrustBlockTemplate:
    """Horizontal credentials bar with certifications and license numbers."""
    return TrustBlockTemplate(
        block_type=TrustBlockType.credentials_bar.value,
        name="Credentials Bar",
        description=(
            "Horizontal row of certification badges, license numbers, and "
            "insurance logos. Establishes professional credibility at a glance."
        ),
        required_data=["business_name", "credentials"],
        optional_data=["license_numbers", "insurance_details", "years_in_business"],
        html_structure=(
            '<div class="credentials-bar">\n'
            "  {credential_items}\n"
            '  <!-- Each item: <span class="credential-badge">'
            '<img src="{badge_icon}" alt="{credential_name}" /> '
            "{credential_name}</span> -->\n"
            "</div>"
        ),
        copy_template="{credential_name} | License #{license_number} | Since {year}",
        schema_markup=(
            "{\n"
            '  "@context": "https://schema.org",\n'
            '  "@type": "LocalBusiness",\n'
            '  "name": "{business_name}",\n'
            '  "hasCredential": [\n'
            "    {\n"
            '      "@type": "EducationalOccupationalCredential",\n'
            '      "credentialCategory": "{credential_type}",\n'
            '      "name": "{credential_name}"\n'
            "    }\n"
            "  ]\n"
            "}"
        ),
        placement_guidance="hero_adjacent",
        archetype_relevance=["local_service", "professional_services"],
    )


def build_review_aggregate() -> TrustBlockTemplate:
    """Large aggregate review display — stars, count, platform link."""
    return TrustBlockTemplate(
        block_type=TrustBlockType.review_aggregate.value,
        name="Review Aggregate",
        description=(
            "Large-format aggregate review display showing star rating, "
            "total count, and source platform. The single most powerful "
            "trust element for most businesses."
        ),
        required_data=["review_count", "avg_rating", "review_platform"],
        optional_data=["review_url", "rating_distribution", "multi_platform_totals"],
        html_structure=(
            '<div class="review-aggregate">\n'
            '  <span class="stars">{star_icons}</span>\n'
            '  <span class="rating">{avg_rating}</span>\n'
            '  <span class="count">from {review_count} {platform} reviews</span>\n'
            '  <a href="{review_url}">Read our reviews</a>\n'
            "</div>"
        ),
        copy_template="{avg_rating} stars from {review_count} {platform} reviews",
        schema_markup=(
            "{\n"
            '  "@context": "https://schema.org",\n'
            '  "@type": "AggregateRating",\n'
            '  "ratingValue": "{avg_rating}",\n'
            '  "reviewCount": "{review_count}",\n'
            '  "bestRating": "5",\n'
            '  "worstRating": "1"\n'
            "}"
        ),
        placement_guidance="hero_adjacent",
        archetype_relevance=[],  # all archetypes
    )


def build_testimonial_card() -> TrustBlockTemplate:
    """Individual customer testimonial with attribution."""
    return TrustBlockTemplate(
        block_type=TrustBlockType.testimonial_card.value,
        name="Testimonial Card",
        description=(
            "Individual customer testimonial displayed as a styled quote "
            "card with attribution, optional photo, and star rating. "
            "Best used in groups of 2-4."
        ),
        required_data=["quote_text", "customer_name"],
        optional_data=["customer_photo_url", "star_rating", "service_type", "date", "city"],
        html_structure=(
            '<div class="testimonial-card">\n'
            '  <div class="stars">{star_icons}</div>\n'
            '  <blockquote>"{quote_text}"</blockquote>\n'
            '  <div class="attribution">\n'
            '    <img src="{customer_photo_url}" alt="{customer_name}" />\n'
            "    <span>{customer_name}, {city}</span>\n"
            "  </div>\n"
            "</div>"
        ),
        copy_template='"{quote_text}" \u2014 {customer_name}, {city}',
        schema_markup=(
            "{\n"
            '  "@context": "https://schema.org",\n'
            '  "@type": "Review",\n'
            '  "author": {\n'
            '    "@type": "Person",\n'
            '    "name": "{customer_name}"\n'
            "  },\n"
            '  "reviewBody": "{quote_text}",\n'
            '  "reviewRating": {\n'
            '    "@type": "Rating",\n'
            '    "ratingValue": "{star_rating}"\n'
            "  }\n"
            "}"
        ),
        placement_guidance="mid_page",
        archetype_relevance=[],  # all archetypes
    )


def build_case_study_snippet() -> TrustBlockTemplate:
    """Problem-Solution-Result in three sentences."""
    return TrustBlockTemplate(
        block_type=TrustBlockType.case_study_snippet.value,
        name="Case Study Snippet",
        description=(
            "Problem \u2192 Solution \u2192 Result in three concise sentences. "
            "Demonstrates real outcomes without requiring a full case study "
            "page. Works especially well for B2B and service businesses."
        ),
        required_data=["problem", "solution", "result"],
        optional_data=["client_name", "industry", "metric_improvement"],
        html_structure=(
            '<div class="case-study-snippet">\n'
            '  <div class="step">\n'
            '    <span class="icon">\u26a0\ufe0f</span>\n'
            "    <h4>Challenge</h4>\n"
            "    <p>{problem}</p>\n"
            "  </div>\n"
            '  <div class="step">\n'
            '    <span class="icon">\u2699\ufe0f</span>\n'
            "    <h4>Solution</h4>\n"
            "    <p>{solution}</p>\n"
            "  </div>\n"
            '  <div class="step">\n'
            '    <span class="icon">\u2705</span>\n'
            "    <h4>Result</h4>\n"
            "    <p>{result}</p>\n"
            "  </div>\n"
            "</div>"
        ),
        copy_template="Challenge: {problem}. Solution: {solution}. Result: {result}.",
        schema_markup=None,
        placement_guidance="mid_page",
        archetype_relevance=["professional_services", "local_service"],
    )


def build_team_showcase() -> TrustBlockTemplate:
    """Team photo/bio grid with experience highlights."""
    return TrustBlockTemplate(
        block_type=TrustBlockType.team_showcase.value,
        name="Team Showcase",
        description=(
            "Grid of team member cards showing photo, name, role, and "
            "years of experience. Humanizes the business and builds "
            "personal connection with visitors."
        ),
        required_data=["team_members"],
        optional_data=["team_photo_url", "certifications", "fun_fact"],
        html_structure=(
            '<div class="team-grid">\n'
            "  {team_member_cards}\n"
            "  <!-- Each card:\n"
            '  <div class="team-card">\n'
            '    <img src="{photo_url}" alt="{name}" />\n'
            "    <h4>{name}</h4>\n"
            "    <p>{role}</p>\n"
            "    <p>{years_experience} years of experience</p>\n"
            "  </div>\n"
            "  -->\n"
            "</div>"
        ),
        copy_template="{name}, {role} \u2014 {years_experience} years of experience",
        schema_markup=None,
        placement_guidance="mid_page",
        archetype_relevance=["local_service", "professional_services"],
    )


def build_guarantee_badge() -> TrustBlockTemplate:
    """Guarantee statement with badge/seal visual concept."""
    return TrustBlockTemplate(
        block_type=TrustBlockType.guarantee_badge.value,
        name="Guarantee Badge",
        description=(
            "Guarantee statement with badge/seal visual concept. Reduces "
            "purchase risk at the point of decision. Place near CTAs for "
            "maximum conversion lift."
        ),
        required_data=["guarantee_text", "guarantee_type"],
        optional_data=["guarantee_duration", "terms_url"],
        html_structure=(
            '<div class="guarantee-badge">\n'
            '  <div class="badge-seal">\n'
            '    <span class="badge-icon">\u2714</span>\n'
            "    <span>{guarantee_type}</span>\n"
            "  </div>\n"
            '  <p class="guarantee-text">{guarantee_text}</p>\n'
            '  <a href="{terms_url}">See terms</a>\n'
            "</div>"
        ),
        copy_template="{guarantee_type}: {guarantee_text}",
        schema_markup=None,
        placement_guidance="hero_adjacent",
        archetype_relevance=["local_service", "ecommerce"],
    )


def build_media_mentions() -> TrustBlockTemplate:
    """'As Seen In' row with publication logos."""
    return TrustBlockTemplate(
        block_type=TrustBlockType.media_mentions.value,
        name="Media Mentions",
        description=(
            '"As Seen In" row with publication logos or names. Borrows '
            "authority from recognized publications. Most effective when "
            "the audience recognizes the publications."
        ),
        required_data=["publications"],
        optional_data=["mention_urls", "mention_dates"],
        html_structure=(
            '<div class="media-mentions">\n'
            "  <p>As featured in</p>\n"
            '  <div class="logo-row">\n'
            "    {publication_items}\n"
            "    <!-- Each item:\n"
            '    <span class="pub-logo">'
            '<img src="{logo_url}" alt="{publication_name}" />'
            "</span>\n"
            "    -->\n"
            "  </div>\n"
            "</div>"
        ),
        copy_template="As featured in {publication_1}, {publication_2}, and {publication_3}",
        schema_markup=None,
        placement_guidance="above_fold",
        archetype_relevance=["professional_services", "ecommerce"],
    )


def build_numbers_bar() -> TrustBlockTemplate:
    """Row of impressive numbers — projects, years, stars, etc."""
    return TrustBlockTemplate(
        block_type=TrustBlockType.numbers_bar.value,
        name="Numbers Bar",
        description=(
            "Horizontal bar of 3-5 large numbers with short descriptive "
            "labels. Communicates scale, experience, and reliability at "
            "a glance. Works on nearly every page type."
        ),
        required_data=["stat_items"],
        optional_data=["stat_icons"],
        html_structure=(
            '<div class="numbers-bar">\n'
            "  {stat_items}\n"
            "  <!-- Each item:\n"
            '  <div class="stat">\n'
            '    <span class="number">{number}+</span>\n'
            '    <span class="label">{label}</span>\n'
            "  </div>\n"
            "  -->\n"
            "</div>"
        ),
        copy_template="{number_1}+ {label_1} | {number_2} {label_2} | {number_3} {label_3}",
        schema_markup=None,
        placement_guidance="hero_adjacent",
        archetype_relevance=[],  # all archetypes
    )


# ============================================================================
# Template registry
# ============================================================================

_TEMPLATE_BUILDERS = [
    build_credentials_bar,
    build_review_aggregate,
    build_testimonial_card,
    build_case_study_snippet,
    build_team_showcase,
    build_guarantee_badge,
    build_media_mentions,
    build_numbers_bar,
]


def get_all_templates() -> List[TrustBlockTemplate]:
    """Return every built-in trust block template."""
    return [builder() for builder in _TEMPLATE_BUILDERS]


# ============================================================================
# ReviewRenderer
# ============================================================================


class ReviewRenderer:
    """Transform raw review data into multiple usable formats.

    Accepts a list of ``ReviewData`` objects and provides methods to
    curate website testimonials, build social proof graphic specs,
    compile aggregate statistics, generate review response templates,
    and extract short quotable phrases.
    """

    def __init__(self, reviews: List[ReviewData]) -> None:
        self.reviews = list(reviews)

    # ------------------------------------------------------------------
    # Website testimonials
    # ------------------------------------------------------------------

    def render_website_testimonials(
        self,
        limit: int = 5,
        min_rating: int = 4,
    ) -> List[Dict[str, Any]]:
        """Select the best reviews for website display.

        Selection criteria (applied in order):
        1. Rating >= *min_rating*.
        2. Text length between 40 and 500 characters (not too short, not
           too long).
        3. Prefer diverse service types — at most 2 reviews per type.
        4. Sort by rating descending, then by date descending.
        """
        candidates = [
            r for r in self.reviews
            if r.rating >= min_rating and 40 <= len(r.review_text) <= 500
        ]

        # Sort: highest rating first, then most recent date
        candidates.sort(key=lambda r: (r.rating, r.date), reverse=True)

        selected: List[ReviewData] = []
        service_counts: Dict[Optional[str], int] = {}

        for review in candidates:
            stype = review.service_type
            if service_counts.get(stype, 0) >= 2:
                continue
            selected.append(review)
            service_counts[stype] = service_counts.get(stype, 0) + 1
            if len(selected) >= limit:
                break

        # If diversity filtering was too aggressive, backfill
        if len(selected) < limit:
            remaining = [r for r in candidates if r not in selected]
            for review in remaining:
                selected.append(review)
                if len(selected) >= limit:
                    break

        return [
            {
                "quote": review.review_text,
                "customer_name": review.reviewer_name,
                "rating": review.rating,
                "service_type": review.service_type,
                "date": review.date,
            }
            for review in selected
        ]

    # ------------------------------------------------------------------
    # Social proof graphic
    # ------------------------------------------------------------------

    def render_social_proof_graphic(self, review: ReviewData) -> Dict[str, Any]:
        """Generate specifications for a social media graphic featuring one review.

        Returns layout parameters suitable for a design tool or Remotion
        composition — not an actual image.
        """
        # Choose layout based on text length
        text_len = len(review.review_text)
        if text_len <= 120:
            layout_type = "quote"
            font_size_suggestion = "28px"
        else:
            layout_type = "card"
            font_size_suggestion = "20px"

        star_text = "\u2605" * review.rating + "\u2606" * (5 - review.rating)

        return {
            "text_content": f'"{review.review_text}"',
            "attribution": f"\u2014 {review.reviewer_name}",
            "star_display": star_text,
            "platform": review.platform,
            "layout_type": layout_type,
            "dimensions": "1080x1080",
            "background_suggestion": (
                "Dark navy (#1a2332) or brand primary color with 90% "
                "opacity overlay"
            ),
            "font_suggestion": (
                f"Heading: Inter Bold {font_size_suggestion}; "
                "Attribution: Inter Regular 16px; "
                "Stars: 24px gold (#F5A623)"
            ),
        }

    # ------------------------------------------------------------------
    # Aggregate proof
    # ------------------------------------------------------------------

    def render_aggregate_proof(self) -> Dict[str, Any]:
        """Compile aggregate data across all loaded reviews."""
        if not self.reviews:
            return {
                "total_reviews": 0,
                "avg_rating": 0.0,
                "platform_breakdown": {},
                "star_distribution": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0},
                "headline": "No reviews yet",
            }

        total = len(self.reviews)
        avg = round(sum(r.rating for r in self.reviews) / total, 1)

        platform_breakdown: Dict[str, int] = {}
        star_dist: Dict[int, int] = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}

        for review in self.reviews:
            platform_breakdown[review.platform] = (
                platform_breakdown.get(review.platform, 0) + 1
            )
            star_dist[review.rating] = star_dist.get(review.rating, 0) + 1

        headline = f"{avg} Stars from {total} Reviews"

        return {
            "total_reviews": total,
            "avg_rating": avg,
            "platform_breakdown": platform_breakdown,
            "star_distribution": star_dist,
            "headline": headline,
        }

    # ------------------------------------------------------------------
    # Review response templates
    # ------------------------------------------------------------------

    def render_review_response_templates(self) -> Dict[str, str]:
        """Generate response templates for every review sentiment tier.

        Each template is 3-5 sentences with ``{placeholder}`` tokens for
        the business to fill in specific details.
        """
        return {
            "positive_5star": (
                "Thank you so much, {reviewer_name}! We are thrilled to "
                "hear that your experience with {service_type} exceeded "
                "expectations. Your kind words mean a lot to our team and "
                "keep us motivated to deliver our best every day. We look "
                "forward to serving you again soon!"
            ),
            "positive_4star": (
                "Thank you for the wonderful feedback, {reviewer_name}! "
                "We are glad we could deliver a great {service_type} "
                "experience for you. If there is anything we could have "
                "done to earn that fifth star, we would love to hear about "
                "it \u2014 our goal is to get better with every job. We hope "
                "to see you again!"
            ),
            "neutral_3star": (
                "Thank you for taking the time to share your feedback, "
                "{reviewer_name}. We appreciate your honesty and are sorry "
                "your experience was not everything you hoped for. We take "
                "every review seriously and would love the opportunity to "
                "understand what we can improve. Please reach out to us at "
                "{contact_email} so we can make things right."
            ),
            "negative_2star": (
                "We are sorry to hear about your experience, "
                "{reviewer_name}. This does not reflect the standard of "
                "service we hold ourselves to and we sincerely apologize "
                "for the inconvenience. We want to make this right \u2014 "
                "please contact us directly at {contact_phone} or "
                "{contact_email} and ask for {manager_name}. We are "
                "committed to resolving this for you."
            ),
            "negative_1star": (
                "We are deeply sorry for your experience, {reviewer_name}. "
                "No customer should ever feel this way after working with "
                "us and we take full responsibility. We would like to "
                "personally address your concerns and find a way to make "
                "this right. Please call us at {contact_phone} or email "
                "{contact_email} at your earliest convenience so we can "
                "resolve this directly."
            ),
        }

    # ------------------------------------------------------------------
    # Curate by service type
    # ------------------------------------------------------------------

    def curate_by_service(
        self,
        service_type: str,
        limit: int = 3,
    ) -> List[ReviewData]:
        """Return reviews filtered by *service_type*, sorted by rating then recency."""
        matches = [
            r for r in self.reviews
            if r.service_type and r.service_type.lower() == service_type.lower()
        ]
        matches.sort(key=lambda r: (r.rating, r.date), reverse=True)
        return matches[:limit]

    # ------------------------------------------------------------------
    # Best short quotes
    # ------------------------------------------------------------------

    def get_best_quotes(
        self,
        max_words: int = 30,
        limit: int = 10,
    ) -> List[str]:
        """Extract the best short quotes from reviews.

        Prefers quotes with specific details (numbers, names, or strong
        emotional language) over generic praise.
        """
        candidates: List[Dict[str, Any]] = []

        # Signals of a strong, specific quote
        specificity_patterns = [
            re.compile(r"\d+"),                    # contains numbers
            re.compile(r"\$"),                     # mentions money
            re.compile(r"saved|fixed|solved|helped|transformed|changed", re.IGNORECASE),
            re.compile(r"best|amazing|incredible|fantastic|perfect|exceeded", re.IGNORECASE),
            re.compile(r"years?|months?|weeks?|days?", re.IGNORECASE),  # time references
            re.compile(r"recommend", re.IGNORECASE),
            re.compile(r"never|always|every time", re.IGNORECASE),
        ]

        for review in self.reviews:
            text = review.review_text.strip()
            words = text.split()
            if not words or len(words) > max_words:
                continue

            # Score specificity
            score = 0
            for pattern in specificity_patterns:
                if pattern.search(text):
                    score += 1

            # Bonus for higher rating
            score += review.rating

            # Bonus for verified
            if review.verified:
                score += 1

            # Penalty for very short or generic text
            if len(words) < 5:
                score -= 2

            candidates.append({"text": text, "score": score})

        # Sort by score descending
        candidates.sort(key=lambda c: c["score"], reverse=True)

        return [c["text"] for c in candidates[:limit]]


# ============================================================================
# Trust block selection engine
# ============================================================================

# Optimal ordering by page type.  Each value is a list of TrustBlockType
# values in recommended display order.
_PAGE_TYPE_ORDER: Dict[str, List[str]] = {
    "homepage": [
        TrustBlockType.review_aggregate.value,
        TrustBlockType.numbers_bar.value,
        TrustBlockType.testimonial_card.value,
        TrustBlockType.credentials_bar.value,
        TrustBlockType.media_mentions.value,
        TrustBlockType.case_study_snippet.value,
        TrustBlockType.guarantee_badge.value,
        TrustBlockType.team_showcase.value,
    ],
    "service_page": [
        TrustBlockType.testimonial_card.value,
        TrustBlockType.case_study_snippet.value,
        TrustBlockType.guarantee_badge.value,
        TrustBlockType.review_aggregate.value,
        TrustBlockType.numbers_bar.value,
        TrustBlockType.credentials_bar.value,
        TrustBlockType.media_mentions.value,
        TrustBlockType.team_showcase.value,
    ],
    "landing_page": [
        TrustBlockType.review_aggregate.value,
        TrustBlockType.testimonial_card.value,
        TrustBlockType.guarantee_badge.value,
        TrustBlockType.numbers_bar.value,
        TrustBlockType.credentials_bar.value,
        TrustBlockType.case_study_snippet.value,
        TrustBlockType.media_mentions.value,
        TrustBlockType.team_showcase.value,
    ],
    "about_page": [
        TrustBlockType.team_showcase.value,
        TrustBlockType.media_mentions.value,
        TrustBlockType.credentials_bar.value,
        TrustBlockType.numbers_bar.value,
        TrustBlockType.review_aggregate.value,
        TrustBlockType.testimonial_card.value,
        TrustBlockType.case_study_snippet.value,
        TrustBlockType.guarantee_badge.value,
    ],
}

# Map from block_type to the set of required_data field names.
# Built lazily on first call.
_TEMPLATE_INDEX: Optional[Dict[str, TrustBlockTemplate]] = None


def _get_template_index() -> Dict[str, TrustBlockTemplate]:
    """Return (and cache) a dict keyed by ``block_type``."""
    global _TEMPLATE_INDEX  # noqa: PLW0603
    if _TEMPLATE_INDEX is None:
        _TEMPLATE_INDEX = {t.block_type: t for t in get_all_templates()}
    return _TEMPLATE_INDEX


# Mapping: each required_data token to the ``available_data`` key the
# caller should set to ``True`` to indicate they have that data.  This
# allows ``select_trust_blocks`` to match caller-supplied availability
# flags against each template's ``required_data``.
_DATA_KEY_ALIASES: Dict[str, List[str]] = {
    "business_name": ["business_name"],
    "credentials": ["credentials", "certifications", "licenses"],
    "license_numbers": ["license_numbers", "licenses"],
    "review_count": ["review_count", "reviews"],
    "avg_rating": ["avg_rating", "reviews"],
    "review_platform": ["review_platform", "reviews"],
    "quote_text": ["quote_text", "testimonials", "reviews"],
    "customer_name": ["customer_name", "testimonials", "reviews"],
    "problem": ["problem", "case_studies"],
    "solution": ["solution", "case_studies"],
    "result": ["result", "case_studies"],
    "team_members": ["team_members", "team"],
    "guarantee_text": ["guarantee_text", "guarantee"],
    "guarantee_type": ["guarantee_type", "guarantee"],
    "publications": ["publications", "media_mentions"],
    "stat_items": ["stat_items", "numbers", "stats"],
}


def _data_available(required_data: List[str], available_data: Dict[str, bool]) -> bool:
    """Check whether all *required_data* tokens can be satisfied.

    Each token is checked against its aliases in ``_DATA_KEY_ALIASES``.
    If any alias evaluates to ``True`` in *available_data*, the
    requirement is satisfied.
    """
    for token in required_data:
        aliases = _DATA_KEY_ALIASES.get(token, [token])
        if not any(available_data.get(alias, False) for alias in aliases):
            return False
    return True


def select_trust_blocks(
    page_type: str,
    archetype: str,
    available_data: Dict[str, bool],
) -> List[TrustBlockTemplate]:
    """Return an ordered list of recommended trust blocks for a page.

    Parameters
    ----------
    page_type:
        One of ``"homepage"``, ``"service_page"``, ``"landing_page"``,
        ``"about_page"``.  Unknown page types fall back to the homepage
        ordering.
    archetype:
        Business archetype (e.g. ``"local_service"``).  Used to boost
        relevance of archetype-specific blocks.
    available_data:
        Dict mapping data-availability flags to ``True``/``False``.
        Only blocks whose ``required_data`` is fully satisfiable are
        returned.

    Returns
    -------
    list[TrustBlockTemplate]
        Templates in recommended display order (most impactful first).
        Only templates whose required data is available are included.
    """
    index = _get_template_index()
    order = _PAGE_TYPE_ORDER.get(page_type, _PAGE_TYPE_ORDER["homepage"])

    results: List[TrustBlockTemplate] = []

    for block_type in order:
        template = index.get(block_type)
        if template is None:
            continue

        # Check data availability
        if not _data_available(template.required_data, available_data):
            continue

        # Check archetype relevance (empty list means all archetypes)
        if template.archetype_relevance and archetype not in template.archetype_relevance:
            continue

        results.append(template)

    return results
