"""Healthcare / Medical overlay for the Kai Marketing OS.

Layers HIPAA compliance, medical claim restrictions, patient privacy
requirements, and healthcare-specific KPIs onto any compatible base
archetype.  Designed for medical practices, dental offices, clinics,
chiropractors, optometrists, veterinarians, physical therapy practices,
and other healthcare providers.

Compatible with: ``local-service``, ``professional-services``,
``multi-location``.

Usage::

    from kai.archetypes.overlays import apply_overlay, HEALTHCARE_OVERLAY
    from kai.archetypes import LOCAL_SERVICE_ARCHETYPE

    healthcare_local = apply_overlay(
        LOCAL_SERVICE_ARCHETYPE, HEALTHCARE_OVERLAY
    )
"""

from __future__ import annotations

from kai.archetypes.base import KPIDefinition
from kai.archetypes.overlays.overlay_registry import OverlayDefinition

# ============================================================================
# Healthcare-specific KPIs
# ============================================================================

_HEALTHCARE_KPIS = {
    "patient_acquisition_cost": KPIDefinition(
        id="patient_acquisition_cost",
        name="Patient Acquisition Cost",
        description=(
            "Average marketing spend to acquire one new patient, "
            "including ad spend, content, and overhead"
        ),
        unit="dollars",
        direction="lower_is_better",
        priority="primary",
        benchmark_range="$50-300",
    ),
    "patient_satisfaction_score": KPIDefinition(
        id="patient_satisfaction_score",
        name="Patient Satisfaction Score",
        description=(
            "Average patient satisfaction rating from post-visit "
            "surveys or review platforms"
        ),
        unit="rating",
        direction="higher_is_better",
        priority="secondary",
        benchmark_range="7-10",
    ),
    "appointment_show_rate": KPIDefinition(
        id="appointment_show_rate",
        name="Appointment Show Rate",
        description=(
            "Percentage of scheduled appointments where the patient "
            "actually shows up"
        ),
        unit="percentage",
        direction="higher_is_better",
        priority="secondary",
        benchmark_range="80-95%",
    ),
}

# ============================================================================
# Overlay definition
# ============================================================================

HEALTHCARE_OVERLAY = OverlayDefinition(
    id="healthcare",
    name="Healthcare / Medical",
    description=(
        "Adds HIPAA compliance, medical claim restrictions, patient "
        "privacy requirements, and healthcare-specific KPIs.  Applies "
        "to medical practices, dental offices, clinics, chiropractors, "
        "and other healthcare providers."
    ),
    compatible_archetypes=["local-service", "professional-services", "multi-location"],
    additional_audit_categories=[
        "hipaa_compliance",
        "medical_claim_verification",
        "patient_review_management",
    ],
    additional_kpis=_HEALTHCARE_KPIS,
    additional_compliance=[
        (
            "HIPAA requires that no patient information (including "
            "testimonials) be shared without written consent"
        ),
        (
            "Medical claims must be evidence-based -- no unproven "
            "treatment efficacy claims"
        ),
        (
            "Before/after photos require explicit patient consent and "
            "may not be used on certain platforms"
        ),
        "Advertising cannot guarantee specific medical outcomes",
        "Prescription medication advertising has FDA requirements",
        (
            "Telehealth advertising must comply with state licensing "
            "requirements"
        ),
        (
            "Patient testimonials may need disclaimer: "
            "'Individual results may vary'"
        ),
    ],
    restricted_actions=["before_after_posts", "testimonial_cards"],
    restricted_claims=[
        "cure",
        "guaranteed results",
        "painless",
        "risk-free treatment",
        "best doctor/practice",
    ],
    required_disclaimers=[
        "Individual results may vary",
        "Consult your healthcare provider",
    ],
    modified_priorities={},
    additional_creative_rules=[
        "No before/after images without written patient consent on file",
        "No stock photos representing specific medical procedures",
        "All practitioner credentials must be current and verifiable",
        (
            "Meta Ads: healthcare falls under Special Ad Categories on "
            "some platforms"
        ),
    ],
    metadata={
        "regulatory_bodies": ["FDA", "HHS/OCR", "state_medical_boards"],
        "key_law": "HIPAA",
    },
)

__all__ = ["HEALTHCARE_OVERLAY"]
