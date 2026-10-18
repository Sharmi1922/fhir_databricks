"""Silver layer: SCD Type 2 tracking for FHIR resources.

Uses Auto CDC (dp.create_auto_cdc_flow) with stored_as_scd_type=2 to maintain
full change history for each FHIR resource type. Each silver table includes
__START_AT and __END_AT columns for SCD2 validity tracking.

Resource types are defined once in RESOURCE_TYPES to avoid hardcoding.
Metadata: _processed_at timestamp added per resource in temporary views.
"""

from pyspark import pipelines as dp
from pyspark.sql.functions import col, current_timestamp

# Single source of truth for resource types -- no hardcoding per table
RESOURCE_TYPES = [
    "Patient",
    "Observation",
    "Encounter",
    "Condition",
    "MedicationRequest",
]


# ---------------------------------------------------------------------------
# Temporary views: filter bronze by resource type, add _processed_at metadata
# Auto CDC reads from these views as its source.
# ---------------------------------------------------------------------------

@dp.temporary_view()
def bronze_patient_changes():
    """Filtered Patient changes from bronze for Auto CDC."""
    return (
        spark.readStream.table("bronze_fhir_raw")
        .filter(col("resourceType") == "Patient")
        .filter(col("id").isNotNull())
        .withColumn("_processed_at", current_timestamp())
    )


@dp.temporary_view()
def bronze_observation_changes():
    """Filtered Observation changes from bronze for Auto CDC."""
    return (
        spark.readStream.table("bronze_fhir_raw")
        .filter(col("resourceType") == "Observation")
        .filter(col("id").isNotNull())
        .withColumn("_processed_at", current_timestamp())
    )


@dp.temporary_view()
def bronze_encounter_changes():
    """Filtered Encounter changes from bronze for Auto CDC."""
    return (
        spark.readStream.table("bronze_fhir_raw")
        .filter(col("resourceType") == "Encounter")
        .filter(col("id").isNotNull())
        .withColumn("_processed_at", current_timestamp())
    )


@dp.temporary_view()
def bronze_condition_changes():
    """Filtered Condition changes from bronze for Auto CDC."""
    return (
        spark.readStream.table("bronze_fhir_raw")
        .filter(col("resourceType") == "Condition")
        .filter(col("id").isNotNull())
        .withColumn("_processed_at", current_timestamp())
    )


@dp.temporary_view()
def bronze_medication_request_changes():
    """Filtered MedicationRequest changes from bronze for Auto CDC."""
    return (
        spark.readStream.table("bronze_fhir_raw")
        .filter(col("resourceType") == "MedicationRequest")
        .filter(col("id").isNotNull())
        .withColumn("_processed_at", current_timestamp())
    )


# ---------------------------------------------------------------------------
# SCD Type 2 streaming tables (targets for Auto CDC flows)
# Auto CDC adds __START_AT and __END_AT columns automatically.
# ---------------------------------------------------------------------------

dp.create_streaming_table(
    name="silver_patient",
    comment="SCD2 Patient resources with full change history",
    cluster_by=["id"],
)

dp.create_streaming_table(
    name="silver_observation",
    comment="SCD2 Observation resources with full change history",
    cluster_by=["id"],
)

dp.create_streaming_table(
    name="silver_encounter",
    comment="SCD2 Encounter resources with full change history",
    cluster_by=["id"],
)

dp.create_streaming_table(
    name="silver_condition",
    comment="SCD2 Condition resources with full change history",
    cluster_by=["id"],
)

dp.create_streaming_table(
    name="silver_medication_request",
    comment="SCD2 MedicationRequest resources with full change history",
    cluster_by=["id"],
)


# ---------------------------------------------------------------------------
# Auto CDC flows: apply changes with SCD Type 2
# sequence_by = _source_timestamp (FHIR meta.lastUpdated) for true chronology
# stored_as_scd_type=2 maintains full history with __START_AT/__END_AT
# ---------------------------------------------------------------------------

dp.create_auto_cdc_flow(
    target="silver_patient",
    source="bronze_patient_changes",
    keys=["id"],
    sequence_by="_source_timestamp",
    stored_as_scd_type=2,
)

dp.create_auto_cdc_flow(
    target="silver_observation",
    source="bronze_observation_changes",
    keys=["id"],
    sequence_by="_source_timestamp",
    stored_as_scd_type=2,
)

dp.create_auto_cdc_flow(
    target="silver_encounter",
    source="bronze_encounter_changes",
    keys=["id"],
    sequence_by="_source_timestamp",
    stored_as_scd_type=2,
)

dp.create_auto_cdc_flow(
    target="silver_condition",
    source="bronze_condition_changes",
    keys=["id"],
    sequence_by="_source_timestamp",
    stored_as_scd_type=2,
)

dp.create_auto_cdc_flow(
    target="silver_medication_request",
    source="bronze_medication_request_changes",
    keys=["id"],
    sequence_by="_source_timestamp",
    stored_as_scd_type=2,
)
