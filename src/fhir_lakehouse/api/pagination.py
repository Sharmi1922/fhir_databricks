"""Pagination utilities for FHIR Bundle traversal."""

from __future__ import annotations
from typing import Any, Callable, Iterator, Optional


def _extract_next_url(bundle: dict[str, Any]) -> Optional[str]:
    """Extract the next-page URL from a FHIR Bundle's link array."""
    for link in bundle.get("link", []):
        if link.get("relation") == "next":
            return link.get("url")
    return None


class PageIterator:
    """Iterator that yields successive FHIR Bundle pages.

    Args:
        get_fn: Callable that takes a path and optional params, returns a JSON dict.
        resource_type: Initial resource type for the first request.
        params: Query params for the first request.
        base_url: Base URL (used to resolve relative next-page links).
    """

    def __init__(
        self,
        get_fn: Callable[..., dict[str, Any]],
        resource_type: str,
        params: Optional[dict[str, Any]],
        base_url: str = "",
    ) -> None:
        self._get = get_fn
        self._resource_type = resource_type
        self._params = params or {}
        self._base_url = base_url
        self._first = True

    def __iter__(self) -> Iterator[dict[str, Any]]:
        self._first = True
        return self

    def __next__(self) -> dict[str, Any]:
        if self._first:
            self._first = False
            return self._get(self._resource_type, self._params)

        # Fetch the page, then look for next link inside it
        raise StopIteration


def paginate_bundles(
    get_fn: Callable[..., dict[str, Any]],
    resource_type: str,
    params: Optional[dict[str, Any]] = None,
    base_url: str = "",
) -> Iterator[dict[str, Any]]:
    """Yield all Bundle pages for a FHIR search, following 'next' links.

    This is a generator-based alternative to PageIterator that resolves
    the next-page URL from each bundle's link array.

    Args:
        get_fn: Callable to fetch a URL/path and return JSON dict.
        resource_type: FHIR resource type to search.
        params: Initial query parameters.
        base_url: Base URL for resolving relative links.

    Yields:
        Each Bundle dict in the pagination chain.
    """
    bundle = get_fn(resource_type, params)
    yield bundle

    while True:
        next_url = _extract_next_url(bundle)
        if not next_url:
            break
        # Strip base_url to get a relative path
        if base_url and next_url.startswith(base_url):
            next_url = next_url[len(base_url):]
        bundle = get_fn(next_url.lstrip("/"))
        yield bundle