"""FHIR resource parsers: extract and flatten FHIR JSON resources."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional


def parse_resource(raw_json: str | dict[str, Any]) -> dict[str, Any]:
    """Parse a raw FHIR resource from JSON string or dict.

    Args:
        raw_json: JSON string or pre-parsed dict.

    Returns:
        Parsed FHIR resource dict.
    """
    if isinstance(raw_json, str):
        return json.loads(raw_json)
    return raw_json


def flatten_resource(
    resource: dict[str, Any],
    prefix: str = "",
    max_depth: int = 3,
) -> dict[str, Any]:
    """Flatten a nested FHIR resource into a single-level dict.

    Nested objects are joined with ``_``.  Arrays become JSON strings.

    Args:
        resource: FHIR resource dict.
        prefix: Key prefix for nested fields.
        max_depth: Maximum nesting depth before falling back to JSON string.

    Returns:
        Flattened dict.
    """
    result: dict[str, Any] = {}

    for key, value in resource.items():
        full_key = f"{prefix}_{key}" if prefix else key

        if isinstance(value, dict) and max_depth > 0:
            result.update(flatten_resource(value, full_key, max_depth - 1))
        elif isinstance(value, list):
            result[full_key] = json.dumps(value, default=str)
        else:
            result[full_key] = value

    return result


def extract_reference_id(reference: Optional[str]) -> Optional[str]:
    """Extract the ID portion from a FHIR reference string (e.g. 'Patient/123' -> '123')."""
    if not reference:
        return None
    parts = reference.split("/")
    return parts[-1] if parts else None


def get_resource_metadata(resource: dict[str, Any]) -> dict[str, Any]:
    """Extract common metadata fields from a FHIR resource."""
    return {
        "resource_id": resource.get("id"),
        "resource_type": resource.get("resourceType"),
        "last_updated": resource.get("meta", {}).get("lastUpdated"),
        "version_id": resource.get("meta", {}).get("versionId"),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }