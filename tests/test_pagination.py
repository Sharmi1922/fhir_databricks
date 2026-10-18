"""Tests for FHIR Bundle pagination utilities."""

import pytest

from fhir_lakehouse.api.pagination import _extract_next_url, paginate_bundles


def test_extract_next_url_found():
    bundle = {
        "link": [
            {"relation": "self", "url": "http://example.com/Patient"},
            {"relation": "next", "url": "http://example.com/Patient?_offset=2"},
        ]
    }
    assert _extract_next_url(bundle) == "http://example.com/Patient?_offset=2"


def test_extract_next_url_not_found():
    bundle = {
        "link": [
            {"relation": "self", "url": "http://example.com/Patient"},
        ]
    }
    assert _extract_next_url(bundle) is None


def test_extract_next_url_empty_bundle():
    assert _extract_next_url({}) is None


def test_paginate_bundles_single_page():
    bundles = [
        {"resourceType": "Bundle", "entry": [{"resource": {"id": "1"}}], "link": []},
    ]

    def get_fn(path, params=None):
        return bundles[0]

    results = list(paginate_bundles(get_fn, "Patient", base_url="http://example.com"))
    assert len(results) == 1
    assert results[0]["entry"][0]["resource"]["id"] == "1"


def test_paginate_bundles_multi_page():
    page1 = {
        "resourceType": "Bundle",
        "entry": [{"resource": {"id": "1"}}],
        "link": [{"relation": "next", "url": "http://example.com/Patient?_offset=2"}],
    }
    page2 = {
        "resourceType": "Bundle",
        "entry": [{"resource": {"id": "2"}}],
        "link": [],
    }

    call_count = [0]

    def get_fn(path, params=None):
        if call_count[0] == 0:
            call_count[0] += 1
            return page1
        return page2

    results = list(paginate_bundles(get_fn, "Patient", base_url="http://example.com"))
    assert len(results) == 2
    assert results[0]["entry"][0]["resource"]["id"] == "1"
    assert results[1]["entry"][0]["resource"]["id"] == "2"