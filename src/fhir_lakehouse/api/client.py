"""FHIR API client for fetching resources from a FHIR R4 server.

The HTTP transport is injected so this module stays testable and does
not make direct network calls on its own.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Iterator, Optional, Protocol

from fhir_lakehouse.api.pagination import paginate_bundles
from fhir_lakehouse.config import FhirApiConfig
from fhir_lakehouse.logging_utils import get_logger

logger = get_logger(__name__)


class HttpTransport(Protocol):
    """Protocol for an injectable HTTP transport."""

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Fetch JSON from path with optional query params."""
        ...


class FhirClient:
    """Client for interacting with a FHIR R4 REST API.

    Args:
        config: FhirApiConfig instance with connection settings.
        transport: Injectable HTTP transport that implements ``get(path, params)``.
    """

    def __init__(self, config: FhirApiConfig, transport: HttpTransport) -> None:
        self.config = config
        self._transport = transport

    def _get_with_retry(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Fetch via transport with configurable retry logic."""
        for attempt in range(1, self.config.retry_max + 1):
            try:
                logger.debug("GET %s (attempt %d/%d)", path, attempt, self.config.retry_max)
                return self._transport.get(path, params)
            except Exception as e:
                logger.warning("Request failed (attempt %d): %s", attempt, e)
                if attempt == self.config.retry_max:
                    raise
                time.sleep(2 ** (attempt - 1))
        raise RuntimeError("Exhausted retries")

    def fetch_resource(
        self,
        resource_type: str,
        params: Optional[dict] = None,
    ) -> Iterator[dict[str, Any]]:
        """Fetch all resources of a given type, paginating automatically.

        Args:
            resource_type: FHIR resource type (e.g. "Patient", "Observation").
            params: Optional query params (e.g. {"_count": "100"}).

        Yields:
            Individual FHIR resource dicts.
        """
        if params is None:
            params = {"_count": str(self.config.page_size)}
        elif "_count" not in params:
            params["_count"] = str(self.config.page_size)

        for bundle in paginate_bundles(
            self._get_with_retry, resource_type, params, self.config.base_url
        ):
            for entry in bundle.get("entry", []):
                yield entry.get("resource", {})

    def fetch_resource_by_id(self, resource_type: str, resource_id: str) -> dict[str, Any]:
        """Fetch a single resource by ID."""
        return self._get_with_retry(f"{resource_type}/{resource_id}")