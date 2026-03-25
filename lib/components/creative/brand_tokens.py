"""
Brand Token Extractor — Pull design tokens from any codebase or config.

Sources (checked in priority order):
1. ~/.kai-marketing/config.yaml → brand section
2. tailwind.config.ts/js → theme.extend.colors
3. CSS variables → :root { --color-* }
4. TypeScript theme files → colors/fonts objects
5. package.json → name, description

Usage:
    tokens = extract_brand_tokens("/path/to/project")
    tokens = load_brand_from_config()
    remotion_config = to_remotion_brand(tokens)
"""

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class BrandTokens:
    """Extracted brand design tokens."""
    name: str = ""
    tagline: str = ""
    colors: dict = field(default_factory=lambda: {
        "primary": "#6366f1",
        "secondary": "#8b5cf6",
        "background": "#0f0f23",
        "text": "#ffffff",
        "accent": "#22c55e",
    })
    fonts: dict = field(default_factory=lambda: {
        "heading": "Inter",
        "body": "Inter",
    })
    assets: dict = field(default_factory=lambda: {
        "logo": "",
        "character": "",
    })
    voice: dict = field(default_factory=lambda: {
        "formal_casual": 4,
        "serious_playful": 3,
        "technical_simple": 7,
        "confident": 8,
        "terse": 8,
    })

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "tagline": self.tagline,
            "colors": self.colors,
            "fonts": self.fonts,
            "assets": self.assets,
            "voice": self.voice,
        }


def load_brand_from_config() -> BrandTokens:
    """Load brand tokens from ~/.kai-marketing/config.yaml."""
    config_path = Path.home() / ".kai-marketing" / "config.yaml"
    if not config_path.exists():
        return BrandTokens()

    try:
        import yaml
        cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        brand = cfg.get("brand", {})
        if not brand:
            return BrandTokens()

        return BrandTokens(
            name=brand.get("name", ""),
            tagline=brand.get("tagline", ""),
            colors=brand.get("colors", BrandTokens().colors),
            fonts=brand.get("fonts", BrandTokens().fonts),
            assets=brand.get("assets", BrandTokens().assets),
            voice=brand.get("voice", BrandTokens().voice),
        )
    except Exception:
        return BrandTokens()


def extract_from_tailwind(project_root: Path) -> dict:
    """Extract colors and fonts from tailwind.config.ts/js."""
    colors = {}
    fonts = {}

    for ext in ["ts", "js", "mjs"]:
        tw_path = project_root / f"tailwind.config.{ext}"
        if tw_path.exists():
            content = tw_path.read_text(encoding="utf-8", errors="ignore")

            # Extract color hex values
            for match in re.finditer(r"['\"]?(primary|secondary|accent|background|foreground|brand)['\"]?\s*:\s*['\"]?(#[0-9a-fA-F]{3,8})['\"]?", content):
                colors[match.group(1)] = match.group(2)

            # Extract font families
            for match in re.finditer(r"fontFamily\s*:\s*\{[^}]*?['\"]?(sans|heading|body|mono)['\"]?\s*:\s*\[?\s*['\"]([^'\"]+)['\"]", content, re.DOTALL):
                fonts[match.group(1)] = match.group(2)

            break

    return {"colors": colors, "fonts": fonts}


def extract_from_css(project_root: Path) -> dict:
    """Extract CSS custom properties from globals.css or similar."""
    colors = {}

    css_candidates = [
        project_root / "src" / "styles" / "globals.css",
        project_root / "src" / "app" / "globals.css",
        project_root / "styles" / "globals.css",
        project_root / "src" / "index.css",
    ]

    for css_path in css_candidates:
        if css_path.exists():
            content = css_path.read_text(encoding="utf-8", errors="ignore")

            # Extract --color-* or --* custom properties with color values
            for match in re.finditer(r"--([\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8}|rgb[a]?\([^)]+\))", content):
                name = match.group(1).replace("-", "_")
                colors[name] = match.group(2)
            break

    return {"colors": colors}


def extract_from_package_json(project_root: Path) -> dict:
    """Extract brand name from package.json."""
    pkg_path = project_root / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
            return {
                "name": pkg.get("name", "").replace("-", " ").replace("_", " ").title(),
                "description": pkg.get("description", ""),
            }
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return {}


def extract_brand_tokens(project_root: str | Path) -> BrandTokens:
    """
    Extract brand tokens from a project directory.
    Checks: config.yaml → tailwind → CSS → package.json
    """
    root = Path(project_root)
    tokens = load_brand_from_config()

    # If config has a name, it's already set up — use it
    if tokens.name:
        return tokens

    # Extract from codebase
    tw = extract_from_tailwind(root)
    css = extract_from_css(root)
    pkg = extract_from_package_json(root)

    # Merge (config takes priority, then tailwind, then CSS)
    if not tokens.name and pkg.get("name"):
        tokens.name = pkg["name"]
    if not tokens.tagline and pkg.get("description"):
        tokens.tagline = pkg["description"]

    for source in [tw.get("colors", {}), css.get("colors", {})]:
        for key, val in source.items():
            if key in ("primary", "brand") and not tokens.colors.get("primary"):
                tokens.colors["primary"] = val
            elif key in ("secondary", "accent") and not tokens.colors.get("secondary"):
                tokens.colors["secondary"] = val
            elif "background" in key and not tokens.colors.get("background"):
                tokens.colors["background"] = val

    for key, val in tw.get("fonts", {}).items():
        if key in ("sans", "heading") and tokens.fonts.get("heading") == "Inter":
            tokens.fonts["heading"] = val
        elif key in ("sans", "body") and tokens.fonts.get("body") == "Inter":
            tokens.fonts["body"] = val

    # Find logo
    for logo_candidate in [
        root / "public" / "logo.png",
        root / "public" / "logo.svg",
        root / "public" / "images" / "logo.png",
        root / "src" / "assets" / "logo.png",
        root / "assets" / "logo.png",
    ]:
        if logo_candidate.exists():
            tokens.assets["logo"] = str(logo_candidate)
            break

    return tokens


def to_remotion_brand(tokens: BrandTokens) -> str:
    """Convert brand tokens to Remotion brand.ts TypeScript config."""
    return f'''// Auto-generated by kai-marketing brand_tokens.py
// Source: ~/.kai-marketing/config.yaml + codebase extraction

export const brand = {{
  name: "{tokens.name}",
  tagline: "{tokens.tagline}",

  colors: {{
    primary: "{tokens.colors.get('primary', '#6366f1')}",
    secondary: "{tokens.colors.get('secondary', '#8b5cf6')}",
    background: "{tokens.colors.get('background', '#0f0f23')}",
    backgroundLight: "{_lighten(tokens.colors.get('background', '#0f0f23'))}",
    text: "{tokens.colors.get('text', '#ffffff')}",
    textMuted: "rgba(255,255,255,0.7)",
    success: "{tokens.colors.get('accent', '#22c55e')}",
    error: "#ef4444",
  }},

  fonts: {{
    heading: "{tokens.fonts.get('heading', 'Inter')}",
    body: "{tokens.fonts.get('body', 'Inter')}",
  }},

  assets: {{
    logo: "{tokens.assets.get('logo', 'logo.png')}",
  }},

  copy: {{
    hooks: [],
    problems: [],
    solutions: [],
    ctas: [],
  }},
}};
'''


def _lighten(hex_color: str) -> str:
    """Lighten a hex color by 20%."""
    try:
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, int(r + (255 - r) * 0.2))
        g = min(255, int(g + (255 - g) * 0.2))
        b = min(255, int(b + (255 - b) * 0.2))
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, IndexError):
        return hex_color
