"""Literal customer phrase constraints. Requires an explicit scoped profile."""
import re


def check_content(content, profile):
    violations = []
    for phrase in profile.get("banned_phrases", []):
        for number, line in enumerate(content.splitlines(), 1):
            if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", line, re.IGNORECASE):
                violations.append({"line": number, "text": phrase})
    return {"passed": not violations, "violations": violations}
