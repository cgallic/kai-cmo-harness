from pathlib import Path

from scripts.security.sanitize import compile_patterns, sanitize_text, scan_text


def test_sanitizer_flags_email_phone_and_secret(tmp_path: Path) -> None:
    path = tmp_path / "lead.md"
    text = "Contact jane@example.com at (555) 234-9876 with API_KEY=abc123456789abcdef.\n"

    findings = scan_text(path, text, compile_patterns({}))

    labels = {finding.label for finding in findings}
    assert {"EMAIL", "PHONE", "SECRET_ASSIGNMENT"} <= labels


def test_sanitizer_redacts_configured_client_domain(tmp_path: Path) -> None:
    text = "Client domain is acme.example and owner is ops@acme.example.\n"
    patterns = compile_patterns({"client_domains": ["acme.example"]})

    sanitized = sanitize_text(text, patterns)

    assert "acme.example" not in sanitized
    assert "[CLIENT_DOMAIN]" in sanitized
    assert "[EMAIL]" in sanitized
