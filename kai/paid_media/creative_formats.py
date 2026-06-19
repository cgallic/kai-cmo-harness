"""Canonical paid-media creative format library and selection helpers.

This module gives Kai a reusable taxonomy for paid-social and short-form ad
formats.  The library powers selection by platform, funnel stage, available
assets, and compliance risk so `/kai-ad-campaign` can choose concrete formats
instead of generic creative categories alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


PASS = "PASS"
FAIL = "FAIL"
NEEDS_ASSET = "NEEDS_ASSET"
REVIEW = "REVIEW"


@dataclass(frozen=True)
class CreativeFormatDefinition:
    """One canonical ad creative format in the paid-media library."""

    id: str
    name: str
    category: str
    production_style: str
    funnel_stages: Tuple[str, ...]
    platforms: Tuple[str, ...]
    proof_types: Tuple[str, ...]
    required_assets: Tuple[str, ...]
    optional_assets: Tuple[str, ...]
    why_it_works: str
    prompt_template: str
    compliance_flags: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CreativeFormatSelection:
    """Selection result for a creative format against current constraints."""

    definition: CreativeFormatDefinition
    platform_fit: str
    funnel_fit: str
    asset_feasibility: str
    compliance_status: str
    missing_assets: Tuple[str, ...]
    compliance_flags: Tuple[str, ...]
    score: int


PLATFORM_ALIASES: Dict[str, Tuple[str, ...]] = {
    "meta": ("meta", "facebook", "instagram", "reels", "stories"),
    "meta_reels": ("meta", "instagram", "reels", "stories"),
    "tiktok": ("tiktok",),
    "youtube_shorts": ("youtube", "youtube_shorts", "shorts"),
    "linkedin": ("linkedin",),
    "display_native": ("display_native", "display", "native"),
}

REGULATED_FLAGS = {
    "before_after_restricted",
    "transformation_claim",
    "testimonial_substantiation",
    "financial_or_health_claim",
}


def _format(
    *,
    id: str,
    name: str,
    category: str,
    production_style: str,
    funnel_stages: Sequence[str],
    platforms: Sequence[str],
    proof_types: Sequence[str],
    required_assets: Sequence[str],
    optional_assets: Sequence[str],
    why_it_works: str,
    prompt_template: str,
    compliance_flags: Sequence[str] = (),
) -> CreativeFormatDefinition:
    return CreativeFormatDefinition(
        id=id,
        name=name,
        category=category,
        production_style=production_style,
        funnel_stages=tuple(funnel_stages),
        platforms=tuple(platforms),
        proof_types=tuple(proof_types),
        required_assets=tuple(required_assets),
        optional_assets=tuple(optional_assets),
        why_it_works=why_it_works,
        prompt_template=prompt_template,
        compliance_flags=tuple(compliance_flags),
    )


CREATIVE_FORMAT_LIBRARY: Tuple[CreativeFormatDefinition, ...] = (
    _format(
        id="talking_head",
        name="Talking Head",
        category="founder_expert",
        production_style="face_to_camera",
        funnel_stages=("tof", "mof"),
        platforms=("meta", "tiktok", "youtube_shorts", "linkedin"),
        proof_types=("founder", "expert", "mechanism"),
        required_assets=("founder_footage",),
        optional_assets=("captions", "b_roll"),
        why_it_works="Direct face time builds trust and makes the hook feel native.",
        prompt_template="Open with a sharp hook to camera, then explain the mechanism in plain language.",
    ),
    _format(
        id="walk_and_talk",
        name="Walk and Talk",
        category="founder_expert",
        production_style="mobile_native",
        funnel_stages=("tof",),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("founder", "story"),
        required_assets=("founder_footage",),
        optional_assets=("outdoor_b_roll", "captions"),
        why_it_works="Movement adds pattern interruption without making the ad feel overproduced.",
        prompt_template="Start mid-stride with the problem, then deliver one clear takeaway while walking.",
    ),
    _format(
        id="ugc_unboxing",
        name="UGC Unboxing",
        category="ugc",
        production_style="creator_native",
        funnel_stages=("tof", "mof"),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("demo", "reaction"),
        required_assets=("ugc_creator", "product_sample"),
        optional_assets=("captions", "usage_rights"),
        why_it_works="The reveal and first reaction compress curiosity and product proof into one asset.",
        prompt_template="Show the package opening first, then capture first-touch reactions and one outcome claim.",
        compliance_flags=("creator_rights",),
    ),
    _format(
        id="native_try_on",
        name="Native Try-On",
        category="ugc",
        production_style="creator_native",
        funnel_stages=("tof", "mof"),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("demo", "transformation"),
        required_assets=("ugc_creator", "product_sample"),
        optional_assets=("mirror_shot", "captions"),
        why_it_works="Fast in-use proof helps buyers imagine themselves using the product.",
        prompt_template="Lead with the product in hand, then show the try-on and one immediate reaction.",
        compliance_flags=("creator_rights", "before_after_restricted"),
    ),
    _format(
        id="vlog",
        name="Vlog",
        category="lifestyle",
        production_style="day_in_life",
        funnel_stages=("tof",),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("lifestyle", "story"),
        required_assets=("creator_day_in_life",),
        optional_assets=("product_sample", "captions"),
        why_it_works="The diary feel lowers resistance and makes the brand part of a broader routine.",
        prompt_template="Narrate a real moment, then slip the product into the routine without breaking the scene.",
        compliance_flags=("creator_rights",),
    ),
    _format(
        id="asmr",
        name="ASMR",
        category="sensory",
        production_style="closeup_sensory",
        funnel_stages=("tof",),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("demo",),
        required_assets=("product_closeups",),
        optional_assets=("foley_audio", "macro_shots"),
        why_it_works="Sensory detail buys extra watch time and makes the asset stand out in feed.",
        prompt_template="Focus on satisfying sounds and closeups while keeping captions simple and product-led.",
    ),
    _format(
        id="pov_faceless",
        name="POV Faceless",
        category="pov",
        production_style="hands_only",
        funnel_stages=("tof", "mof"),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("demo", "story"),
        required_assets=("hands_on_demo",),
        optional_assets=("voiceover", "captions"),
        why_it_works="POV keeps the ad native even when the brand has no strong on-camera spokesperson.",
        prompt_template="Frame the scene as the viewer's own experience and narrate the problem from first person.",
    ),
    _format(
        id="native_lifestyle",
        name="Native Lifestyle",
        category="lifestyle",
        production_style="social_native",
        funnel_stages=("tof",),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("lifestyle", "aspiration"),
        required_assets=("lifestyle_b_roll",),
        optional_assets=("creator_voiceover", "captions"),
        why_it_works="Lifestyle framing sells the identity and context around the product, not just the SKU.",
        prompt_template="Lead with the desired scene, then show the product as the obvious supporting tool.",
    ),
    _format(
        id="skit",
        name="Skit",
        category="story",
        production_style="scene_based",
        funnel_stages=("tof",),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("story", "contrast"),
        required_assets=("actors",),
        optional_assets=("props", "captions"),
        why_it_works="Short scenes dramatize the pain quickly and can carry heavier contrast angles.",
        prompt_template="Write a two-scene setup and payoff where the problem is obvious before the offer appears.",
    ),
    _format(
        id="meme",
        name="Meme",
        category="pattern_interrupt",
        production_style="trend_native",
        funnel_stages=("tof",),
        platforms=("meta", "tiktok"),
        proof_types=("contrast", "humor"),
        required_assets=("trend_reference",),
        optional_assets=("captions", "soundtrack"),
        why_it_works="Borrowed format recognition can win the first second when the joke matches the pain point.",
        prompt_template="Use a familiar meme structure to frame the problem, then pivot into the offer.",
    ),
    _format(
        id="ugly_ad",
        name="Ugly Ad",
        category="pattern_interrupt",
        production_style="deliberately_raw",
        funnel_stages=("tof",),
        platforms=("meta", "tiktok", "display_native"),
        proof_types=("offer", "contrast"),
        required_assets=("offer_copy",),
        optional_assets=("rough_graphics",),
        why_it_works="Messy visuals can outperform polished ads when they feel more like a discovery than an ad.",
        prompt_template="Use blunt text and rough framing to state the problem, proof, and offer with zero polish.",
    ),
    _format(
        id="ai_real_mashup",
        name="AI + Real Mashup",
        category="hybrid",
        production_style="synthetic_plus_real",
        funnel_stages=("tof",),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("story", "visual_metaphor"),
        required_assets=("real_footage", "ai_generated_frames"),
        optional_assets=("voiceover",),
        why_it_works="The format buys attention with novelty while keeping enough real footage to ground trust.",
        prompt_template="Start with a surreal AI visual, then cut to the real product and practical proof.",
        compliance_flags=("ai_disclosure",),
    ),
    _format(
        id="pattern_interrupt",
        name="Pattern Interrupt",
        category="pattern_interrupt",
        production_style="hook_first",
        funnel_stages=("tof",),
        platforms=("meta", "tiktok", "youtube_shorts", "display_native"),
        proof_types=("contrast", "problem"),
        required_assets=("hook_visual",),
        optional_assets=("captions",),
        why_it_works="The asset is designed to win the first stop before it earns the right to explain.",
        prompt_template="Open on the unexpected visual or line first, then reveal why it matters to the buyer.",
    ),
    _format(
        id="staged_organic_moment",
        name="Staged Organic Moment",
        category="ugc",
        production_style="fake_spontaneous",
        funnel_stages=("tof",),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("story", "reaction"),
        required_assets=("creator_scene",),
        optional_assets=("captions",),
        why_it_works="A rehearsed but plausible moment gives the ad native pacing without full improvisation.",
        prompt_template="Script a believable candid moment where the product solves a problem in real time.",
        compliance_flags=("creator_rights",),
    ),
    _format(
        id="native_testimonial",
        name="Native Testimonial",
        category="social_proof",
        production_style="customer_native",
        funnel_stages=("mof", "bof"),
        platforms=("meta", "tiktok", "youtube_shorts", "linkedin"),
        proof_types=("testimonial",),
        required_assets=("customer_testimonial",),
        optional_assets=("usage_rights", "captions"),
        why_it_works="A believable first-person claim lowers risk when the buyer is evaluating options.",
        prompt_template="Lead with the strongest customer quote, then tie it back to one clear objection.",
        compliance_flags=("testimonial_substantiation",),
    ),
    _format(
        id="street_interview",
        name="Street Interview",
        category="social_proof",
        production_style="vox_pop",
        funnel_stages=("tof", "mof"),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("social_proof", "reaction"),
        required_assets=("interviewer", "public_interviews"),
        optional_assets=("captions",),
        why_it_works="Fast reactions and multiple voices create a dense proof package quickly.",
        prompt_template="Ask one simple question that reveals the pain or desired outcome, then stitch the best answers.",
        compliance_flags=("creator_rights",),
    ),
    _format(
        id="founder",
        name="Founder",
        category="founder_expert",
        production_style="face_to_camera",
        funnel_stages=("mof", "bof"),
        platforms=("meta", "tiktok", "youtube_shorts", "linkedin"),
        proof_types=("founder", "mechanism", "story"),
        required_assets=("founder_footage",),
        optional_assets=("customer_quote", "captions"),
        why_it_works="Founder presence is high-trust when the offer needs context, authority, or conviction.",
        prompt_template="Have the founder explain the problem origin, the mechanism, and the CTA in one take.",
    ),
    _format(
        id="podcast_clip",
        name="Podcast Clip",
        category="expert",
        production_style="longform_excerpt",
        funnel_stages=("mof",),
        platforms=("meta", "youtube_shorts", "linkedin"),
        proof_types=("expert", "mechanism"),
        required_assets=("podcast_video",),
        optional_assets=("subtitles",),
        why_it_works="Repurposed long-form authority works when the buyer needs depth, not just a flashy hook.",
        prompt_template="Pull the 20-30 second answer where the speaker names the problem and a non-obvious insight.",
    ),
    _format(
        id="social_proof_mashup",
        name="Social Proof Mashup",
        category="social_proof",
        production_style="proof_compilation",
        funnel_stages=("mof", "bof"),
        platforms=("meta", "tiktok", "youtube_shorts", "linkedin", "display_native"),
        proof_types=("review", "testimonial", "ugc"),
        required_assets=("reviews",),
        optional_assets=("ugc_creator", "star_rating_graphic"),
        why_it_works="Proof density lets the buyer infer consensus fast.",
        prompt_template="Compile the strongest reviews or clips around one buyer objection and close with the offer.",
        compliance_flags=("testimonial_substantiation",),
    ),
    _format(
        id="expert_explainer",
        name="Expert Explainer",
        category="expert",
        production_style="teaching",
        funnel_stages=("mof", "bof"),
        platforms=("meta", "youtube_shorts", "linkedin"),
        proof_types=("expert", "mechanism", "data"),
        required_assets=("subject_matter_expert",),
        optional_assets=("slides", "screen_recording"),
        why_it_works="Teaching reduces skepticism when the buyer needs clear reasoning before taking action.",
        prompt_template="State the problem plainly, explain the mechanism, then connect it to the offer or next step.",
        compliance_flags=("financial_or_health_claim",),
    ),
    _format(
        id="dead_simple_how_to",
        name="Dead Simple How-To",
        category="education",
        production_style="step_by_step",
        funnel_stages=("tof", "mof"),
        platforms=("meta", "tiktok", "youtube_shorts", "linkedin"),
        proof_types=("mechanism", "demo"),
        required_assets=("step_demo",),
        optional_assets=("captions", "screen_recording"),
        why_it_works="The quick-win structure earns attention by delivering a usable insight immediately.",
        prompt_template="Teach one small thing first, then show how the product shortens or improves the process.",
    ),
    _format(
        id="mystical_curiosity",
        name="Mystical / Curiosity-Led",
        category="curiosity",
        production_style="intrigue",
        funnel_stages=("tof",),
        platforms=("meta", "tiktok", "youtube_shorts", "display_native"),
        proof_types=("curiosity", "contrast"),
        required_assets=("curiosity_hook",),
        optional_assets=("symbolic_visuals",),
        why_it_works="Curiosity-led framing can win weak-awareness audiences when the claim is restrained.",
        prompt_template="Use an intriguing observation or mystery, then bridge into the practical takeaway.",
    ),
    _format(
        id="comment_response",
        name="Comment Response",
        category="social_proof",
        production_style="reply_native",
        funnel_stages=("mof", "bof"),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("objection_handling", "expert"),
        required_assets=("real_comment",),
        optional_assets=("founder_footage", "screen_capture"),
        why_it_works="Replying to a real objection makes the asset feel contextual and timely.",
        prompt_template="Put the real comment on screen first, then answer it directly with proof or demo.",
    ),
    _format(
        id="visual_explainer",
        name="Visual Explainer",
        category="education",
        production_style="graphic_led",
        funnel_stages=("mof",),
        platforms=("meta", "youtube_shorts", "linkedin", "display_native"),
        proof_types=("mechanism", "data"),
        required_assets=("graphics",),
        optional_assets=("voiceover", "screen_recording"),
        why_it_works="Graphics can simplify a harder-to-see mechanism or workflow faster than talking alone.",
        prompt_template="Use one visual frame per idea and keep each frame tied to the buyer's decision.",
        compliance_flags=("financial_or_health_claim",),
    ),
    _format(
        id="vsl",
        name="VSL",
        category="sales",
        production_style="longform_sales",
        funnel_stages=("bof",),
        platforms=("meta", "youtube_shorts", "display_native"),
        proof_types=("offer", "mechanism", "testimonial"),
        required_assets=("offer_copy",),
        optional_assets=("voiceover", "slides", "testimonials"),
        why_it_works="Longer sales logic is useful when the offer needs context, stakes, and objection handling.",
        prompt_template="Open with the problem and thesis, then sequence proof, mechanism, objections, and CTA.",
        compliance_flags=("testimonial_substantiation", "financial_or_health_claim"),
    ),
    _format(
        id="product_demo",
        name="Product Demo",
        category="demo",
        production_style="show_the_thing",
        funnel_stages=("mof", "bof"),
        platforms=("meta", "tiktok", "youtube_shorts", "linkedin"),
        proof_types=("demo", "mechanism"),
        required_assets=("product_demo",),
        optional_assets=("voiceover", "captions"),
        why_it_works="Seeing the product in action shortens the gap between interest and belief.",
        prompt_template="Show the product doing the job before you explain why it matters.",
    ),
    _format(
        id="before_after",
        name="Before and After",
        category="transformation",
        production_style="contrast",
        funnel_stages=("mof", "bof"),
        platforms=("meta", "tiktok", "youtube_shorts", "display_native"),
        proof_types=("transformation", "demo"),
        required_assets=("before_after_proof",),
        optional_assets=("captions",),
        why_it_works="The contrast compresses the value proposition into one instantly legible frame.",
        prompt_template="Use the before state first, then cut hard to the after state and the driver behind it.",
        compliance_flags=("before_after_restricted", "financial_or_health_claim"),
    ),
    _format(
        id="problem_agitation",
        name="Problem Agitation",
        category="pas",
        production_style="pain_led",
        funnel_stages=("tof", "mof"),
        platforms=("meta", "tiktok", "youtube_shorts", "display_native"),
        proof_types=("problem", "contrast"),
        required_assets=("pain_visual",),
        optional_assets=("captions", "voiceover"),
        why_it_works="Naming the pain sharply helps weak-awareness buyers self-qualify fast.",
        prompt_template="Start with the painful symptom, intensify the cost of inaction, then reveal the relief path.",
    ),
    _format(
        id="undeniable_transformation",
        name="Undeniable Transformation",
        category="transformation",
        production_style="proof_heavy",
        funnel_stages=("mof", "bof"),
        platforms=("meta", "tiktok", "youtube_shorts"),
        proof_types=("transformation", "testimonial"),
        required_assets=("transformation_proof",),
        optional_assets=("customer_testimonial",),
        why_it_works="It pushes strong outcome proof when the buyer wants a visible result, not theory.",
        prompt_template="Lead with the result, then explain the timeline, mechanism, and buyer fit.",
        compliance_flags=("transformation_claim", "testimonial_substantiation"),
    ),
    _format(
        id="infographic",
        name="Infographic",
        category="data",
        production_style="static_graphic",
        funnel_stages=("mof",),
        platforms=("meta", "linkedin", "display_native"),
        proof_types=("data", "comparison"),
        required_assets=("data_points", "design_template"),
        optional_assets=("screen_recording",),
        why_it_works="The format works when the buyer trusts structured comparison or quantified insight.",
        prompt_template="Use one primary statistic or process map and keep the rest as supporting annotations.",
        compliance_flags=("financial_or_health_claim",),
    ),
    _format(
        id="headline_led",
        name="Headline-Led",
        category="offer",
        production_style="copy_first",
        funnel_stages=("tof", "mof", "bof"),
        platforms=("meta", "display_native", "linkedin"),
        proof_types=("offer", "contrast"),
        required_assets=("headline_copy",),
        optional_assets=("simple_background",),
        why_it_works="Strong copy can carry the concept when visuals are limited or speed matters.",
        prompt_template="Write the entire ad around one hard-hitting line and let the design stay secondary.",
    ),
    _format(
        id="feature_callout",
        name="Feature Callout",
        category="demo",
        production_style="feature_led",
        funnel_stages=("mof", "bof"),
        platforms=("meta", "youtube_shorts", "linkedin", "display_native"),
        proof_types=("mechanism", "feature"),
        required_assets=("product_features",),
        optional_assets=("screen_recording", "graphics"),
        why_it_works="Feature-led creative works when one capability clearly resolves a buyer objection.",
        prompt_template="Call out the feature, show it working, then tie it to the practical benefit.",
    ),
    _format(
        id="offer_promo",
        name="Offer Promo",
        category="offer",
        production_style="conversion_led",
        funnel_stages=("bof",),
        platforms=("meta", "tiktok", "youtube_shorts", "display_native"),
        proof_types=("offer", "urgency"),
        required_assets=("offer_copy",),
        optional_assets=("countdown_graphic", "product_shots"),
        why_it_works="Offer-led assets are clear closers when the audience already understands the product.",
        prompt_template="Put the offer and deadline in frame early, then restate the best-fit buyer and CTA.",
    ),
    _format(
        id="testimonial_mashup",
        name="Testimonial Mashup",
        category="social_proof",
        production_style="proof_compilation",
        funnel_stages=("mof", "bof"),
        platforms=("meta", "tiktok", "youtube_shorts", "linkedin"),
        proof_types=("testimonial", "review"),
        required_assets=("customer_testimonial",),
        optional_assets=("reviews", "captions"),
        why_it_works="Multiple proof fragments can beat a single polished testimonial by increasing density.",
        prompt_template="Stitch short customer lines around one claim or objection until a pattern is obvious.",
        compliance_flags=("testimonial_substantiation",),
    ),
    _format(
        id="carousel_proof_card",
        name="Carousel Proof Card",
        category="proof_card",
        production_style="swipeable_static",
        funnel_stages=("mof", "bof"),
        platforms=("meta", "linkedin"),
        proof_types=("review", "feature", "comparison"),
        required_assets=("proof_cards",),
        optional_assets=("product_shots",),
        why_it_works="Swipeable cards let the buyer process multiple proof points without a long video.",
        prompt_template="Make each card answer one objection: problem, mechanism, proof, feature, CTA.",
        compliance_flags=("testimonial_substantiation",),
    ),
    _format(
        id="screen_recording_demo",
        name="Screen Recording Demo",
        category="demo",
        production_style="interface_led",
        funnel_stages=("mof", "bof"),
        platforms=("meta", "youtube_shorts", "linkedin", "display_native"),
        proof_types=("demo", "feature"),
        required_assets=("screen_recording",),
        optional_assets=("voiceover", "captions"),
        why_it_works="For software or digital products, the interface itself is often the strongest proof asset.",
        prompt_template="Record the workflow, zoom into the key step, then narrate the result and CTA.",
    ),
    _format(
        id="comparison_chart",
        name="Comparison Chart",
        category="comparison",
        production_style="structured_static",
        funnel_stages=("bof",),
        platforms=("meta", "linkedin", "display_native"),
        proof_types=("comparison", "feature"),
        required_assets=("comparison_data",),
        optional_assets=("design_template",),
        why_it_works="Comparison creative helps late-stage buyers justify a switch or selection.",
        prompt_template="Keep the chart tight: competitor, attribute, proof, and why your offer wins.",
        compliance_flags=("financial_or_health_claim",),
    ),
    _format(
        id="search_text_offer",
        name="Search Text Offer",
        category="search",
        production_style="text_only",
        funnel_stages=("bof",),
        platforms=("display_native",),
        proof_types=("offer", "intent"),
        required_assets=("headline_copy", "offer_copy"),
        optional_assets=("keyword_list",),
        why_it_works="The format extends the library beyond video and mirrors late-stage, intent-heavy message work.",
        prompt_template="Write the ad around the explicit problem or offer the buyer is already searching for.",
        compliance_flags=("financial_or_health_claim",),
    ),
)

CREATIVE_FORMAT_MAP: Dict[str, CreativeFormatDefinition] = {
    item.id: item for item in CREATIVE_FORMAT_LIBRARY
}


def _normalize_tokens(values: Iterable[str]) -> Tuple[str, ...]:
    return tuple(sorted({value.strip().lower() for value in values if value and value.strip()}))


def _platform_tokens(platform: str) -> Tuple[str, ...]:
    key = platform.strip().lower()
    return PLATFORM_ALIASES.get(key, (key,))


def get_creative_format(format_id: str) -> CreativeFormatDefinition:
    """Return a format definition by ID."""

    return CREATIVE_FORMAT_MAP[format_id]


def select_creative_formats(
    *,
    platform: str,
    funnel_stage: str,
    available_assets: Sequence[str] = (),
    regulated: bool = False,
    include_needs_asset: bool = True,
    max_results: int = 10,
) -> List[CreativeFormatSelection]:
    """Select creative formats that fit the requested constraints."""

    platform_tokens = set(_platform_tokens(platform))
    stage = funnel_stage.strip().lower()
    assets = set(_normalize_tokens(available_assets))
    selections: List[CreativeFormatSelection] = []

    for definition in CREATIVE_FORMAT_LIBRARY:
        definition_platforms = set(_normalize_tokens(definition.platforms))
        platform_fit = PASS if platform_tokens.intersection(definition_platforms) else FAIL
        funnel_fit = PASS if stage in _normalize_tokens(definition.funnel_stages) else FAIL

        required_assets = set(_normalize_tokens(definition.required_assets))
        missing_assets = tuple(sorted(required_assets - assets))
        asset_feasibility = PASS if not missing_assets else NEEDS_ASSET

        compliance_flags = definition.compliance_flags
        risky_flags = tuple(flag for flag in compliance_flags if flag in REGULATED_FLAGS)
        compliance_status = REVIEW if regulated and risky_flags else PASS

        if platform_fit == FAIL or funnel_fit == FAIL:
            continue
        if asset_feasibility == NEEDS_ASSET and not include_needs_asset:
            continue

        score = 100
        score -= len(missing_assets) * 7
        score -= len(risky_flags) * 5 if regulated else 0
        score += min(len(required_assets.intersection(assets)), 3) * 2

        selections.append(
            CreativeFormatSelection(
                definition=definition,
                platform_fit=platform_fit,
                funnel_fit=funnel_fit,
                asset_feasibility=asset_feasibility,
                compliance_status=compliance_status,
                missing_assets=missing_assets,
                compliance_flags=compliance_flags,
                score=score,
            )
        )

    selections.sort(
        key=lambda item: (
            item.asset_feasibility != PASS,
            item.compliance_status == REVIEW,
            -item.score,
            item.definition.name,
        )
    )
    return selections[:max_results]


__all__ = [
    "PASS",
    "FAIL",
    "NEEDS_ASSET",
    "REVIEW",
    "CreativeFormatDefinition",
    "CreativeFormatSelection",
    "CREATIVE_FORMAT_LIBRARY",
    "CREATIVE_FORMAT_MAP",
    "get_creative_format",
    "select_creative_formats",
]
