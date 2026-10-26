"""Revenue lens: content is graded on leads/revenue when measured, and the
collector can read the lead -> booked -> paid stages (Stripe, CRM, bookings,
PostHog). Missing access stays a data gap, never a zero."""

import json
from pathlib import Path

import pytest

from scripts.audit import collect
from scripts.audit.data_sources import AuditDataset


# ---------------------------------------------------------------------------
# 30-day grading
# ---------------------------------------------------------------------------

@pytest.fixture
def pc():
    from scripts.self_improvement import performance_check as pc

    return pc


RANK_WINNER_GSC = {"position": 3, "ctr": 0.08, "impressions": 500, "clicks": 40}
RANK_LOSER_GSC = {"position": 25, "ctr": 0.015, "impressions": 200, "clicks": 3}


def test_lead_makes_a_low_ranking_page_a_winner(pc):
    ga4 = {"avg_session_duration": 10, "key_events": 2, "revenue": 0}
    result = pc.evaluate_performance({"url": "u", "keyword": "k"}, RANK_LOSER_GSC, ga4)
    assert result["grade"] == "winner"
    assert result["is_underperformer"] is False
    assert result["outcomes"] == {"leads": 2.0, "revenue": 0.0, "source": "ga4_landing_page"}


def test_ranking_page_without_leads_is_not_a_winner(pc):
    ga4 = {"avg_session_duration": pc.WIN_TIME_ON_PAGE, "key_events": 0, "revenue": 0}
    gsc = dict(RANK_WINNER_GSC, position=pc.WIN_POSITION, ctr=pc.WIN_CTR)
    result = pc.evaluate_performance({"url": "u", "keyword": "k"}, gsc, ga4)
    assert result["grade"] == "average"
    assert result["ranks_without_leads"] is True


def test_attributed_revenue_beats_ga4(pc):
    entry = {"url": "u", "keyword": "k", "outcomes": {"leads": 0, "revenue": 450, "source": "stripe"}}
    result = pc.evaluate_performance(entry, RANK_LOSER_GSC, {"key_events": 0})
    assert result["grade"] == "winner"
    assert result["outcomes"]["source"] == "stripe"


def test_unmeasured_outcomes_keep_rank_grading(pc):
    result = pc.evaluate_performance({"url": "u", "keyword": "k"}, RANK_LOSER_GSC, {"outcome_error": "denied"})
    assert result == {"is_winner": False, "is_underperformer": True, "grade": "underperformer"}


def test_discord_message_leads_with_outcomes(pc):
    evaluation = {"grade": "average", "is_winner": False, "is_underperformer": False,
                  "outcomes": {"leads": 0.0, "revenue": 0.0, "source": "ga4_landing_page"},
                  "ranks_without_leads": True}
    msg = pc.format_discord_message({"keyword": "k", "url": "u"}, RANK_WINNER_GSC, {}, evaluation)
    assert msg.index("Outcomes") < msg.index("GSC")
    assert "Ranks but produced no leads" in msg
    unmeasured = pc.format_discord_message({"keyword": "k", "url": "u"}, RANK_WINNER_GSC, {},
                                           {"grade": "average", "is_winner": False, "is_underperformer": False})
    assert "check: leads/revenue unmeasured" in unmeasured


# ---------------------------------------------------------------------------
# Funnel collectors
# ---------------------------------------------------------------------------

REVENUE_ENV = [
    "STRIPE_API_KEY", "STRIPE_EXPORT_PATH", "HUBSPOT_ACCESS_TOKEN", "CRM_EXPORT_PATH",
    "CALENDLY_API_TOKEN", "BOOKINGS_EXPORT_PATH", "POSTHOG_PERSONAL_API_KEY",
    "POSTHOG_PROJECT_ID", "POSTHOG_FUNNEL_EVENTS", "POSTHOG_EXPORT_PATH",
]


@pytest.fixture
def clean_env(monkeypatch):
    for name in REVENUE_ENV:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def metrics(dataset: AuditDataset) -> dict:
    return {m.metric_id: m.value for m in dataset.metrics}


def test_sales_mode_makes_every_money_stage_a_gap(tmp_path, clean_env):
    dataset = AuditDataset(audit_mode="sales_external", target_url="https://example.com")
    collect.collect_revenue(dataset, tmp_path / "raw", mode="sales_external")
    assert not dataset.metrics
    missing = {g.missing_source for g in dataset.data_gaps}
    assert {"Stripe payments", "CRM (HubSpot)", "Booking system (Calendly)", "PostHog product analytics"} <= missing


def test_missing_credentials_are_gaps_not_zeros(tmp_path, clean_env):
    dataset = AuditDataset(audit_mode="onboarding_connected", target_url="https://example.com")
    collect.collect_revenue(dataset, tmp_path / "raw", mode="onboarding_connected")
    assert not dataset.metrics
    assert len(dataset.data_gaps) == 4


def test_stripe_api_net_revenue_and_pii_stripped(tmp_path, clean_env):
    clean_env.setenv("STRIPE_API_KEY", "rk_test_x")
    page = {"has_more": False, "data": [
        {"id": "ch_1", "amount": 50000, "amount_refunded": 5000, "currency": "usd", "status": "succeeded",
         "paid": True, "customer": "cus_1", "billing_details": {"email": "a@b.co"}},
        {"id": "ch_2", "amount": 20000, "amount_refunded": 0, "currency": "usd", "status": "failed",
         "paid": False, "customer": "cus_2"},
        {"id": "ch_3", "amount": 3000, "amount_refunded": 0, "currency": "jpy", "status": "succeeded",
         "paid": True, "customer": "cus_1"},
    ]}
    clean_env.setattr(collect, "fetch_json", lambda *a, **k: (200, page, json.dumps(page)))
    dataset = AuditDataset(audit_mode="onboarding_connected", target_url="https://example.com")
    collect.collect_stripe(dataset, tmp_path / "raw", mode="onboarding_connected")
    m = metrics(dataset)
    assert m["stripe_net_revenue"] == {"usd": 450.0, "jpy": 3000.0}
    assert m["stripe_paid_charges"] == 2
    assert m["stripe_paying_customers"] == 1
    raw = next((tmp_path / "raw").glob("stripe-charges*")).read_text()
    assert "a@b.co" not in raw


def test_stripe_dashboard_csv_export(tmp_path, clean_env):
    export = tmp_path / "payments.csv"
    export.write_text("id,Amount,Amount Refunded,Currency,Status,Customer ID\n"
                      "ch_1,120.00,20.00,usd,Paid,cus_1\nch_2,80.00,0,usd,Failed,cus_2\n")
    clean_env.setenv("STRIPE_EXPORT_PATH", str(export))
    dataset = AuditDataset(audit_mode="onboarding_connected", target_url="https://example.com")
    collect.collect_stripe(dataset, tmp_path / "raw", mode="onboarding_connected")
    assert metrics(dataset)["stripe_net_revenue"] == {"usd": 100.0}


def test_crm_export_lead_to_won(tmp_path, clean_env):
    export = tmp_path / "crm.json"
    export.write_text(json.dumps({"contacts_total": 40, "deals": [
        {"amount": "1500", "dealstage": "closedwon", "hs_is_closed_won": "true"},
        {"amount": "900", "dealstage": "appointmentscheduled"},
    ]}))
    clean_env.setenv("CRM_EXPORT_PATH", str(export))
    dataset = AuditDataset(audit_mode="onboarding_connected", target_url="https://example.com")
    collect.collect_crm(dataset, tmp_path / "raw", mode="onboarding_connected")
    m = metrics(dataset)
    assert m["crm_new_leads"] == 40
    assert m["crm_deals_won"] == 1
    assert m["crm_won_revenue"] == 1500.0
    assert m["crm_lead_to_won_rate"] == 0.025


def test_bookings_export(tmp_path, clean_env):
    export = tmp_path / "events.json"
    export.write_text(json.dumps({"collection": [{"status": "active"}, {"status": "canceled"}, {"status": "active"}]}))
    clean_env.setenv("BOOKINGS_EXPORT_PATH", str(export))
    dataset = AuditDataset(audit_mode="onboarding_connected", target_url="https://example.com")
    collect.collect_bookings(dataset, tmp_path / "raw", mode="onboarding_connected")
    m = metrics(dataset)
    assert (m["bookings_total"], m["bookings_canceled"], m["bookings_held_or_upcoming"]) == (3, 1, 2)


def test_posthog_api_funnel_steps(tmp_path, clean_env):
    clean_env.setenv("POSTHOG_PERSONAL_API_KEY", "phx_x")
    clean_env.setenv("POSTHOG_PROJECT_ID", "1")
    clean_env.setenv("POSTHOG_FUNNEL_EVENTS", "$pageview,lead_submitted,purchase")
    seen = {}

    def fake(url, **kwargs):
        seen["query"] = kwargs["payload"]["query"]["query"]
        return 200, {"results": [["$pageview", 900, 500], ["lead_submitted", 30, 25], ["purchase", 5, 5]]}, ""

    clean_env.setattr(collect, "fetch_json", fake)
    dataset = AuditDataset(audit_mode="onboarding_connected", target_url="https://example.com")
    collect.collect_posthog(dataset, tmp_path / "raw", mode="onboarding_connected")
    steps = metrics(dataset)["posthog_funnel_steps"]
    assert [s["step"] for s in steps] == ["$pageview", "lead_submitted", "purchase"]
    assert steps[1]["from_previous"] == 0.05
    assert steps[2]["from_previous"] == 0.2
    assert "'lead_submitted'" in seen["query"]


def test_posthog_rejects_unsafe_event_names(tmp_path, clean_env):
    clean_env.setenv("POSTHOG_PERSONAL_API_KEY", "phx_x")
    clean_env.setenv("POSTHOG_PROJECT_ID", "1")
    clean_env.setenv("POSTHOG_FUNNEL_EVENTS", "ok,x') OR 1=1 --")
    clean_env.setattr(collect, "fetch_json", lambda *a, **k: pytest.fail("query must not run"))
    dataset = AuditDataset(audit_mode="onboarding_connected", target_url="https://example.com")
    collect.collect_posthog(dataset, tmp_path / "raw", mode="onboarding_connected")
    assert not dataset.metrics


def test_revenue_flag_runs_collector(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(collect, "collect_public_site", lambda *a, **k: None)
    monkeypatch.setattr(collect, "collect_revenue", lambda *a, **k: called.append(k["mode"]))
    monkeypatch.setattr("sys.argv", ["collect.py", "--url", "https://example.com", "--out", str(tmp_path),
                                     "--mode", "onboarding_connected", "--revenue"])
    assert collect.main() == 0
    assert called == ["onboarding_connected"]
