"""Profile validation package for the Kai Marketing OS.

Validates a ``BusinessProfile`` against universal and archetype-specific
requirements.  Returns structured results that tell downstream consumers
exactly what is known, what is missing, and whether there is enough data
to proceed.

Usage::

    from kai.validation import validate_profile, ValidationResult
    from kai.models import BusinessProfile

    result: ValidationResult = validate_profile(profile)
    if not result.is_sufficient:
        for issue in result.critical_issues:
            print(f"CRITICAL: {issue.field_path} -- {issue.message}")
"""

from .profile_validator import (
    # Enums
    FieldValidationStatus,
    ValidationSeverity,
    # Data models
    FieldValidation,
    ValidationResult,
    # Core functions
    validate_profile,
    get_archetype_requirements,
)

__all__ = [
    # Enums
    "FieldValidationStatus",
    "ValidationSeverity",
    # Data models
    "FieldValidation",
    "ValidationResult",
    # Core functions
    "validate_profile",
    "get_archetype_requirements",
]
