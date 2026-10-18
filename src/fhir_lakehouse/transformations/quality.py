"""Data quality checks for FHIR resources."""

from __future__ import annotations

from typing import Any

from fhir_lakehouse.logging_utils import get_logger

logger = get_logger(__name__)


def check_required_fields(
    resource: dict[str, Any],
    required_fields: list[str],
) -> list[str]:
    """Return a list of missing required fields.

    Args:
        resource: FHIR resource dict.
        required_fields: List of field names that must be present.

    Returns:
        List of missing field names (empty if all present).
    """
    missing = [f for f in required_fields if f not in resource or resource[f] is None]
    if missing:
        logger.warning(
            "Resource %s missing fields: %s",
            resource.get("id", "<unknown>"),
            missing,
        )
    return missing


def validate_resource_type(
    resource: dict[str, Any],
    expected_type: str,
) -> bool:
    """Check that a resource has the expected resourceType."""
    actual = resource.get("resourceType")
    if actual != expected_type:
        logger.warning(
            "Expected resourceType=%s, got %s for id=%s",
            expected_type,
            actual,
            resource.get("id", "<unknown>"),
        )
        return False
    return True


def check_quality(
    resource: dict[str, Any],
    expected_type: str,
    required_fields: list[str],
) -> dict[str, Any]:
    """Run all quality checks and return a result dict.

    Returns:
        Dict with keys: ``valid`` (bool), ``missing_fields`` (list),
        ``type_mismatch`` (bool).
    """
    missing = check_required_fields(resource, required_fields)
    type_ok = validate_resource_type(resource, expected_type)

    return {
        "valid": len(missing) == 0 and type_ok,
        "missing_fields": missing,
        "type_mismatch": not type_ok,
    }