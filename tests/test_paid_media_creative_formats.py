from kai.paid_media.creative_formats import (
    CREATIVE_FORMAT_LIBRARY,
    PASS,
    REVIEW,
    get_creative_format,
    select_creative_formats,
)


def test_library_extends_beyond_seed_formats() -> None:
    assert len(CREATIVE_FORMAT_LIBRARY) >= 35
    assert get_creative_format("talking_head").name == "Talking Head"
    assert get_creative_format("screen_recording_demo").name == "Screen Recording Demo"


def test_select_formats_prefers_asset_feasible_short_form_options() -> None:
    selections = select_creative_formats(
        platform="tiktok",
        funnel_stage="tof",
        available_assets=("founder_footage", "captions", "hook_visual"),
        include_needs_asset=False,
        max_results=10,
    )

    selected_ids = {item.definition.id for item in selections}

    assert "talking_head" in selected_ids
    assert "walk_and_talk" in selected_ids
    assert "native_testimonial" not in selected_ids
    assert all(item.asset_feasibility == PASS for item in selections)


def test_regulated_selection_flags_risky_formats_for_review() -> None:
    selections = select_creative_formats(
        platform="meta",
        funnel_stage="bof",
        available_assets=("before_after_proof", "offer_copy", "transformation_proof"),
        regulated=True,
        include_needs_asset=False,
        max_results=10,
    )

    by_id = {item.definition.id: item for item in selections}

    assert by_id["before_after"].compliance_status == REVIEW
    assert by_id["undeniable_transformation"].compliance_status == REVIEW


def test_linkedin_mof_selection_surfaces_expert_formats() -> None:
    selections = select_creative_formats(
        platform="linkedin",
        funnel_stage="mof",
        available_assets=("subject_matter_expert", "podcast_video", "slides"),
        include_needs_asset=False,
        max_results=10,
    )

    selected_ids = {item.definition.id for item in selections}

    assert "expert_explainer" in selected_ids
    assert "podcast_clip" in selected_ids
