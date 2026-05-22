from __future__ import annotations

import json
from pathlib import Path


def test_creator_disclosure_presets_have_expected_jurisdictions() -> None:
    path = Path("harness/references/creator-disclosure-presets.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    presets = payload.get("presets") or {}
    assert "us_ftc" in presets
    assert "uk_asa" in presets
    assert "eu_ucpd" in presets

    for preset_name in ("us_ftc", "uk_asa", "eu_ucpd"):
        preset = presets[preset_name]
        assert isinstance(preset.get("label_examples"), list)
        assert preset.get("label_examples")
        assert isinstance(preset.get("requirements"), list)
        assert preset.get("requirements")
