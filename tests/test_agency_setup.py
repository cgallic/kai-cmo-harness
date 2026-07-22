"""Tests for the one-command durable agency setup."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from kai.packaging.agency_setup import AgencySetupError, run_agency_setup


def _answers():
    return {
        "business_name": "Proofbound Agency",
        "business_description": "An agency that operates client marketing systems.",
        "business_type": "Professional Services/B2B",
        "primary_service": "Marketing operations",
        "service_list": "Marketing operations, Paid media",
        "social_platforms": ["LinkedIn"],
        "ad_platforms": ["Google Ads"],
        "require_content_approval": True,
        "auto_approve_low_risk": False,
    }


def test_run_agency_setup_writes_and_reads_back_durable_context(tmp_path):
    response = run_agency_setup(tmp_path, _answers())

    receipt = response["receipt"]
    assert receipt["status"] == "durable_context_written"
    assert receipt["brand_id"] == "proofbound-agency"
    assert "external-effect verification" in receipt["proof_boundary"]

    for artifact in receipt["artifacts"].values():
        resolved = Path(artifact["path"])
        assert resolved.is_file()
        assert hashlib.sha256(resolved.read_bytes()).hexdigest() == artifact["sha256"]

    receipt_path = Path(response["receipt_path"])
    assert json.loads(receipt_path.read_text(encoding="utf-8"))["brand_id"] == "proofbound-agency"


def test_run_agency_setup_rejects_missing_required_context(tmp_path):
    with pytest.raises(AgencySetupError, match="business name"):
        run_agency_setup(tmp_path, {"business_type": "Professional Services/B2B"})


def test_run_agency_setup_rejects_invalid_select_values(tmp_path):
    answers = _answers()
    answers["business_type"] = "Space empire"
    with pytest.raises(AgencySetupError, match="must be one of"):
        run_agency_setup(tmp_path, answers)
