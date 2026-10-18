"""SCD Type 2 utilities: content hashing and change detection for FHIR resources."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional


def compute_hash(resource: dict[str, Any], exclude_fields: Optional[list[str]] = None) -> str:
    """Compute a deterministic SHA-256 hash of a FHIR resource.

    Args:
        resource: FHIR resource dict.
        exclude_fields: Fields to exclude from hashing (e.g. ``meta`` with version info).

    Returns:
        Hex digest string.
    """
    exclude_fields = exclude_fields or ["meta", "id", "resourceType"]
    filtered = {
        k: v for k, v in sorted(resource.items())
        if k not in exclude_fields
    }
    payload = json.dumps(filtered, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def has_changed(
    current: dict[str, Any],
    previous_hash: Optional[str],
    exclude_fields: Optional[list[str]] = None,
) -> bool:
    """Check whether a resource has changed since the last known hash.

    Args:
        current: Current FHIR resource dict.
        previous_hash: Hash of the previous version (None means new resource).
        exclude_fields: Fields to exclude from hashing.

    Returns:
        True if the resource is new or changed.
    """
    current_hash = compute_hash(current, exclude_fields)
    return current_hash != previous_hash


def build_scd2_record(
    resource: dict[str, Any],
    previous_hash: Optional[str],
    start_at: str,
    end_at: Optional[str] = None,
    exclude_fields: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Build an SCD2 record for a FHIR resource.

    Args:
        resource: FHIR resource dict.
        previous_hash: Hash of previous version (None for new).
        start_at: Value for ``__START_AT`` column.
        end_at: Value for ``__END_AT`` column (None means current/active).
        exclude_fields: Fields to exclude from hashing.

    Returns:
        Dict with resource fields plus SCD2 columns.
    """
    record = dict(resource)
    record["__START_AT"] = start_at
    record["__END_AT"] = end_at
    record["__HASH"] = compute_hash(resource, exclude_fields)
    record["__IS_CURRENT"] = end_at is None
    record["__IS_NEW"] = previous_hash is None
    record["__CHANGED"] = has_changed(resource, previous_hash, exclude_fields)
    return record