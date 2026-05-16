from pathlib import Path
import json
import subprocess
import sys

from kai.creative.claymation_pipeline import (
    ClaymationLead,
    generate_claymation_ad_concept,
    generate_outbound_pitch,
    run_dry_run,
    score_weak_ad_opportunity,
)


def test_scores_sample_worthy_lead():
    lead = ClaymationLead(
        name="Local Gym",
        category="gym",
        city="Austin",
        state="TX",
        rating=4.9,
        reviews=120,
        social_links={"instagram": "https://example.com/localgym"},
        ad_observations=[
            "No video creative",
            "Generic stock visuals",
            "Weak CTA",
            "No local specificity",
        ],
    )

    score = score_weak_ad_opportunity(lead)

    assert score.score >= 12
    assert score.band == "sample-worthy"
    assert any(signal["id"] == "strong_reviews_weak_ads" for signal in score.signals)


def test_generates_concept_and_pitch_without_side_effects():
    lead = ClaymationLead(
        name="Northside Cafe",
        category="restaurant",
        city="Denver",
        state="CO",
        ad_observations=["Static only", "unclear offer"],
    )

    score = score_weak_ad_opportunity(lead)
    concept = generate_claymation_ad_concept(lead)
    pitch = generate_outbound_pitch(lead, score, concept)

    assert "Northside Cafe" in concept.angle
    assert len(concept.storyboard) >= 4
    assert concept.frame_prompts
    assert "Sample video idea" in pitch.email_subject
    assert pitch.recommended_package in {"Starter 2 videos/month", "Growth 4 videos/month"}


def test_run_dry_run_marks_no_external_side_effects():
    result = run_dry_run([
        ClaymationLead(
            name="Sample Salon",
            category="salon",
            ad_observations=["no reels", "weak cta"],
        )
    ])

    assert result["dry_run"] is True
    assert result["external_side_effects"] == []
    assert result["items"][0]["concept"]["tool_handoff"]["animation"]["tool"]


def test_cli_writes_dry_run_json(tmp_path):
    leads_csv = tmp_path / "leads.csv"
    leads_csv.write_text(
        "name,category,city,state,rating,reviews,observations\n"
        "Bright Smiles,dentist,Phoenix,AZ,4.8,90,no video; weak cta; generic\n",
        encoding="utf-8",
    )
    output = tmp_path / "dry-run.json"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/leads/claymation_pipeline.py",
            "--input",
            str(leads_csv),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    data = json.loads(output.read_text(encoding="utf-8"))
    assert completed.returncode == 0
    assert data["items"][0]["lead"]["name"] == "Bright Smiles"
    assert data["items"][0]["pitch"]["email_subject"]
