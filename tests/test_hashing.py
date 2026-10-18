"""Tests for SCD2 content hashing utilities."""

from fhir_lakehouse.transformations.scd2 import compute_hash, has_changed, build_scd2_record


def test_compute_hash_deterministic():
    resource = {"resourceType": "Patient", "id": "123", "gender": "male", "active": True}
    h1 = compute_hash(resource)
    h2 = compute_hash(resource)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest


def test_compute_hash_excludes_meta_and_id():
    r1 = {"resourceType": "Patient", "id": "123", "gender": "male"}
    r2 = {"resourceType": "Patient", "id": "456", "gender": "male"}
    assert compute_hash(r1) == compute_hash(r2)


def test_compute_hash_different_content():
    r1 = {"resourceType": "Patient", "id": "1", "gender": "male"}
    r2 = {"resourceType": "Patient", "id": "1", "gender": "female"}
    assert compute_hash(r1) != compute_hash(r2)


def test_has_changed_new_resource():
    resource = {"resourceType": "Patient", "id": "1", "gender": "male"}
    assert has_changed(resource, None) is True


def test_has_changed_same_content():
    resource = {"resourceType": "Patient", "id": "1", "gender": "male"}
    h = compute_hash(resource)
    assert has_changed(resource, h) is False


def test_has_changed_different_content():
    resource = {"resourceType": "Patient", "id": "1", "gender": "male"}
    h = compute_hash(resource)
    resource["gender"] = "female"
    assert has_changed(resource, h) is True


def test_build_scd2_record():
    resource = {"resourceType": "Patient", "id": "1", "gender": "male"}
    record = build_scd2_record(resource, None, start_at="2024-01-01T00:00:00Z")
    assert record["__START_AT"] == "2024-01-01T00:00:00Z"
    assert record["__END_AT"] is None
    assert record["__IS_CURRENT"] is True
    assert record["__IS_NEW"] is True
    assert record["__CHANGED"] is True
    assert "__HASH" in record


def test_build_scd2_record_closed_record():
    resource = {"resourceType": "Patient", "id": "1", "gender": "male"}
    record = build_scd2_record(
        resource, compute_hash(resource),
        start_at="2024-01-01T00:00:00Z",
        end_at="2024-06-01T00:00:00Z",
    )
    assert record["__IS_CURRENT"] is False
    assert record["__IS_NEW"] is False