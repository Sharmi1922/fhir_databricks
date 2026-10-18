"""Tests for FHIR data quality checks."""

from fhir_lakehouse.transformations.quality import (
    check_required_fields,
    validate_resource_type,
    check_quality,
)


def test_check_required_fields_all_present():
    resource = {"resourceType": "Patient", "id": "1", "gender": "male"}
    missing = check_required_fields(resource, ["id", "gender"])
    assert missing == []


def test_check_required_fields_some_missing():
    resource = {"resourceType": "Patient", "id": "1"}
    missing = check_required_fields(resource, ["id", "gender", "birthDate"])
    assert sorted(missing) == ["birthDate", "gender"]


def test_check_required_fields_null_value():
    resource = {"resourceType": "Patient", "id": "1", "gender": None}
    missing = check_required_fields(resource, ["id", "gender"])
    assert "gender" in missing


def test_validate_resource_type_correct():
    resource = {"resourceType": "Patient", "id": "1"}
    assert validate_resource_type(resource, "Patient") is True


def test_validate_resource_type_mismatch():
    resource = {"resourceType": "Observation", "id": "1"}
    assert validate_resource_type(resource, "Patient") is False


def test_validate_resource_type_missing():
    resource = {"id": "1"}
    assert validate_resource_type(resource, "Patient") is False


def test_check_quality_valid():
    resource = {
        "resourceType": "Patient",
        "id": "1",
        "gender": "male",
        "birthDate": "1990-01-01",
    }
    result = check_quality(resource, "Patient", ["id", "gender", "birthDate"])
    assert result["valid"] is True
    assert result["missing_fields"] == []
    assert result["type_mismatch"] is False


def test_check_quality_invalid():
    resource = {
        "resourceType": "Observation",
        "id": "1",
    }
    result = check_quality(resource, "Patient", ["id", "gender"])
    assert result["valid"] is False
    assert "gender" in result["missing_fields"]
    assert result["type_mismatch"] is True