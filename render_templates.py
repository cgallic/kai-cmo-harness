#!/usr/bin/env python3
"""
Kai CMO Harness — Template Renderer

Reads config.yaml and renders all .j2 templates in workspace/agents/
plus workspace markdown files that contain Jinja2 syntax.

Usage:
    python render_templates.py
    python render_templates.py --config my-config.yaml
    python render_templates.py --config my-config.yaml --output-dir workspace/
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install it with: pip install pyyaml")
    sys.exit(1)

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateSyntaxError
except ImportError:
    print("ERROR: Jinja2 is required. Install it with: pip install jinja2")
    sys.exit(1)


# Jinja2 syntax detection pattern — matches {{ }}, {% %}, or {# #}
JINJA2_PATTERN = re.compile(r"\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\}", re.DOTALL)

# Workspace markdown files to check for template syntax
WORKSPACE_MD_FILES = [
    "MARKETING.md",
    "SOUL.md",
    "HEARTBEAT.md",
    "AGENTS.md",
    "TOOLS.md",
]


def load_config(config_path: Path) -> dict:
    """Load and validate config.yaml."""
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        print()
        print("To get started:")
        print("  1. Copy config.yaml.example to config.yaml")
        print("  2. Fill in your values")
        print("  3. Run: python render_templates.py")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"ERROR: Invalid YAML in {config_path}:")
            print(f"  {e}")
            sys.exit(1)

    if not config:
        print(f"ERROR: Config file is empty: {config_path}")
        sys.exit(1)

    # Validate required top-level keys
    required_keys = ["owner", "products"]
    missing = [k for k in required_keys if k not in config]
    if missing:
        print(f"ERROR: Missing required config keys: {', '.join(missing)}")
        print(f"  See config.yaml.example for the expected structure.")
        sys.exit(1)

    return config


def build_template_context(config: dict) -> dict:
    """Flatten config into the template variable namespace."""
    return {
        "owner": config.get("owner", {}),
        "products": config.get("products", []),
        "discord": config.get("discord", {}),
        "harness": config.get("harness", {}),
        "server": config.get("server", {}),
        "schedule": config.get("schedule", {}),
    }


def render_j2_templates(output_dir: Path, context: dict) -> list[str]:
    """
    Find all .j2 files in <output_dir>/agents/ and render them as .md files.
    Returns list of rendered file paths (relative to output_dir).
    """
    agents_dir = output_dir / "agents"
    rendered = []

    if not agents_dir.exists():
        return rendered

    j2_files = sorted(agents_dir.glob("*.j2"))
    if not j2_files:
        return rendered

    env = Environment(
        loader=FileSystemLoader(str(agents_dir)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )

    for j2_path in j2_files:
        template_name = j2_path.name
        output_name = j2_path.stem  # strip .j2 extension
        # If the stem doesn't already end with .md, add it
        if not output_name.endswith(".md"):
            output_name += ".md"
        output_path = agents_dir / output_name

        try:
            template = env.get_template(template_name)
            rendered_content = template.render(**context)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered_content)

            rel_path = output_path.relative_to(output_dir)
            rendered.append(str(rel_path))
        except TemplateSyntaxError as e:
            print(f"  WARNING: Syntax error in {template_name} (line {e.lineno}): {e.message}")
        except Exception as e:
            print(f"  WARNING: Failed to render {template_name}: {e}")

    return rendered


def render_workspace_md(output_dir: Path, context: dict) -> list[str]:
    """
    Check workspace markdown files for Jinja2 syntax and render them in-place.
    Only processes files that actually contain {{ }}, {% %}, or {# #} tags.
    Returns list of rendered file paths (relative to output_dir).
    """
    rendered = []

    for filename in WORKSPACE_MD_FILES:
        filepath = output_dir / filename
        if not filepath.exists():
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Skip files with no Jinja2 syntax
        if not JINJA2_PATTERN.search(content):
            continue

        env = Environment(
            loader=FileSystemLoader(str(output_dir)),
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )

        try:
            template = env.from_string(content)
            rendered_content = template.render(**context)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(rendered_content)

            rendered.append(filename)
        except TemplateSyntaxError as e:
            print(f"  WARNING: Syntax error in {filename} (line {e.lineno}): {e.message}")
        except Exception as e:
            print(f"  WARNING: Failed to render {filename}: {e}")

    return rendered


def main():
    parser = argparse.ArgumentParser(
        description="Render Jinja2 templates using config.yaml values."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to config.yaml (default: config.yaml)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("workspace"),
        help="Path to workspace directory (default: workspace/)",
    )
    args = parser.parse_args()

    # Resolve paths relative to script location if not absolute
    script_dir = Path(__file__).parent.resolve()

    config_path = args.config if args.config.is_absolute() else script_dir / args.config
    output_dir = args.output_dir if args.output_dir.is_absolute() else script_dir / args.output_dir

    print(f"Config:    {config_path}")
    print(f"Output:    {output_dir}")
    print()

    # Load config
    config = load_config(config_path)
    context = build_template_context(config)

    product_names = [p.get("name", p.get("id", "?")) for p in context["products"]]
    print(f"Owner:     {context['owner'].get('name', '(not set)')}")
    print(f"Products:  {', '.join(product_names)}")
    print()

    # Render .j2 agent templates
    print("--- Agent templates (.j2) ---")
    j2_rendered = render_j2_templates(output_dir, context)
    if j2_rendered:
        for path in j2_rendered:
            print(f"  rendered: {path}")
    else:
        agents_dir = output_dir / "agents"
        if not agents_dir.exists():
            print(f"  (no agents/ directory found at {agents_dir})")
        else:
            print("  (no .j2 templates found in agents/)")
    print()

    # Render workspace markdown files
    print("--- Workspace markdown files ---")
    md_rendered = render_workspace_md(output_dir, context)
    if md_rendered:
        for path in md_rendered:
            print(f"  rendered: {path}")
    else:
        print("  (no files contained Jinja2 syntax — nothing to render)")
    print()

    # Summary
    total = len(j2_rendered) + len(md_rendered)
    if total > 0:
        print(f"Done. Rendered {total} file(s).")
    else:
        print("Done. No templates found to render.")
        print()
        print("To use templating:")
        print("  - Add .j2 files to workspace/agents/ (e.g. writer-agent.md.j2)")
        print("  - Or add {{ owner.name }} / {% for p in products %} syntax to workspace .md files")


if __name__ == "__main__":
    main()
