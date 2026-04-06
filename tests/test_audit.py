"""Tests for kai.runtime.audit — Audit diagnosis layer."""

from __future__ import annotations

import os
import sys
import unittest

# Ensure the repo root is on sys.path so `kai` is importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kai.runtime.audit import (
    AuditCategory,
    AuditFinding,
    AuditResult,
    CategoryResult,
    CATEGORY_WEIGHTS,
    CATEGORY_DISPLAY,
    FindingPriority,
    FindingSeverity,
    LocalServiceAuditor,
    compute_category_score,
    compute_overall_score,
    prioritize_findings,
    severity_to_priority,
)


# ---------------------------------------------------------------------------
# AuditFinding schema
# ---------------------------------------------------------------------------


class TestAuditFindingSchema(unittest.TestCase):
    """AuditFinding has all required fields and auto-generates an ID."""

    def test_auto_id_generated(self) -> None:
        f = AuditFinding(category="offer_clarity", title="No pricing")
        self.assertTrue(f.finding_id.startswith("fnd_"))
        self.assertEqual(len(f.finding_id), 16)  # fnd_ + 12 hex chars

    def test_explicit_id_preserved(self) -> None:
        f = AuditFinding(finding_id="fnd_custom123456", category="local_seo")
        self.assertEqual(f.finding_id, "fnd_custom123456")

    def test_required_fields_present(self) -> None:
        f = AuditFinding(
            category="trust_and_proof",
            title="No testimonials",
            summary="Website has zero customer testimonials.",
            severity="high",
            priority="P1",
            evidence={"testimonial_count": 0},
            recommended_direction="Add testimonials to homepage",
            affected_channel="website",
        )
        d = f.model_dump()
        required = {
            "finding_id", "category", "title", "summary", "severity",
            "priority", "evidence", "recommended_direction",
            "affected_channel", "metadata",
        }
        self.assertEqual(required, required & set(d.keys()))

    def test_defaults(self) -> None:
        f = AuditFinding()
        self.assertEqual(f.severity, "medium")
        self.assertEqual(f.priority, "P2")
        self.assertEqual(f.evidence, {})
        self.assertEqual(f.metadata, {})
        self.assertEqual(f.affected_channel, "")
        self.assertEqual(f.recommended_direction, "")

    def test_model_dump_roundtrip(self) -> None:
        f = AuditFinding(
            category="speed_to_lead",
            title="No call handling",
            severity="critical",
            priority="P0",
        )
        d = f.model_dump()
        self.assertEqual(d["category"], "speed_to_lead")
        self.assertEqual(d["severity"], "critical")
        self.assertEqual(d["priority"], "P0")


# ---------------------------------------------------------------------------
# CategoryResult schema
# ---------------------------------------------------------------------------


class TestCategoryResult(unittest.TestCase):
    """CategoryResult grades and counts."""

    def _make_cr(self, score: float, n_findings: int = 0, n_critical: int = 0) -> CategoryResult:
        findings = []
        for i in range(n_critical):
            findings.append(AuditFinding(severity="critical"))
        for i in range(n_findings - n_critical):
            findings.append(AuditFinding(severity="medium"))
        return CategoryResult(
            category="offer_clarity",
            display_name="Offer Clarity",
            score=score,
            weight=3.0,
            findings=findings,
        )

    def test_grade_a(self) -> None:
        self.assertEqual(self._make_cr(95).grade, "A")

    def test_grade_b(self) -> None:
        self.assertEqual(self._make_cr(80).grade, "B")

    def test_grade_c(self) -> None:
        self.assertEqual(self._make_cr(65).grade, "C")

    def test_grade_d(self) -> None:
        self.assertEqual(self._make_cr(45).grade, "D")

    def test_grade_f(self) -> None:
        self.assertEqual(self._make_cr(30).grade, "F")

    def test_grade_boundary_90_is_a(self) -> None:
        self.assertEqual(self._make_cr(90).grade, "A")

    def test_grade_boundary_75_is_b(self) -> None:
        self.assertEqual(self._make_cr(75).grade, "B")

    def test_grade_boundary_60_is_c(self) -> None:
        self.assertEqual(self._make_cr(60).grade, "C")

    def test_grade_boundary_40_is_d(self) -> None:
        self.assertEqual(self._make_cr(40).grade, "D")

    def test_grade_boundary_39_is_f(self) -> None:
        self.assertEqual(self._make_cr(39).grade, "F")

    def test_finding_count(self) -> None:
        cr = self._make_cr(50, n_findings=4, n_critical=1)
        self.assertEqual(cr.finding_count, 4)

    def test_critical_count(self) -> None:
        cr = self._make_cr(50, n_findings=5, n_critical=2)
        self.assertEqual(cr.critical_count, 2)


# ---------------------------------------------------------------------------
# AuditResult schema
# ---------------------------------------------------------------------------


class TestAuditResult(unittest.TestCase):
    """AuditResult overall scoring and properties."""

    def test_auto_id(self) -> None:
        r = AuditResult()
        self.assertTrue(r.audit_id.startswith("aud_"))

    def test_overall_grade(self) -> None:
        r = AuditResult(overall_score=82)
        self.assertEqual(r.overall_grade, "B")

    def test_total_findings(self) -> None:
        findings = [AuditFinding() for _ in range(7)]
        r = AuditResult(prioritized_findings=findings)
        self.assertEqual(r.total_findings, 7)

    def test_critical_findings_filter(self) -> None:
        findings = [
            AuditFinding(severity="critical"),
            AuditFinding(severity="high"),
            AuditFinding(severity="critical"),
            AuditFinding(severity="low"),
        ]
        r = AuditResult(prioritized_findings=findings)
        self.assertEqual(len(r.critical_findings), 2)

    def test_top_fixes_returns_max_5(self) -> None:
        findings = [AuditFinding() for _ in range(10)]
        r = AuditResult(prioritized_findings=findings)
        self.assertEqual(len(r.top_fixes), 5)

    def test_top_fixes_returns_all_if_fewer_than_5(self) -> None:
        findings = [AuditFinding() for _ in range(3)]
        r = AuditResult(prioritized_findings=findings)
        self.assertEqual(len(r.top_fixes), 3)

    def test_model_dump_has_all_keys(self) -> None:
        r = AuditResult(brand_id="test-brand", overall_score=55.5)
        d = r.model_dump()
        required = {
            "audit_id", "brand_id", "archetype", "overall_score",
            "categories", "prioritized_findings", "metadata",
        }
        self.assertEqual(required, required & set(d.keys()))


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------


class TestComputeCategoryScore(unittest.TestCase):
    """compute_category_score — weighted pass rate."""

    def test_all_passed(self) -> None:
        checks = [{"passed": True}, {"passed": True}, {"passed": True}]
        self.assertEqual(compute_category_score(checks), 100.0)

    def test_none_passed(self) -> None:
        checks = [{"passed": False}, {"passed": False}]
        self.assertEqual(compute_category_score(checks), 0.0)

    def test_half_passed(self) -> None:
        checks = [{"passed": True}, {"passed": False}]
        self.assertEqual(compute_category_score(checks), 50.0)

    def test_weighted_scoring(self) -> None:
        checks = [
            {"passed": True, "weight": 3.0},
            {"passed": False, "weight": 1.0},
        ]
        # 3/4 = 75%
        self.assertEqual(compute_category_score(checks), 75.0)

    def test_empty_checks_returns_zero(self) -> None:
        self.assertEqual(compute_category_score([]), 0.0)

    def test_default_weight_is_one(self) -> None:
        checks = [{"passed": True}, {"passed": True}, {"passed": False}]
        # 2/3 ≈ 66.7
        self.assertAlmostEqual(compute_category_score(checks), 66.7, places=1)


class TestComputeOverallScore(unittest.TestCase):
    """compute_overall_score — weighted average of categories."""

    def test_single_category(self) -> None:
        cats = [CategoryResult(score=80.0, weight=1.0)]
        self.assertEqual(compute_overall_score(cats), 80.0)

    def test_weighted_average(self) -> None:
        cats = [
            CategoryResult(score=100.0, weight=5.0),
            CategoryResult(score=0.0, weight=5.0),
        ]
        self.assertEqual(compute_overall_score(cats), 50.0)

    def test_unequal_weights(self) -> None:
        cats = [
            CategoryResult(score=100.0, weight=3.0),
            CategoryResult(score=50.0, weight=1.0),
        ]
        # (300 + 50) / 4 = 87.5
        self.assertEqual(compute_overall_score(cats), 87.5)

    def test_empty_categories(self) -> None:
        self.assertEqual(compute_overall_score([]), 0.0)


# ---------------------------------------------------------------------------
# Prioritization
# ---------------------------------------------------------------------------


class TestPrioritizeFindings(unittest.TestCase):
    """prioritize_findings — P0 first, then severity within priority."""

    def test_p0_before_p1(self) -> None:
        f1 = AuditFinding(priority="P1", severity="critical")
        f2 = AuditFinding(priority="P0", severity="low")
        result = prioritize_findings([f1, f2])
        self.assertEqual(result[0].priority, "P0")
        self.assertEqual(result[1].priority, "P1")

    def test_same_priority_sorted_by_severity(self) -> None:
        f1 = AuditFinding(priority="P1", severity="low")
        f2 = AuditFinding(priority="P1", severity="critical")
        f3 = AuditFinding(priority="P1", severity="high")
        result = prioritize_findings([f1, f2, f3])
        self.assertEqual(result[0].severity, "critical")
        self.assertEqual(result[1].severity, "high")
        self.assertEqual(result[2].severity, "low")

    def test_full_ordering(self) -> None:
        findings = [
            AuditFinding(priority="P3", severity="low"),
            AuditFinding(priority="P0", severity="critical"),
            AuditFinding(priority="P1", severity="high"),
            AuditFinding(priority="P0", severity="high"),
            AuditFinding(priority="P2", severity="medium"),
        ]
        result = prioritize_findings(findings)
        expected_order = [
            ("P0", "critical"),
            ("P0", "high"),
            ("P1", "high"),
            ("P2", "medium"),
            ("P3", "low"),
        ]
        actual_order = [(f.priority, f.severity) for f in result]
        self.assertEqual(actual_order, expected_order)

    def test_empty_list(self) -> None:
        self.assertEqual(prioritize_findings([]), [])


class TestSeverityToPriority(unittest.TestCase):
    """severity_to_priority — default mapping."""

    def test_critical_to_p0(self) -> None:
        self.assertEqual(severity_to_priority("critical"), "P0")

    def test_high_to_p1(self) -> None:
        self.assertEqual(severity_to_priority("high"), "P1")

    def test_medium_to_p2(self) -> None:
        self.assertEqual(severity_to_priority("medium"), "P2")

    def test_low_to_p3(self) -> None:
        self.assertEqual(severity_to_priority("low"), "P3")

    def test_unknown_defaults_to_p2(self) -> None:
        self.assertEqual(severity_to_priority("banana"), "P2")


# ---------------------------------------------------------------------------
# LocalServiceAuditor
# ---------------------------------------------------------------------------


class TestLocalServiceAuditorEmpty(unittest.TestCase):
    """Auditor with empty profile — all sections missing."""

    def setUp(self) -> None:
        self.auditor = LocalServiceAuditor()
        self.result = self.auditor.audit({}, brand_id="test-brand")

    def test_result_type(self) -> None:
        self.assertIsInstance(self.result, AuditResult)

    def test_brand_id_set(self) -> None:
        self.assertEqual(self.result.brand_id, "test-brand")

    def test_archetype_is_local_service(self) -> None:
        self.assertEqual(self.result.archetype, "local-service")

    def test_overall_score_is_zero(self) -> None:
        self.assertEqual(self.result.overall_score, 0.0)

    def test_all_eight_categories_present(self) -> None:
        self.assertEqual(len(self.result.categories), 8)
        cat_names = {c.category for c in self.result.categories}
        expected = {c.value for c in AuditCategory}
        self.assertEqual(cat_names, expected)

    def test_missing_section_findings_generated(self) -> None:
        # Each missing section should produce a HIGH/P1 finding
        missing_findings = [
            f for f in self.result.prioritized_findings
            if f.evidence.get("section_missing")
        ]
        self.assertEqual(len(missing_findings), 8)
        for f in missing_findings:
            self.assertEqual(f.severity, "high")
            self.assertEqual(f.priority, "P1")

    def test_findings_are_prioritized(self) -> None:
        # All same priority/severity, so order is stable but valid
        for f in self.result.prioritized_findings:
            self.assertIn(f.priority, ["P0", "P1", "P2", "P3"])


class TestLocalServiceAuditorPartial(unittest.TestCase):
    """Auditor with partial profile — some sections populated."""

    def setUp(self) -> None:
        self.auditor = LocalServiceAuditor()
        self.profile = {
            "offer_clarity": [
                {"id": "oc_1", "label": "Service pages exist", "passed": True},
                {"id": "oc_2", "label": "Pricing visible", "passed": False},
                {"id": "oc_3", "label": "Service areas listed", "passed": True},
            ],
            "speed_to_lead": [
                {"id": "stl_1", "label": "Phone in header", "passed": True, "weight": 2.0},
                {"id": "stl_2", "label": "KaiCalls configured", "passed": False, "weight": 3.0},
                {"id": "stl_3", "label": "After-hours handling", "passed": False, "weight": 2.0},
            ],
        }
        self.result = self.auditor.audit(self.profile, brand_id="partial-brand")

    def test_populated_category_scored(self) -> None:
        oc = next(c for c in self.result.categories if c.category == "offer_clarity")
        # 2 of 3 passed, equal weight → 66.7
        self.assertAlmostEqual(oc.score, 66.7, places=1)

    def test_weighted_category_scored(self) -> None:
        stl = next(c for c in self.result.categories if c.category == "speed_to_lead")
        # weight 2 passed, weight 3+2 failed → 2/7 ≈ 28.6
        self.assertAlmostEqual(stl.score, 28.6, places=1)

    def test_failed_checks_become_findings(self) -> None:
        stl = next(c for c in self.result.categories if c.category == "speed_to_lead")
        self.assertEqual(stl.finding_count, 2)

    def test_passed_checks_not_findings(self) -> None:
        oc = next(c for c in self.result.categories if c.category == "offer_clarity")
        self.assertEqual(oc.finding_count, 1)

    def test_missing_sections_still_generate_findings(self) -> None:
        # 6 sections not provided → 6 missing-section findings
        missing = [
            f for f in self.result.prioritized_findings
            if f.evidence.get("section_missing")
        ]
        self.assertEqual(len(missing), 6)

    def test_overall_score_nonzero(self) -> None:
        self.assertGreater(self.result.overall_score, 0.0)

    def test_overall_score_less_than_100(self) -> None:
        self.assertLess(self.result.overall_score, 100.0)


class TestLocalServiceAuditorPerfect(unittest.TestCase):
    """Auditor with all checks passing."""

    def setUp(self) -> None:
        self.auditor = LocalServiceAuditor()
        self.profile = {}
        for cat in AuditCategory:
            self.profile[cat.value] = [
                {"id": f"{cat.value}_1", "label": "Check 1", "passed": True},
                {"id": f"{cat.value}_2", "label": "Check 2", "passed": True},
            ]
        self.result = self.auditor.audit(self.profile)

    def test_overall_score_100(self) -> None:
        self.assertEqual(self.result.overall_score, 100.0)

    def test_overall_grade_a(self) -> None:
        self.assertEqual(self.result.overall_grade, "A")

    def test_no_failed_check_findings(self) -> None:
        # No failed checks → no check-based findings (no missing sections either)
        failed_findings = [
            f for f in self.result.prioritized_findings
            if not f.evidence.get("section_missing")
        ]
        self.assertEqual(len(failed_findings), 0)

    def test_no_missing_section_findings(self) -> None:
        missing = [
            f for f in self.result.prioritized_findings
            if f.evidence.get("section_missing")
        ]
        self.assertEqual(len(missing), 0)

    def test_all_categories_grade_a(self) -> None:
        for cat in self.result.categories:
            self.assertEqual(cat.grade, "A", f"{cat.display_name} should be A")


class TestLocalServiceAuditorFindingDetails(unittest.TestCase):
    """Verify finding fields are populated correctly from checks."""

    def test_custom_severity_on_check(self) -> None:
        auditor = LocalServiceAuditor()
        profile = {
            "reviews_reputation": [
                {
                    "id": "rr_1",
                    "label": "Review count low",
                    "passed": False,
                    "severity": "critical",
                    "priority": "P0",
                },
            ],
        }
        result = auditor.audit(profile)
        rr = next(c for c in result.categories if c.category == "reviews_reputation")
        self.assertEqual(len(rr.findings), 1)
        f = rr.findings[0]
        self.assertEqual(f.severity, "critical")
        self.assertEqual(f.priority, "P0")

    def test_evidence_preserved(self) -> None:
        auditor = LocalServiceAuditor()
        profile = {
            "trust_and_proof": [
                {
                    "id": "tp_1",
                    "label": "No BBB listing",
                    "passed": False,
                    "evidence": {"bbb_listed": False, "checked_at": "2026-04-01"},
                },
            ],
        }
        result = auditor.audit(profile)
        tp = next(c for c in result.categories if c.category == "trust_and_proof")
        f = tp.findings[0]
        self.assertEqual(f.evidence["bbb_listed"], False)

    def test_default_channel_per_category(self) -> None:
        auditor = LocalServiceAuditor()
        profile = {
            "local_seo": [{"id": "ls_1", "label": "NAP inconsistent", "passed": False}],
            "speed_to_lead": [{"id": "stl_1", "label": "No call handling", "passed": False}],
            "channel_presence": [{"id": "cp_1", "label": "No Facebook page", "passed": False}],
        }
        result = auditor.audit(profile)
        ls = next(c for c in result.categories if c.category == "local_seo")
        stl = next(c for c in result.categories if c.category == "speed_to_lead")
        cp = next(c for c in result.categories if c.category == "channel_presence")
        self.assertEqual(ls.findings[0].affected_channel, "gbp")
        self.assertEqual(stl.findings[0].affected_channel, "phone")
        self.assertEqual(cp.findings[0].affected_channel, "social")

    def test_default_direction_per_category(self) -> None:
        auditor = LocalServiceAuditor()
        profile = {
            "follow_up_gaps": [{"id": "fu_1", "label": "No post-job follow-up", "passed": False}],
        }
        result = auditor.audit(profile)
        fu = next(c for c in result.categories if c.category == "follow_up_gaps")
        self.assertIn("follow-up", fu.findings[0].recommended_direction.lower())

    def test_check_override_channel(self) -> None:
        auditor = LocalServiceAuditor()
        profile = {
            "offer_clarity": [
                {
                    "id": "oc_1",
                    "label": "GBP services not listed",
                    "passed": False,
                    "affected_channel": "gbp",
                },
            ],
        }
        result = auditor.audit(profile)
        oc = next(c for c in result.categories if c.category == "offer_clarity")
        self.assertEqual(oc.findings[0].affected_channel, "gbp")


class TestLocalServiceAuditorHandoffContract(unittest.TestCase):
    """Verify the audit result satisfies the handoff contract.

    The proposal layer should be able to answer:
    - What is wrong?
    - Why does it matter?
    - How urgent is it?
    - Which channel should be touched?
    - What type of action should be proposed?
    """

    def setUp(self) -> None:
        self.auditor = LocalServiceAuditor()
        self.profile = {
            "conversion_path": [
                {
                    "id": "cp_1",
                    "label": "Phone not in header",
                    "passed": False,
                    "summary": "Phone number is not visible in the site header on mobile.",
                    "severity": "critical",
                    "evidence": {"phone_in_header": False, "mobile_tested": True},
                    "recommended_direction": "Add clickable phone CTA to mobile header",
                    "affected_channel": "website",
                },
            ],
        }
        self.result = self.auditor.audit(self.profile, brand_id="contract-test")

    def test_what_is_wrong(self) -> None:
        f = self.result.prioritized_findings[0]
        self.assertTrue(len(f.title) > 0)
        self.assertTrue(len(f.summary) > 0)

    def test_why_does_it_matter(self) -> None:
        f = self.result.prioritized_findings[0]
        self.assertIn(f.severity, ["critical", "high", "medium", "low"])

    def test_how_urgent(self) -> None:
        f = self.result.prioritized_findings[0]
        self.assertIn(f.priority, ["P0", "P1", "P2", "P3"])

    def test_which_channel(self) -> None:
        f = self.result.prioritized_findings[0]
        self.assertTrue(len(f.affected_channel) > 0)

    def test_what_action_type(self) -> None:
        f = self.result.prioritized_findings[0]
        self.assertTrue(len(f.recommended_direction) > 0)

    def test_evidence_is_structured(self) -> None:
        f = self.result.prioritized_findings[0]
        self.assertIsInstance(f.evidence, dict)
        self.assertIn("phone_in_header", f.evidence)


# ---------------------------------------------------------------------------
# Category weights and display coverage
# ---------------------------------------------------------------------------


class TestCategoryConstants(unittest.TestCase):
    """All categories have weights and display names."""

    def test_all_categories_have_weights(self) -> None:
        for cat in AuditCategory:
            self.assertIn(cat, CATEGORY_WEIGHTS, f"Missing weight for {cat}")
            self.assertGreater(CATEGORY_WEIGHTS[cat], 0)

    def test_all_categories_have_display_names(self) -> None:
        for cat in AuditCategory:
            self.assertIn(cat, CATEGORY_DISPLAY, f"Missing display name for {cat}")
            self.assertTrue(len(CATEGORY_DISPLAY[cat]) > 0)

    def test_eight_categories(self) -> None:
        self.assertEqual(len(AuditCategory), 8)


if __name__ == "__main__":
    unittest.main()
