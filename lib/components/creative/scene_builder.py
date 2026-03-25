"""
Scene Builder — Converts a creative brief into Remotion scene configurations.

Takes ad copy + brand tokens → generates scene-by-scene config that
Remotion templates consume.

Usage:
    from lib.components.creative.scene_builder import build_scenes
    scenes = build_scenes(archetype="problem-agitation", copy=ad_copy, brand=tokens)
"""

import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Scene:
    """A single scene in a video ad composition."""
    name: str
    duration_frames: int  # at 30fps
    text_primary: str = ""
    text_secondary: str = ""
    animation: str = "fade-in"  # fade-in, slide-up, spring, scale
    background: str = "brand"  # brand, gradient, image, video
    element: str = "text"  # text, product, logo, cta, stat
    metadata: dict = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        return self.duration_frames / 30


@dataclass
class Composition:
    """A complete video ad composition (sequence of scenes)."""
    name: str
    archetype: str
    scenes: list  # list of Scene
    fps: int = 30
    width: int = 1080
    height: int = 1920  # 9:16 vertical by default

    @property
    def total_frames(self) -> int:
        return sum(s.duration_frames for s in self.scenes)

    @property
    def total_seconds(self) -> float:
        return self.total_frames / self.fps

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "archetype": self.archetype,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "total_frames": self.total_frames,
            "total_seconds": self.total_seconds,
            "scenes": [
                {
                    "name": s.name,
                    "duration_frames": s.duration_frames,
                    "duration_seconds": s.duration_seconds,
                    "text_primary": s.text_primary,
                    "text_secondary": s.text_secondary,
                    "animation": s.animation,
                    "background": s.background,
                    "element": s.element,
                    "metadata": s.metadata,
                }
                for s in self.scenes
            ],
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ARCHETYPE BUILDERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _build_problem_agitation(copy: dict) -> list:
    """Problem → Frustration → Hint at solution. 6-15 seconds. Cold audiences."""
    hook = copy.get("hook", copy.get("hooks", [""])[0] if copy.get("hooks") else "")
    problem = copy.get("problem", copy.get("pain", ""))
    solution_hint = copy.get("solution_hint", copy.get("tagline", ""))
    cta = copy.get("cta", "Learn More")

    return [
        Scene(name="hook", duration_frames=90, text_primary=hook,
              animation="scale", element="text", background="brand"),
        Scene(name="problem", duration_frames=120, text_primary=problem,
              animation="slide-up", element="text", background="gradient"),
        Scene(name="agitate", duration_frames=90, text_secondary="Sound familiar?",
              animation="fade-in", element="text", background="gradient"),
        Scene(name="cta", duration_frames=90, text_primary=cta,
              animation="spring", element="cta", background="brand"),
    ]


def _build_social_proof(copy: dict) -> list:
    """Stat/Quote → Brief explanation → CTA. 6-15 seconds. Warm audiences."""
    stat = copy.get("stat", copy.get("proof", ""))
    explanation = copy.get("explanation", copy.get("benefit", ""))
    cta = copy.get("cta", "Start Free Trial")

    return [
        Scene(name="stat", duration_frames=120, text_primary=stat,
              animation="scale", element="stat", background="brand"),
        Scene(name="explain", duration_frames=120, text_primary=explanation,
              animation="slide-up", element="text", background="gradient"),
        Scene(name="cta", duration_frames=90, text_primary=cta,
              animation="spring", element="cta", background="brand"),
    ]


def _build_product_demo(copy: dict) -> list:
    """Show product → Key feature → Benefit → CTA. 15-30 seconds."""
    intro = copy.get("intro", copy.get("hook", ""))
    feature = copy.get("feature", "")
    benefit = copy.get("benefit", "")
    cta = copy.get("cta", "See It In Action")

    return [
        Scene(name="intro", duration_frames=90, text_primary=intro,
              animation="fade-in", element="text", background="brand"),
        Scene(name="demo", duration_frames=180, text_primary=feature,
              animation="slide-up", element="product", background="gradient",
              metadata={"show_screenshot": True}),
        Scene(name="benefit", duration_frames=120, text_primary=benefit,
              animation="fade-in", element="text", background="brand"),
        Scene(name="cta", duration_frames=90, text_primary=cta,
              animation="spring", element="cta", background="brand"),
    ]


def _build_lifestyle(copy: dict) -> list:
    """Desired state → How product enables it → CTA. 6-15 seconds."""
    aspiration = copy.get("aspiration", copy.get("outcome", ""))
    bridge = copy.get("bridge", copy.get("how", ""))
    cta = copy.get("cta", "Get Started")

    return [
        Scene(name="aspiration", duration_frames=120, text_primary=aspiration,
              animation="fade-in", element="text", background="gradient"),
        Scene(name="bridge", duration_frames=120, text_primary=bridge,
              animation="slide-up", element="text", background="brand"),
        Scene(name="cta", duration_frames=90, text_primary=cta,
              animation="spring", element="cta", background="brand"),
    ]


_ARCHETYPE_BUILDERS = {
    "problem-agitation": _build_problem_agitation,
    "social-proof": _build_social_proof,
    "product-demo": _build_product_demo,
    "lifestyle": _build_lifestyle,
}


def build_scenes(
    archetype: str,
    copy: dict,
    format: str = "vertical",  # vertical (9:16), square (1:1), landscape (16:9)
) -> Composition:
    """Build a Remotion composition from archetype + copy."""
    builder = _ARCHETYPE_BUILDERS.get(archetype)
    if not builder:
        raise ValueError(f"Unknown archetype: {archetype}. Valid: {list(_ARCHETYPE_BUILDERS.keys())}")

    scenes = builder(copy)

    # Set dimensions based on format
    dimensions = {
        "vertical": (1080, 1920),   # 9:16 (Reels, Stories, TikTok)
        "square": (1080, 1080),     # 1:1 (Feed)
        "landscape": (1920, 1080),  # 16:9 (YouTube, in-stream)
        "portrait": (1080, 1350),   # 4:5 (Feed optimal)
    }
    w, h = dimensions.get(format, (1080, 1920))

    return Composition(
        name=f"{archetype}-{format}",
        archetype=archetype,
        scenes=scenes,
        width=w,
        height=h,
    )


def get_all_archetypes() -> list[str]:
    """Get all available archetype names."""
    return list(_ARCHETYPE_BUILDERS.keys())


def scenes_to_remotion_config(composition: Composition) -> str:
    """Convert composition to JSON config that Remotion templates read."""
    return json.dumps(composition.to_dict(), indent=2)
