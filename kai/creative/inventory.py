"""Content inventory and asset awareness system for the Kai Marketing OS.

Catalogs everything a business has available -- photos, testimonials, case
studies, logos, brand assets, approved copy, and video clips -- and makes it
queryable so the creative engine can reuse existing assets instead of always
creating from scratch.

The gap analysis function compares what creative briefs require against what
the inventory contains, identifying exactly what is missing and needs to be
produced.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.
"""

from __future__ import annotations

import copy
import os
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:
        """Minimal pydantic-like fallback."""

        def __init__(self, **data):
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

        def model_dump(self):
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self):
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self):
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel
    Field = _PydanticField


# ============================================================================
# Enums
# ============================================================================


class AssetQuality(str, Enum):
    """Quality tier for an inventory asset."""

    PROFESSIONAL = "professional"
    GOOD = "good"
    USABLE = "usable"
    POOR = "poor"
    PLACEHOLDER = "placeholder"


class UsageRights(str, Enum):
    """Usage rights classification for an inventory asset."""

    OWNED = "owned"
    LICENSED = "licensed"
    STOCK = "stock"
    USER_GENERATED = "user_generated"
    UNKNOWN = "unknown"


# ============================================================================
# Inventory Item Models
# ============================================================================


class InventoryPhoto(BaseModel):
    """A single photo asset in the inventory."""

    id: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    quality: str = AssetQuality.GOOD.value
    usage_rights: str = UsageRights.OWNED.value
    dimensions: Optional[str] = None
    date_taken: Optional[str] = None
    photographer: Optional[str] = None
    used_on: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InventoryTestimonial(BaseModel):
    """A single testimonial in the inventory."""

    id: str
    quote: str
    customer_name: str
    customer_title: Optional[str] = None
    customer_location: Optional[str] = None
    source: str = "direct"
    date: Optional[str] = None
    star_rating: Optional[int] = None
    verified: bool = False
    usage_rights: str = UsageRights.OWNED.value
    used_on: List[str] = Field(default_factory=list)
    has_photo: bool = False
    has_video: bool = False
    service_category: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InventoryCaseStudy(BaseModel):
    """A single case study in the inventory."""

    id: str
    title: str
    client_name: Optional[str] = None
    industry: Optional[str] = None
    service_provided: Optional[str] = None
    problem_summary: str = ""
    solution_summary: str = ""
    results_metrics: Dict[str, str] = Field(default_factory=dict)
    url: Optional[str] = None
    file_path: Optional[str] = None
    format: str = "blog_post"
    date_published: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InventoryLogo(BaseModel):
    """A single logo variant in the inventory."""

    id: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    format: str = "png"
    color_variant: str = "full_color"
    dimensions: Optional[str] = None
    is_primary: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BrandAssets(BaseModel):
    """Aggregate brand identity assets -- colors, fonts, templates."""

    primary_colors: List[str] = Field(default_factory=list)
    secondary_colors: List[str] = Field(default_factory=list)
    fonts: List[Dict[str, str]] = Field(default_factory=list)
    icon_set: Optional[str] = None
    templates: List[Dict[str, str]] = Field(default_factory=list)
    style_guide_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ApprovedMessageBlock(BaseModel):
    """Pre-approved copy block that can be reused across channels."""

    id: str
    content: str
    block_type: str = "boilerplate"
    approved_by: Optional[str] = None
    approved_date: Optional[str] = None
    channels_approved_for: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InventoryVideoClip(BaseModel):
    """A single video clip in the inventory."""

    id: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    description: str = ""
    duration_seconds: int = 0
    platform: Optional[str] = None
    topic: Optional[str] = None
    quality: str = AssetQuality.GOOD.value
    usage_rights: str = UsageRights.OWNED.value
    has_audio: bool = True
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Aggregate Inventory
# ============================================================================


class ContentInventory(BaseModel):
    """Complete content inventory for a single business.

    Aggregates all asset types and links back to the ``BusinessProfile``
    via ``business_id``.
    """

    business_id: str
    photos: List[InventoryPhoto] = Field(default_factory=list)
    testimonials: List[InventoryTestimonial] = Field(default_factory=list)
    case_studies: List[InventoryCaseStudy] = Field(default_factory=list)
    logos: List[InventoryLogo] = Field(default_factory=list)
    brand_assets: Optional[BrandAssets] = None
    approved_messaging: List[ApprovedMessageBlock] = Field(default_factory=list)
    video_clips: List[InventoryVideoClip] = Field(default_factory=list)
    last_updated: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# File Extension Sets
# ============================================================================

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif", ".tiff", ".bmp"}
_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"}
_LOGO_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg", ".eps", ".ai", ".pdf"}
_TEXT_EXTENSIONS = {".md", ".txt", ".html", ".json", ".yaml", ".yml"}

# Directory names to scan for each asset type
_PHOTO_DIRS = {"photos", "images", "assets/images", "img", "media/images"}
_TESTIMONIAL_DIRS = {"testimonials", "reviews", "social-proof"}
_CASE_STUDY_DIRS = {"case-studies", "case_studies", "success-stories"}
_LOGO_DIRS = {"logos", "brand", "brand/logos"}
_VIDEO_DIRS = {"videos", "clips", "media/videos"}
_BRAND_DIRS = {"brand", "style-guide", "brand-assets"}


# ============================================================================
# Helper Utilities
# ============================================================================


def _generate_id() -> str:
    """Generate a short unique identifier for an inventory item."""
    return uuid.uuid4().hex[:12]


def _safe_listdir(directory: str) -> List[str]:
    """List directory contents, returning empty list if directory is missing."""
    try:
        return os.listdir(directory)
    except (OSError, PermissionError):
        return []


def _find_matching_subdirs(workspace: str, target_names: set) -> List[str]:
    """Find subdirectories under *workspace* whose name matches any in *target_names*.

    Handles both flat names (``"photos"``) and nested names
    (``"assets/images"``).
    """
    found: List[str] = []
    for name in target_names:
        candidate = os.path.join(workspace, name)
        if os.path.isdir(candidate):
            found.append(candidate)
    return found


def _collect_files(directory: str, extensions: set) -> List[str]:
    """Recursively collect files under *directory* matching *extensions*."""
    results: List[str] = []
    for root, _dirs, files in os.walk(directory):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in extensions:
                results.append(os.path.join(root, fname))
    return results


def _infer_photo_tags(file_path: str) -> List[str]:
    """Infer descriptive tags from a photo file path and name."""
    tags: List[str] = []
    lower = file_path.lower()
    tag_keywords = {
        "team": "team",
        "headshot": "headshot",
        "exterior": "exterior",
        "interior": "interior",
        "before": "before_after",
        "after": "before_after",
        "product": "product",
        "logo": "logo",
        "hero": "hero",
        "banner": "banner",
        "work": "work_in_progress",
        "office": "interior",
        "storefront": "exterior",
    }
    for keyword, tag in tag_keywords.items():
        if keyword in lower and tag not in tags:
            tags.append(tag)
    return tags


def _infer_logo_format(file_path: str) -> str:
    """Return the logo format string from the file extension."""
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    return ext if ext else "png"


def _infer_logo_color_variant(file_path: str) -> str:
    """Guess color variant from file name conventions."""
    lower = os.path.basename(file_path).lower()
    if "white" in lower or "reversed" in lower:
        return "white"
    if "black" in lower or "dark" in lower:
        return "black"
    if "mono" in lower:
        return "monochrome"
    return "full_color"


def _extract_testimonial_from_text(file_path: str) -> Optional[Dict[str, str]]:
    """Attempt to read a text/markdown file and extract testimonial content.

    Returns ``None`` if the file cannot be read or appears empty.  The
    caller receives a dict with ``quote`` and ``customer_name`` keys.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read().strip()
    except (OSError, PermissionError):
        return None

    if not text:
        return None

    # Try to split attribution from quote.  Common patterns:
    #   "Great service!" -- John Smith
    #   "Great service!" - John Smith
    #   > Great service!  \n -- John Smith
    lines = [ln.strip().lstrip(">").strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None

    quote = lines[0].strip('"').strip("'")
    customer_name = "Unknown"

    # Look for an attribution line after the quote
    for line in lines[1:]:
        for sep in ("--", "---", "- ", "~ "):
            if line.startswith(sep):
                candidate = line[len(sep):].strip()
                if candidate:
                    customer_name = candidate
                    break
        else:
            # If line has no separator but is short, treat as a name
            if len(line) < 60 and not line.startswith(("#", "-", "*")):
                customer_name = line
    return {"quote": quote, "customer_name": customer_name}


# ============================================================================
# Loader Functions
# ============================================================================


def load_inventory_from_workspace(workspace_path: str) -> Dict[str, Any]:
    """Scan a workspace directory for existing assets and return a raw
    ``ContentInventory``-shaped dict.

    Auto-discovered assets are marked with ``quality="usable"`` and
    ``usage_rights="unknown"`` because we cannot verify them automatically.
    """
    photos: List[Dict[str, Any]] = []
    testimonials: List[Dict[str, Any]] = []
    case_studies: List[Dict[str, Any]] = []
    logos: List[Dict[str, Any]] = []
    video_clips: List[Dict[str, Any]] = []

    if not os.path.isdir(workspace_path):
        return _build_empty_inventory(workspace_path)

    # ----- Photos / Images -----
    for photo_dir in _find_matching_subdirs(workspace_path, _PHOTO_DIRS):
        for fpath in _collect_files(photo_dir, _IMAGE_EXTENSIONS):
            photos.append({
                "id": _generate_id(),
                "file_path": fpath,
                "url": None,
                "description": os.path.splitext(os.path.basename(fpath))[0].replace("_", " ").replace("-", " "),
                "tags": _infer_photo_tags(fpath),
                "quality": AssetQuality.USABLE.value,
                "usage_rights": UsageRights.UNKNOWN.value,
                "dimensions": None,
                "date_taken": None,
                "photographer": None,
                "used_on": [],
                "metadata": {"auto_discovered": True, "source_dir": photo_dir},
            })

    # ----- Testimonials / Reviews -----
    for test_dir in _find_matching_subdirs(workspace_path, _TESTIMONIAL_DIRS):
        for fpath in _collect_files(test_dir, _TEXT_EXTENSIONS):
            extracted = _extract_testimonial_from_text(fpath)
            if extracted is None:
                continue
            testimonials.append({
                "id": _generate_id(),
                "quote": extracted["quote"],
                "customer_name": extracted["customer_name"],
                "customer_title": None,
                "customer_location": None,
                "source": "direct",
                "date": None,
                "star_rating": None,
                "verified": False,
                "usage_rights": UsageRights.UNKNOWN.value,
                "used_on": [],
                "has_photo": False,
                "has_video": False,
                "service_category": None,
                "metadata": {"auto_discovered": True, "source_file": fpath},
            })

    # ----- Case Studies -----
    for cs_dir in _find_matching_subdirs(workspace_path, _CASE_STUDY_DIRS):
        for fpath in _collect_files(cs_dir, _TEXT_EXTENSIONS):
            basename = os.path.splitext(os.path.basename(fpath))[0]
            title = basename.replace("_", " ").replace("-", " ").title()
            case_studies.append({
                "id": _generate_id(),
                "title": title,
                "client_name": None,
                "industry": None,
                "service_provided": None,
                "problem_summary": "",
                "solution_summary": "",
                "results_metrics": {},
                "url": None,
                "file_path": fpath,
                "format": "blog_post",
                "date_published": None,
                "metadata": {"auto_discovered": True, "source_file": fpath},
            })

    # ----- Logos -----
    for logo_dir in _find_matching_subdirs(workspace_path, _LOGO_DIRS):
        for fpath in _collect_files(logo_dir, _LOGO_EXTENSIONS):
            # Only include files that look like logos (name contains "logo")
            # or are in a dedicated logos/ directory
            basename_lower = os.path.basename(fpath).lower()
            in_logo_dir = os.path.basename(logo_dir).lower() in ("logos",)
            if "logo" in basename_lower or in_logo_dir:
                logos.append({
                    "id": _generate_id(),
                    "file_path": fpath,
                    "url": None,
                    "format": _infer_logo_format(fpath),
                    "color_variant": _infer_logo_color_variant(fpath),
                    "dimensions": None,
                    "is_primary": "primary" in basename_lower or "main" in basename_lower,
                    "metadata": {"auto_discovered": True, "source_dir": logo_dir},
                })

    # ----- Videos -----
    for vid_dir in _find_matching_subdirs(workspace_path, _VIDEO_DIRS):
        for fpath in _collect_files(vid_dir, _VIDEO_EXTENSIONS):
            video_clips.append({
                "id": _generate_id(),
                "file_path": fpath,
                "url": None,
                "description": os.path.splitext(os.path.basename(fpath))[0].replace("_", " ").replace("-", " "),
                "duration_seconds": 0,
                "platform": None,
                "topic": None,
                "quality": AssetQuality.USABLE.value,
                "usage_rights": UsageRights.UNKNOWN.value,
                "has_audio": True,
                "tags": [],
                "metadata": {"auto_discovered": True, "source_dir": vid_dir},
            })

    return {
        "business_id": os.path.basename(os.path.normpath(workspace_path)),
        "photos": photos,
        "testimonials": testimonials,
        "case_studies": case_studies,
        "logos": logos,
        "brand_assets": None,
        "approved_messaging": [],
        "video_clips": video_clips,
        "last_updated": None,
        "metadata": {"source": "workspace_scan", "workspace_path": workspace_path},
    }


def _build_empty_inventory(workspace_path: str) -> Dict[str, Any]:
    """Return an empty inventory dict when the workspace is missing or empty."""
    return {
        "business_id": os.path.basename(os.path.normpath(workspace_path)),
        "photos": [],
        "testimonials": [],
        "case_studies": [],
        "logos": [],
        "brand_assets": None,
        "approved_messaging": [],
        "video_clips": [],
        "last_updated": None,
        "metadata": {"source": "workspace_scan", "workspace_path": workspace_path, "empty": True},
    }


def load_inventory_from_yaml(file_path: str) -> Dict[str, Any]:
    """Load a pre-defined inventory from a YAML file.

    The expected YAML structure mirrors the ``ContentInventory`` model
    fields.  Missing top-level keys are filled with sensible defaults.

    Uses ``yaml.safe_load`` which is available in the PyYAML stdlib
    package.  Falls back to an empty inventory if the file is unreadable
    or YAML cannot be imported.
    """
    try:
        import yaml
    except ImportError:
        return {
            "business_id": "unknown",
            "photos": [],
            "testimonials": [],
            "case_studies": [],
            "logos": [],
            "brand_assets": None,
            "approved_messaging": [],
            "video_clips": [],
            "last_updated": None,
            "metadata": {"error": "PyYAML not installed -- cannot load YAML inventory"},
        }

    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except (OSError, PermissionError, yaml.YAMLError):
        return {
            "business_id": "unknown",
            "photos": [],
            "testimonials": [],
            "case_studies": [],
            "logos": [],
            "brand_assets": None,
            "approved_messaging": [],
            "video_clips": [],
            "last_updated": None,
            "metadata": {"error": f"Failed to read or parse YAML file: {file_path}"},
        }

    if not isinstance(raw, dict):
        return {
            "business_id": "unknown",
            "photos": [],
            "testimonials": [],
            "case_studies": [],
            "logos": [],
            "brand_assets": None,
            "approved_messaging": [],
            "video_clips": [],
            "last_updated": None,
            "metadata": {"error": "YAML root is not a mapping"},
        }

    # Normalize: fill defaults for any missing top-level keys
    return {
        "business_id": raw.get("business_id", "unknown"),
        "photos": raw.get("photos", []),
        "testimonials": raw.get("testimonials", []),
        "case_studies": raw.get("case_studies", []),
        "logos": raw.get("logos", []),
        "brand_assets": raw.get("brand_assets", None),
        "approved_messaging": raw.get("approved_messaging", []),
        "video_clips": raw.get("video_clips", []),
        "last_updated": raw.get("last_updated", None),
        "metadata": raw.get("metadata", {}),
    }


# ============================================================================
# Gap Analysis
# ============================================================================

# Mapping from brief format strings to asset types typically required
_FORMAT_ASSET_REQUIREMENTS: Dict[str, List[str]] = {
    "blog": ["photo", "testimonial"],
    "blog_post": ["photo", "testimonial"],
    "linkedin": ["photo"],
    "linkedin_article": ["photo"],
    "email": ["logo"],
    "cold_email": ["logo"],
    "ad": ["photo", "logo", "video_clip"],
    "meta_ad": ["photo", "logo"],
    "google_ad": ["logo"],
    "tiktok": ["video_clip"],
    "tiktok_script": ["video_clip"],
    "video": ["video_clip", "logo"],
    "press": ["logo", "photo"],
    "press_release": ["logo", "photo"],
    "landing_page": ["photo", "testimonial", "case_study", "logo"],
    "sales_page": ["photo", "testimonial", "case_study", "logo"],
    "case_study": ["photo", "case_study"],
    "social": ["photo", "logo"],
}


def _normalize(text: Optional[str]) -> str:
    """Lowercase and strip a string for comparison, returning '' for None."""
    if text is None:
        return ""
    return text.lower().strip()


def _tags_overlap(asset_tags: List[str], brief_tags: List[str]) -> float:
    """Return the Jaccard-like overlap ratio between two tag lists."""
    if not asset_tags or not brief_tags:
        return 0.0
    a = {t.lower().strip() for t in asset_tags}
    b = {t.lower().strip() for t in brief_tags}
    intersection = a & b
    union = a | b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def _text_similarity(a: str, b: str) -> float:
    """Cheap word-overlap similarity between two strings (0.0 to 1.0)."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def _quality_acceptable(quality_value: str) -> bool:
    """Return True if the quality is professional or good."""
    return quality_value in (AssetQuality.PROFESSIONAL.value, AssetQuality.GOOD.value)


def _extract_brief_tags(brief: Dict[str, Any]) -> List[str]:
    """Extract useful matching tags from a brief dict."""
    tags: List[str] = []
    for field in ("tags", "secondary_keywords"):
        val = brief.get(field)
        if isinstance(val, list):
            tags.extend(str(t) for t in val)
    for field in ("target_keyword", "angle", "topic", "format"):
        val = brief.get(field)
        if isinstance(val, str) and val:
            tags.append(val)
    return tags


def _extract_brief_id(brief: Dict[str, Any]) -> str:
    """Get or generate an identifier for a brief."""
    for key in ("id", "brief_id", "title", "target_keyword"):
        val = brief.get(key)
        if val:
            return str(val)
    return _generate_id()


def _extract_brief_format(brief: Dict[str, Any]) -> str:
    """Get the format string from a brief, normalized."""
    return _normalize(brief.get("format", ""))


def analyze_gaps(
    inventory: Dict[str, Any],
    briefs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compare a ContentInventory against a list of creative briefs and
    identify what is missing and what can be reused.

    Parameters
    ----------
    inventory:
        A dict shaped like ``ContentInventory.model_dump()``.
    briefs:
        A list of dicts shaped like creative briefs (see
        ``harness/brief-schema.md``).

    Returns
    -------
    dict
        Gap analysis report containing per-brief missing assets, reuse
        suggestions, and aggregate summary counts.
    """
    if inventory is None:
        inventory = {}

    photos = inventory.get("photos") or []
    testimonials = inventory.get("testimonials") or []
    case_studies_inv = inventory.get("case_studies") or []
    logos = inventory.get("logos") or []
    video_clips = inventory.get("video_clips") or []
    approved_messaging = inventory.get("approved_messaging") or []

    gap_entries: List[Dict[str, Any]] = []
    total_photos_needed = 0
    total_testimonials_needed = 0
    total_case_studies_needed = 0
    total_video_clips_needed = 0
    total_logos_needed = 0

    for brief in (briefs or []):
        brief_id = _extract_brief_id(brief)
        brief_format = _extract_brief_format(brief)
        brief_tags = _extract_brief_tags(brief)
        brief_service = _normalize(brief.get("service_category", brief.get("offer", "")))
        brief_industry = _normalize(brief.get("industry", ""))
        brief_platform = _normalize(brief.get("platform", brief_format))
        brief_key_message = _normalize(brief.get("key_message", brief.get("angle", "")))

        # Determine which asset types this brief format needs
        required_types = _FORMAT_ASSET_REQUIREMENTS.get(
            brief_format,
            _FORMAT_ASSET_REQUIREMENTS.get(brief_format.replace(" ", "_"), ["photo", "logo"]),
        )

        missing_assets: List[Dict[str, str]] = []
        reuse_suggestions: List[Dict[str, str]] = []

        # ----- Check photos -----
        if "photo" in required_types:
            matching_photos = [
                p for p in photos
                if _quality_acceptable(p.get("quality", ""))
                and _tags_overlap(p.get("tags", []), brief_tags) > 0
            ]
            if matching_photos:
                best = max(matching_photos, key=lambda p: _tags_overlap(p.get("tags", []), brief_tags))
                reuse_suggestions.append({
                    "asset_id": best.get("id", ""),
                    "asset_type": "photo",
                    "match_reason": f"Tag overlap with brief tags; quality={best.get('quality', '')}",
                    "adaptation_needed": _photo_adaptation(best, brief_platform),
                })
            else:
                # Check if there are ANY photos (even lower quality)
                any_match = [p for p in photos if _tags_overlap(p.get("tags", []), brief_tags) > 0]
                if any_match:
                    best = any_match[0]
                    reuse_suggestions.append({
                        "asset_id": best.get("id", ""),
                        "asset_type": "photo",
                        "match_reason": f"Partial tag match but quality is {best.get('quality', 'unknown')}",
                        "adaptation_needed": "Quality upgrade needed; may require re-shoot or professional editing",
                    })
                missing_assets.append({
                    "asset_type": "photo",
                    "description": f"Need professional photo matching tags: {', '.join(brief_tags[:5])}",
                    "urgency": "high" if brief_format in ("landing_page", "sales_page", "ad", "meta_ad") else "medium",
                })
                total_photos_needed += 1

        # ----- Check testimonials -----
        if "testimonial" in required_types:
            matching_testimonials = [
                t for t in testimonials
                if (
                    not brief_service
                    or _normalize(t.get("service_category", "")) == brief_service
                    or _text_similarity(_normalize(t.get("service_category", "")), brief_service) > 0.3
                )
            ]
            if matching_testimonials:
                best = matching_testimonials[0]
                reuse_suggestions.append({
                    "asset_id": best.get("id", ""),
                    "asset_type": "testimonial",
                    "match_reason": f"Service category match: {best.get('service_category', 'general')}",
                    "adaptation_needed": "None" if best.get("verified") else "Verify permission to use",
                })
            else:
                missing_assets.append({
                    "asset_type": "testimonial",
                    "description": f"Need testimonial for service: {brief_service or 'general'}",
                    "urgency": "high" if brief_format in ("landing_page", "sales_page") else "low",
                })
                total_testimonials_needed += 1

        # ----- Check case studies -----
        if "case_study" in required_types:
            matching_cs = [
                cs for cs in case_studies_inv
                if (
                    (brief_industry and _normalize(cs.get("industry", "")) == brief_industry)
                    or (brief_service and _normalize(cs.get("service_provided", "")) == brief_service)
                    or _text_similarity(
                        _normalize(cs.get("title", "")),
                        brief_key_message,
                    ) > 0.2
                )
            ]
            if matching_cs:
                best = matching_cs[0]
                reuse_suggestions.append({
                    "asset_id": best.get("id", ""),
                    "asset_type": "case_study",
                    "match_reason": f"Industry/service match: {best.get('industry', '')} / {best.get('service_provided', '')}",
                    "adaptation_needed": "May need reformatting for target channel",
                })
            else:
                missing_assets.append({
                    "asset_type": "case_study",
                    "description": f"Need case study for industry={brief_industry or 'any'}, service={brief_service or 'any'}",
                    "urgency": "medium",
                })
                total_case_studies_needed += 1

        # ----- Check logos -----
        if "logo" in required_types:
            if logos:
                # Check if we have the right variant for the platform
                needed_variant = _platform_logo_variant(brief_platform)
                variant_match = [
                    lg for lg in logos
                    if lg.get("color_variant") == needed_variant
                ]
                if variant_match:
                    best = variant_match[0]
                    reuse_suggestions.append({
                        "asset_id": best.get("id", ""),
                        "asset_type": "logo",
                        "match_reason": f"Color variant '{needed_variant}' available",
                        "adaptation_needed": "None",
                    })
                else:
                    # Use primary or first logo available
                    primary = [lg for lg in logos if lg.get("is_primary")]
                    fallback = primary[0] if primary else logos[0]
                    reuse_suggestions.append({
                        "asset_id": fallback.get("id", ""),
                        "asset_type": "logo",
                        "match_reason": "Primary logo available; variant mismatch",
                        "adaptation_needed": f"Need '{needed_variant}' variant; currently have '{fallback.get('color_variant', 'unknown')}'",
                    })
            else:
                missing_assets.append({
                    "asset_type": "logo",
                    "description": "No logo files found in inventory",
                    "urgency": "high",
                })
                total_logos_needed += 1

        # ----- Check video clips -----
        if "video_clip" in required_types:
            matching_videos = [
                v for v in video_clips
                if _quality_acceptable(v.get("quality", ""))
                and (
                    not brief_platform
                    or _normalize(v.get("platform", "")) == brief_platform
                    or not v.get("platform")
                )
            ]
            if matching_videos:
                best = matching_videos[0]
                reuse_suggestions.append({
                    "asset_id": best.get("id", ""),
                    "asset_type": "video_clip",
                    "match_reason": f"Platform-compatible video; duration={best.get('duration_seconds', 0)}s",
                    "adaptation_needed": _video_adaptation(best, brief_platform),
                })
            else:
                missing_assets.append({
                    "asset_type": "video_clip",
                    "description": f"Need video clip for platform: {brief_platform or 'general'}",
                    "urgency": "high" if brief_format in ("tiktok", "tiktok_script", "video") else "medium",
                })
                total_video_clips_needed += 1

        # ----- Check approved messaging blocks -----
        if brief_key_message and approved_messaging:
            matching_blocks = [
                mb for mb in approved_messaging
                if _text_similarity(
                    _normalize(mb.get("content", "")),
                    brief_key_message,
                ) > 0.15
                or _normalize(mb.get("block_type", "")) in ("value_prop", "tagline", "boilerplate")
            ]
            for block in matching_blocks[:2]:
                channels = block.get("channels_approved_for", [])
                channel_ok = "all" in channels or brief_platform in [_normalize(c) for c in channels]
                reuse_suggestions.append({
                    "asset_id": block.get("id", ""),
                    "asset_type": "approved_message",
                    "match_reason": f"Approved {block.get('block_type', 'copy')} block with content overlap",
                    "adaptation_needed": "None" if channel_ok else f"Not yet approved for channel '{brief_platform}'",
                })

        gap_entries.append({
            "brief_id": brief_id,
            "brief_format": brief_format,
            "missing_assets": missing_assets,
            "reuse_suggestions": reuse_suggestions,
        })

    briefs_with_gaps = sum(1 for g in gap_entries if g["missing_assets"])

    return {
        "total_briefs": len(briefs or []),
        "briefs_with_gaps": briefs_with_gaps,
        "gaps": gap_entries,
        "summary": {
            "photos_needed": total_photos_needed,
            "testimonials_needed": total_testimonials_needed,
            "case_studies_needed": total_case_studies_needed,
            "video_clips_needed": total_video_clips_needed,
            "logos_needed": total_logos_needed,
        },
    }


def _photo_adaptation(photo: Dict[str, Any], platform: str) -> str:
    """Suggest what adaptation is needed to use a photo on a given platform."""
    platform = platform.lower()
    dimensions = photo.get("dimensions", "")
    suggestions: List[str] = []

    platform_sizes = {
        "instagram": "1080x1080",
        "facebook": "1200x630",
        "meta_ad": "1080x1080 or 1200x628",
        "linkedin": "1200x627",
        "tiktok": "1080x1920",
        "twitter": "1200x675",
        "google_ad": "1200x628",
        "blog": "1200x630",
    }
    target = platform_sizes.get(platform)
    if target and dimensions and dimensions != target:
        suggestions.append(f"Resize from {dimensions} to {target}")

    if not suggestions:
        if target:
            suggestions.append(f"Verify dimensions match {target}")
        else:
            suggestions.append("Verify dimensions fit target placement")

    return "; ".join(suggestions)


def _video_adaptation(video: Dict[str, Any], platform: str) -> str:
    """Suggest what adaptation is needed to use a video on a given platform."""
    platform = platform.lower()
    duration = video.get("duration_seconds", 0)
    suggestions: List[str] = []

    max_durations = {
        "tiktok": 180,
        "instagram": 90,
        "youtube_shorts": 60,
        "facebook": 240,
        "linkedin": 600,
    }
    max_dur = max_durations.get(platform)
    if max_dur and duration > max_dur:
        suggestions.append(f"Trim from {duration}s to under {max_dur}s for {platform}")

    aspect_ratios = {
        "tiktok": "9:16 vertical",
        "instagram": "1:1 or 9:16",
        "youtube_shorts": "9:16 vertical",
        "linkedin": "16:9 horizontal",
    }
    ratio = aspect_ratios.get(platform)
    if ratio:
        suggestions.append(f"Ensure aspect ratio is {ratio}")

    if not suggestions:
        suggestions.append("Review platform specs before publishing")

    return "; ".join(suggestions)


def _platform_logo_variant(platform: str) -> str:
    """Return the preferred logo color variant for a platform."""
    dark_bg_platforms = {"tiktok", "twitter", "x"}
    if platform in dark_bg_platforms:
        return "white"
    return "full_color"


# ============================================================================
# Reuse Recommendation
# ============================================================================


def recommend_reuse(
    inventory: Dict[str, Any],
    brief: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Search the inventory for reusable assets matching a single brief.

    Parameters
    ----------
    inventory:
        A dict shaped like ``ContentInventory.model_dump()``.
    brief:
        A single creative brief dict.

    Returns
    -------
    list[dict]
        Sorted by ``match_score`` descending.  Each entry contains
        ``asset_id``, ``asset_type``, ``match_score``, ``match_reason``,
        and ``adaptation_needed``.
    """
    if inventory is None or brief is None:
        return []

    recommendations: List[Dict[str, Any]] = []
    brief_tags = _extract_brief_tags(brief)
    brief_service = _normalize(brief.get("service_category", brief.get("offer", "")))
    brief_platform = _normalize(brief.get("platform", _extract_brief_format(brief)))
    brief_key_message = _normalize(brief.get("key_message", brief.get("angle", "")))

    # ----- Photos -----
    for photo in inventory.get("photos") or []:
        if not _quality_acceptable(photo.get("quality", "")):
            continue
        tag_score = _tags_overlap(photo.get("tags", []), brief_tags)
        if tag_score > 0:
            score = min(1.0, 0.3 + tag_score * 0.7)
            recommendations.append({
                "asset_id": photo.get("id", ""),
                "asset_type": "photo",
                "match_score": round(score, 3),
                "match_reason": f"Tag overlap ({tag_score:.0%}); quality={photo.get('quality', '')}",
                "adaptation_needed": _photo_adaptation(photo, brief_platform),
            })

    # ----- Testimonials -----
    for testimonial in inventory.get("testimonials") or []:
        score = 0.0
        reasons: List[str] = []

        # Service category match
        test_service = _normalize(testimonial.get("service_category", ""))
        if brief_service and test_service:
            sim = _text_similarity(test_service, brief_service)
            if sim > 0.3 or test_service == brief_service:
                score += 0.5
                reasons.append(f"Service match: {test_service}")

        # Verified bonus
        if testimonial.get("verified"):
            score += 0.2
            reasons.append("Verified review")

        # Star rating bonus
        star = testimonial.get("star_rating")
        if star is not None and star >= 4:
            score += 0.1
            reasons.append(f"{star}-star rating")

        # Quote content relevance
        if brief_key_message:
            quote_sim = _text_similarity(_normalize(testimonial.get("quote", "")), brief_key_message)
            if quote_sim > 0.1:
                score += quote_sim * 0.2
                reasons.append("Quote content relevance")

        if score > 0.1:
            adaptation = "None"
            if not testimonial.get("verified"):
                adaptation = "Verify permission to use"
            recommendations.append({
                "asset_id": testimonial.get("id", ""),
                "asset_type": "testimonial",
                "match_score": round(min(1.0, score), 3),
                "match_reason": "; ".join(reasons),
                "adaptation_needed": adaptation,
            })

    # ----- Case Studies -----
    for cs in inventory.get("case_studies") or []:
        score = 0.0
        reasons_cs: List[str] = []

        cs_industry = _normalize(cs.get("industry", ""))
        cs_service = _normalize(cs.get("service_provided", ""))

        if brief_industry := _normalize(brief.get("industry", "")):
            if cs_industry == brief_industry:
                score += 0.4
                reasons_cs.append(f"Industry match: {cs_industry}")
            elif _text_similarity(cs_industry, brief_industry) > 0.3:
                score += 0.2
                reasons_cs.append(f"Related industry: {cs_industry}")

        if brief_service:
            if cs_service == brief_service:
                score += 0.4
                reasons_cs.append(f"Service match: {cs_service}")
            elif _text_similarity(cs_service, brief_service) > 0.3:
                score += 0.2
                reasons_cs.append(f"Related service: {cs_service}")

        # Title/content relevance
        if brief_key_message:
            title_sim = _text_similarity(_normalize(cs.get("title", "")), brief_key_message)
            if title_sim > 0.1:
                score += title_sim * 0.2
                reasons_cs.append("Title relevance")

        if score > 0.1:
            recommendations.append({
                "asset_id": cs.get("id", ""),
                "asset_type": "case_study",
                "match_score": round(min(1.0, score), 3),
                "match_reason": "; ".join(reasons_cs),
                "adaptation_needed": "May need reformatting for target channel",
            })

    # ----- Logos -----
    for logo in inventory.get("logos") or []:
        score = 0.3  # Logos are almost always reusable
        reasons_lg: List[str] = []

        needed_variant = _platform_logo_variant(brief_platform)
        if logo.get("color_variant") == needed_variant:
            score += 0.4
            reasons_lg.append(f"Correct variant ({needed_variant})")
        else:
            reasons_lg.append(f"Have {logo.get('color_variant', 'unknown')}; need {needed_variant}")

        if logo.get("is_primary"):
            score += 0.2
            reasons_lg.append("Primary logo")

        # Prefer vector formats
        if logo.get("format") in ("svg", "eps", "ai"):
            score += 0.1
            reasons_lg.append(f"Vector format ({logo.get('format')})")

        adaptation = "None"
        if logo.get("color_variant") != needed_variant:
            adaptation = f"Need '{needed_variant}' variant"

        recommendations.append({
            "asset_id": logo.get("id", ""),
            "asset_type": "logo",
            "match_score": round(min(1.0, score), 3),
            "match_reason": "; ".join(reasons_lg),
            "adaptation_needed": adaptation,
        })

    # ----- Video Clips -----
    for video in inventory.get("video_clips") or []:
        if not _quality_acceptable(video.get("quality", "")):
            continue

        score = 0.0
        reasons_v: List[str] = []

        # Platform match
        vid_platform = _normalize(video.get("platform", ""))
        if brief_platform and vid_platform:
            if vid_platform == brief_platform:
                score += 0.4
                reasons_v.append(f"Platform match: {vid_platform}")
        elif not vid_platform:
            # Generic video is somewhat usable anywhere
            score += 0.15
            reasons_v.append("Platform-agnostic video")

        # Tag overlap
        vid_tag_score = _tags_overlap(video.get("tags", []), brief_tags)
        if vid_tag_score > 0:
            score += vid_tag_score * 0.4
            reasons_v.append(f"Tag overlap ({vid_tag_score:.0%})")

        # Topic match
        if brief_key_message and video.get("topic"):
            topic_sim = _text_similarity(_normalize(video["topic"]), brief_key_message)
            if topic_sim > 0.1:
                score += topic_sim * 0.2
                reasons_v.append("Topic relevance")

        if score > 0.1:
            recommendations.append({
                "asset_id": video.get("id", ""),
                "asset_type": "video_clip",
                "match_score": round(min(1.0, score), 3),
                "match_reason": "; ".join(reasons_v),
                "adaptation_needed": _video_adaptation(video, brief_platform),
            })

    # ----- Approved Messaging Blocks -----
    for block in inventory.get("approved_messaging") or []:
        if not brief_key_message:
            continue
        content_sim = _text_similarity(_normalize(block.get("content", "")), brief_key_message)
        if content_sim > 0.1:
            channels = block.get("channels_approved_for", [])
            channel_ok = "all" in channels or brief_platform in [_normalize(c) for c in channels]
            score = min(1.0, 0.2 + content_sim * 0.6 + (0.2 if channel_ok else 0.0))
            adaptation = "None" if channel_ok else f"Not yet approved for '{brief_platform}'"
            recommendations.append({
                "asset_id": block.get("id", ""),
                "asset_type": "approved_message",
                "match_score": round(score, 3),
                "match_reason": f"Content relevance ({content_sim:.0%}); type={block.get('block_type', '')}",
                "adaptation_needed": adaptation,
            })

    # Sort by match_score descending
    recommendations.sort(key=lambda r: r["match_score"], reverse=True)
    return recommendations


# ============================================================================
# Inventory Summary
# ============================================================================


def get_inventory_summary(inventory: Dict[str, Any]) -> Dict[str, Any]:
    """Return a quick count summary of what is in the inventory.

    Handles ``None`` and missing keys gracefully.
    """
    if inventory is None:
        inventory = {}

    photos = inventory.get("photos") or []
    testimonials = inventory.get("testimonials") or []
    case_studies_list = inventory.get("case_studies") or []
    logos = inventory.get("logos") or []
    brand_assets = inventory.get("brand_assets")
    approved_messaging = inventory.get("approved_messaging") or []
    video_clips = inventory.get("video_clips") or []

    professional_photos = sum(
        1 for p in photos
        if p.get("quality") == AssetQuality.PROFESSIONAL.value
    )
    verified_testimonials = sum(
        1 for t in testimonials
        if t.get("verified") is True
    )
    logo_formats = sorted({
        lg.get("format", "unknown") for lg in logos
    })

    return {
        "total_photos": len(photos),
        "professional_photos": professional_photos,
        "total_testimonials": len(testimonials),
        "verified_testimonials": verified_testimonials,
        "total_case_studies": len(case_studies_list),
        "total_logos": len(logos),
        "logo_formats": logo_formats,
        "has_brand_assets": brand_assets is not None,
        "total_approved_messaging": len(approved_messaging),
        "total_video_clips": len(video_clips),
        "last_updated": inventory.get("last_updated"),
    }
