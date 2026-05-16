"""Local business claymation ad pipeline.

This module turns local business lead records into a dry-run creative wedge:
weak creative scoring, sample ad concept, tool handoff, outbound pitch copy,
and retainer package recommendation.

The functions are pure and do not call external services. Asset generation,
animation, voiceover, editing, and outbound sends happen only after a human
approves the dry-run output.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


LEAD_STATUSES = [
    "sourced",
    "qualified",
    "sample_created",
    "contacted",
    "replied",
    "booked",
    "closed",
    "fulfilled",
    "nurture",
    "disqualified",
]


WEAK_AD_SIGNALS: Dict[str, Dict[str, Any]] = {
    "no_video_creative": {
        "points": 3,
        "patterns": ["no video", "static only", "no reels", "no short-form", "photo only"],
        "label": "No clear short-form video creative.",
    },
    "generic_stock_visuals": {
        "points": 3,
        "patterns": ["stock", "generic", "template", "same as everyone", "bland"],
        "label": "Creative looks interchangeable.",
    },
    "weak_cta": {
        "points": 2,
        "patterns": ["weak cta", "no cta", "unclear cta", "no call to action"],
        "label": "Call to action is unclear.",
    },
    "poor_offer_clarity": {
        "points": 2,
        "patterns": ["unclear offer", "no offer", "hard to tell", "confusing offer"],
        "label": "Offer is not obvious.",
    },
    "no_local_specificity": {
        "points": 2,
        "patterns": ["no local", "not local", "no city", "no neighborhood", "generic location"],
        "label": "Creative lacks local proof.",
    },
    "stale_creative": {
        "points": 2,
        "patterns": ["stale", "old", "inactive", "hasn't posted", "has not posted"],
        "label": "Creative looks stale.",
    },
    "low_production_quality": {
        "points": 2,
        "patterns": ["bad crop", "low quality", "hard to read", "rough edit", "bad audio"],
        "label": "Production quality is weak.",
    },
}


TOOL_HANDOFF = {
    "concept": {
        "tool": "Claude",
        "output": "concept angle, storyboard, script, shot list, voiceover copy, CTA",
    },
    "frames": {
        "tool": "Fal.ai or image model",
        "output": "clay-style key frames with prompts and seed notes",
    },
    "animation": {
        "tool": "Kling AI or video model",
        "output": "4-8 second motion clips for each scene",
    },
    "voiceover": {
        "tool": "ElevenLabs or local TTS",
        "output": "single narration track plus per-scene timing",
    },
    "editing": {
        "tool": "CapCut or Remotion",
        "output": "assembled vertical video with captions, music bed, and CTA end card",
    },
}


@dataclass
class ClaymationLead:
    """Normalized local business lead for the claymation ad workflow."""

    name: str
    category: str
    city: str = ""
    state: str = ""
    website: str = ""
    phone: str = ""
    email: str = ""
    contact_url: str = ""
    address: str = ""
    rating: Optional[float] = None
    reviews: int = 0
    social_links: Dict[str, str] = field(default_factory=dict)
    ad_observations: List[str] = field(default_factory=list)
    status: str = "sourced"
    notes: str = ""

    @classmethod
    def from_mapping(cls, data: Dict[str, Any]) -> "ClaymationLead":
        """Create a lead from CSV/JSON-style data."""
        social_links = data.get("social_links") or {}
        if not isinstance(social_links, dict):
            social_links = {}
        for key in ("facebook", "instagram", "tiktok", "youtube", "linkedin"):
            if data.get(key):
                social_links[key] = str(data[key])

        observations = data.get("ad_observations") or data.get("observations") or []
        if isinstance(observations, str):
            observations = [part.strip() for part in observations.replace("|", ";").split(";") if part.strip()]

        rating = _as_float(data.get("rating"))
        reviews = _as_int(data.get("reviews") or data.get("review_count"))
        status = str(data.get("status") or "sourced")
        if status not in LEAD_STATUSES:
            status = "sourced"

        return cls(
            name=str(data.get("name") or data.get("business_name") or "").strip(),
            category=str(data.get("category") or data.get("niche") or "").strip(),
            city=str(data.get("city") or "").strip(),
            state=str(data.get("state") or "").strip(),
            website=str(data.get("website") or "").strip(),
            phone=str(data.get("phone") or "").strip(),
            email=str(data.get("email") or "").strip(),
            contact_url=str(data.get("contact_url") or data.get("contact") or "").strip(),
            address=str(data.get("address") or "").strip(),
            rating=rating,
            reviews=reviews,
            social_links=social_links,
            ad_observations=list(observations),
            status=status,
            notes=str(data.get("notes") or "").strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WeakAdScore:
    """Scored creative opportunity for a local lead."""

    score: int
    band: str
    signals: List[Dict[str, Any]]
    opportunity_note: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClaymationAdConcept:
    """Dry-run ad concept package."""

    angle: str
    storyboard: List[Dict[str, Any]]
    script: str
    shot_list: List[str]
    voiceover_copy: str
    cta: str
    frame_prompts: List[str]
    animation_plan: List[Dict[str, str]]
    editing_notes: List[str]
    tool_handoff: Dict[str, Dict[str, str]] = field(default_factory=lambda: TOOL_HANDOFF.copy())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OutboundPitchPackage:
    """Channel-specific pitch copy for the sample ad wedge."""

    email_subject: str
    email_body: str
    sms: str
    instagram_dm: str
    cold_call_opener: str
    recommended_package: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def score_weak_ad_opportunity(lead: ClaymationLead) -> WeakAdScore:
    """Score a lead for weak creative and sample-ad fit."""
    haystack = " ".join(lead.ad_observations + [lead.notes]).lower()
    signals: List[Dict[str, Any]] = []
    score = 0

    for signal_id, config in WEAK_AD_SIGNALS.items():
        if any(pattern in haystack for pattern in config["patterns"]):
            points = int(config["points"])
            score += points
            signals.append({"id": signal_id, "points": points, "label": config["label"]})

    if not lead.social_links:
        score += 1
        signals.append({
            "id": "missing_social_links",
            "points": 1,
            "label": "No social links are captured yet; discovery needs follow-up.",
        })

    if lead.rating and lead.rating >= 4.5 and lead.reviews >= 50 and score >= 4:
        score += 3
        signals.append({
            "id": "strong_reviews_weak_ads",
            "points": 3,
            "label": "Strong reviews can become proof inside the ad.",
        })

    band = _score_band(score)
    location = ", ".join(part for part in [lead.city, lead.state] if part)
    where = f" in {location}" if location else ""
    note = (
        f"{lead.name} is a {band} target{where}: "
        f"{_signal_summary(signals) if signals else 'no major creative gap has been recorded yet'}."
    )
    return WeakAdScore(score=score, band=band, signals=signals, opportunity_note=note)


def generate_claymation_ad_concept(
    lead: ClaymationLead,
    *,
    offer: Optional[str] = None,
    duration_seconds: int = 30,
) -> ClaymationAdConcept:
    """Generate a deterministic sample ad concept from lead data."""
    category = lead.category or "local business"
    location = _format_location(lead)
    offer_text = offer or _default_offer(category)
    hero = _category_hero(category)
    pain = _category_pain(category)
    cta = _default_cta(category)
    duration_seconds = max(15, min(duration_seconds, 45))

    angle = f"A clay-style {category} mini-story where {hero} fixes {pain} with {lead.name}."
    storyboard = [
        {
            "scene": "hook",
            "duration_seconds": 5,
            "visual": f"A tiny clay {hero} looks frustrated while scrolling past boring local ads.",
            "voiceover": f"{location} has plenty of options. Most ads still look the same.",
        },
        {
            "scene": "problem",
            "duration_seconds": 7,
            "visual": f"The clay character tries a generic solution and the scene flattens into gray paper.",
            "voiceover": f"When the offer is not clear, people keep scrolling.",
        },
        {
            "scene": "solution",
            "duration_seconds": 10,
            "visual": f"{lead.name} pops into a bright clay set with staff, product, and local details.",
            "voiceover": f"{lead.name} makes the choice feel simple: {offer_text}.",
        },
        {
            "scene": "proof",
            "duration_seconds": 5,
            "visual": "Clay review stars stack into a sign while the product or service is shown.",
            "voiceover": _proof_line(lead),
        },
        {
            "scene": "cta",
            "duration_seconds": max(3, duration_seconds - 27),
            "visual": "A clay phone, map pin, and booking button slide into frame.",
            "voiceover": cta,
        },
    ]

    script = "\n".join(f"{idx + 1}. {item['voiceover']}" for idx, item in enumerate(storyboard))
    shot_list = [
        "Vertical 9:16 clay world opener with local cue.",
        "Close-up on the problem moment.",
        "Hero product or service reveal.",
        "Proof card using reviews, staff, location, or offer detail.",
        "CTA end card with phone, booking URL, or map pin.",
    ]
    frame_prompts = [
        f"Claymation-style vertical ad frame for {lead.name}, {category}, {location}; {item['visual']} Soft studio lighting, handmade clay texture, readable negative space."
        for item in storyboard
    ]
    animation_plan = [
        {
            "scene": item["scene"],
            "motion": "subtle clay character movement, camera push, object pop-in, no fast cuts",
        }
        for item in storyboard
    ]
    editing_notes = [
        "Use large captions with one short phrase per beat.",
        "Keep brand colors if available; otherwise use warm local-service colors.",
        "End with one CTA only.",
        "Export a dry-run assembly plan before generating paid assets.",
    ]

    return ClaymationAdConcept(
        angle=angle,
        storyboard=storyboard,
        script=script,
        shot_list=shot_list,
        voiceover_copy=" ".join(item["voiceover"] for item in storyboard),
        cta=cta,
        frame_prompts=frame_prompts,
        animation_plan=animation_plan,
        editing_notes=editing_notes,
    )


def generate_outbound_pitch(
    lead: ClaymationLead,
    score: WeakAdScore,
    concept: ClaymationAdConcept,
    *,
    sample_url: Optional[str] = None,
) -> OutboundPitchPackage:
    """Generate pitch copy from lead, score, and sample concept."""
    first_line = _personal_observation(lead, score)
    sample_line = (
        f"I made a sample direction here: {sample_url}"
        if sample_url
        else "I mocked up a sample direction before making any paid assets."
    )
    package = "Growth 4 videos/month" if score.score >= 12 else "Starter 2 videos/month"

    email_subject = f"Sample video idea for {lead.name}"
    email_body = (
        f"Hey {lead.name} team,\n\n"
        f"{first_line}\n\n"
        f"{sample_line}\n\n"
        f"The idea: {concept.angle}\n\n"
        f"If this is useful, I can turn the same system into {package.lower()} with fresh hooks, captions, and edits each month.\n\n"
        f"Want me to send the first 20-30 second sample plan?"
    )
    sms = (
        f"Hi {lead.name} - I put together a clay-style video ad idea based on your local offer. "
        f"Want me to send the sample plan?"
    )
    instagram_dm = (
        f"Quick idea for {lead.name}: a clay-style short ad built around {concept.cta.lower()} "
        f"Could I send the sample storyboard?"
    )
    cold_call_opener = (
        f"Hi, this is Connor. I had a specific ad idea for {lead.name}, "
        f"not a generic marketing pitch. Who handles your short video ads?"
    )

    return OutboundPitchPackage(
        email_subject=email_subject,
        email_body=email_body,
        sms=sms,
        instagram_dm=instagram_dm,
        cold_call_opener=cold_call_opener,
        recommended_package=package,
    )


def build_retainer_packages() -> List[Dict[str, Any]]:
    """Return the standard 2-video and 4-video monthly package templates."""
    return [
        {
            "name": "Starter",
            "videos_per_month": 2,
            "best_for": "Small local businesses that need consistent creative.",
            "deliverables": [
                "2 short videos",
                "2 hooks per video",
                "captions and CTA copy",
                "1 revision pass",
                "monthly creative report",
            ],
        },
        {
            "name": "Growth",
            "videos_per_month": 4,
            "best_for": "Businesses with active promotions or paid ads.",
            "deliverables": [
                "4 short videos",
                "3 hooks per video",
                "platform-specific crops",
                "2 revision passes",
                "monthly creative report",
                "quarterly offer refresh",
            ],
        },
    ]


def run_dry_run(
    leads: Iterable[ClaymationLead],
    *,
    sample_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the full claymation workflow without external side effects."""
    items = []
    for lead in leads:
        score = score_weak_ad_opportunity(lead)
        concept = generate_claymation_ad_concept(lead)
        pitch = generate_outbound_pitch(lead, score, concept, sample_url=sample_url)
        items.append({
            "lead": lead.to_dict(),
            "score": score.to_dict(),
            "concept": concept.to_dict(),
            "pitch": pitch.to_dict(),
            "next_status": "qualified" if score.score >= 8 else "nurture",
        })

    return {
        "dry_run": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "external_side_effects": [],
        "tool_handoff": TOOL_HANDOFF,
        "retainer_packages": build_retainer_packages(),
        "items": items,
    }


def _as_float(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int:
    try:
        if value in (None, ""):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _score_band(score: int) -> str:
    if score >= 12:
        return "sample-worthy"
    if score >= 8:
        return "good"
    if score >= 4:
        return "monitor"
    return "poor-fit"


def _signal_summary(signals: List[Dict[str, Any]]) -> str:
    labels = [signal["label"].rstrip(".") for signal in signals[:3]]
    if len(signals) > 3:
        labels.append(f"{len(signals) - 3} more signals")
    return "; ".join(labels)


def _format_location(lead: ClaymationLead) -> str:
    location = ", ".join(part for part in [lead.city, lead.state] if part)
    return location or "the local market"


def _default_offer(category: str) -> str:
    lower = category.lower()
    if any(word in lower for word in ["gym", "fitness", "studio"]):
        return "book a trial class this week"
    if any(word in lower for word in ["restaurant", "cafe", "bakery", "food"]):
        return "try the special that locals keep coming back for"
    if any(word in lower for word in ["salon", "spa", "barber", "med spa"]):
        return "claim a first-visit appointment"
    if any(word in lower for word in ["plumber", "hvac", "roof", "electric"]):
        return "book a fast local estimate"
    return "book the next step today"


def _default_cta(category: str) -> str:
    lower = category.lower()
    if any(word in lower for word in ["restaurant", "cafe", "bakery", "food"]):
        return "Stop in today or order online."
    if any(word in lower for word in ["gym", "fitness", "studio", "salon", "spa"]):
        return "Book your first visit today."
    if any(word in lower for word in ["plumber", "hvac", "roof", "electric"]):
        return "Call now for a local estimate."
    return "Message the team today."


def _category_hero(category: str) -> str:
    lower = category.lower()
    if "gym" in lower or "fitness" in lower:
        return "neighbor walking into a class"
    if "restaurant" in lower or "cafe" in lower or "bakery" in lower:
        return "hungry neighbor finding a table"
    if "salon" in lower or "spa" in lower:
        return "client seeing a fresh look in the mirror"
    if "plumber" in lower or "hvac" in lower or "electric" in lower:
        return "homeowner finding fast help"
    return "local customer finding the right place"


def _category_pain(category: str) -> str:
    lower = category.lower()
    if "gym" in lower or "fitness" in lower:
        return "choosing a studio from a feed full of identical workouts"
    if "restaurant" in lower or "cafe" in lower or "bakery" in lower:
        return "deciding where to eat from dull food posts"
    if "salon" in lower or "spa" in lower:
        return "trusting someone new with a personal appointment"
    if "plumber" in lower or "hvac" in lower or "electric" in lower:
        return "finding a reliable pro before the problem gets worse"
    return "picking a local business from a crowded feed"


def _proof_line(lead: ClaymationLead) -> str:
    if lead.rating and lead.reviews:
        return f"With {lead.rating:g} stars across {lead.reviews} reviews, the proof is already there."
    if lead.rating:
        return f"The local proof starts with a {lead.rating:g}-star reputation."
    return "The best proof is a clear look at what customers get."


def _personal_observation(lead: ClaymationLead, score: WeakAdScore) -> str:
    location = _format_location(lead)
    if score.signals:
        return (
            f"I noticed {lead.name} has local proof in {location}, "
            f"but the creative opportunity is pretty clear: {score.signals[0]['label'].rstrip('.').lower()}."
        )
    return f"I found {lead.name} while looking for local businesses in {location} that could use stronger short-form video."
