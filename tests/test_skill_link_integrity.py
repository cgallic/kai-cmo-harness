import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "harness" / "skills"
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def test_skill_markdown_relative_links_resolve():
    missing_links = []

    for skill_file in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
        content = skill_file.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(content):
            raw_target = match.group(1).strip()
            if not raw_target or raw_target.startswith(("#", "http://", "https://", "mailto:")):
                continue

            target = raw_target.split("#", 1)[0]
            if not target:
                continue

            resolved = (skill_file.parent / target).resolve()
            try:
                resolved.relative_to(skill_file.parent.resolve())
            except ValueError:
                continue

            if not resolved.exists():
                missing_links.append(f"{skill_file.relative_to(REPO_ROOT)} -> {raw_target}")

    assert missing_links == []
