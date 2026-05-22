from __future__ import annotations

from scripts.quality_gates.agent_readiness_lint import (
    check_critical_content_formats,
    check_interactive_accessibility,
    check_robots_txt_body,
    check_semantic_structure,
    check_training_bot_decisions,
)


def test_robots_passes_when_search_bots_are_not_root_blocked() -> None:
    result = check_robots_txt_body(200, "User-agent: *\nAllow: /\n")

    assert result["pass"] is True
    assert result["priority"] == "P0"


def test_robots_fails_when_chatgpt_search_bot_is_root_blocked() -> None:
    body = """
User-agent: OAI-SearchBot
Disallow: /

User-agent: *
Allow: /
"""

    result = check_robots_txt_body(200, body)

    assert result["pass"] is False
    assert "OAI-SearchBot" in " ".join(result["details"])


def test_training_bot_decisions_are_p1_not_p0() -> None:
    result = check_training_bot_decisions(200, "User-agent: *\nAllow: /\n")

    assert result["pass"] is False
    assert result["priority"] == "P1"
    assert "GPTBot" in " ".join(result["details"])


def test_semantic_structure_requires_h1_and_main() -> None:
    body = "<html><body><main><h1>Product</h1><h2>What it does</h2></main></body></html>"

    result = check_semantic_structure(body)

    assert result["pass"] is True
    assert result["priority"] == "P1"


def test_interactive_accessibility_flags_unlabeled_inputs() -> None:
    body = "<main><h1>Contact</h1><form><input id='email' type='email'></form></main>"

    result = check_interactive_accessibility(body)

    assert result["pass"] is False
    assert "input" in " ".join(result["details"])


def test_critical_content_formats_flags_image_only_pages() -> None:
    body = "<main><h1>Menu</h1><img src='a.png'><img src='b.png'><img src='c.png'></main>"

    result = check_critical_content_formats(body, "Menu")

    assert result["pass"] is False
    assert "media-only" in " ".join(result["details"])
