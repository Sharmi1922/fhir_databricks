"""Gold layer: Aggregated analytics views from silver tables.

All silver tables use SCD Type 2, so gold views filter for current
records only (__END_AT IS NULL) to get the latest version of each resource.
Metadata: _refreshed_at timestamp on every gold view.
"""

from pyspark import pipelines as dp
from pyspark.sql.functions import col, count, current_timestamp, lit


@dp.materialized_view(
    name="gold_patient_summary",
    comment="Patient count by gender",
)
def gold_patient_summary():
    """Aggregate current patient counts by gender."""
    return (
        spark.read.table("silver_patient")
        .filter(col("__END_AT").isNull())
        .groupBy("gender")
        .agg(count("*").alias("patient_count"))
        .orderBy("gender")
        .withColumn("_refreshed_at", current_timestamp())
    )


@dp.materialized_view(
    name="gold_observation_summary",
    comment="Observation count by status",
)
def gold_observation_summary():
    """Aggregate current observation counts by status."""
    return (
        spark.read.table("silver_observation")
        .filter(col("__END_AT").isNull())
        .groupBy("status")
        .agg(count("*").alias("observation_count"))
        .orderBy("status")
        .withColumn("_refreshed_at", current_timestamp())
    )


@dp.materialized_view(
    name="gold_encounter_summary",
    comment="Encounter count by status",
)
def gold_encounter_summary():
    """Aggregate current encounter counts by status."""
    return (
        spark.read.table("silver_encounter")
        .filter(col("__END_AT").isNull())
        .groupBy("status")
        .agg(count("*").alias("encounter_count"))
        .orderBy("status")
        .withColumn("_refreshed_at", current_timestamp())
    )


@dp.materialized_view(
    name="gold_condition_summary",
    comment="Total condition count",
)
def gold_condition_summary():
    """Count current conditions in the silver layer."""
    return (
        spark.read.table("silver_condition")
        .filter(col("__END_AT").isNull())
        .agg(count("*").alias("condition_count"))
        .withColumn("_refreshed_at", current_timestamp())
    )


@dp.materialized_view(
    name="gold_resource_overview",
    comment="Total record counts across all resource types",
)
def gold_resource_overview():
    """Overview of current record counts across all silver tables."""
    patients = spark.read.table("silver_patient").filter(col("__END_AT").isNull()).select(lit("Patient").alias("resource_type"))
    observations = spark.read.table("silver_observation").filter(col("__END_AT").isNull()).select(lit("Observation").alias("resource_type"))
    encounters = spark.read.table("silver_encounter").filter(col("__END_AT").isNull()).select(lit("Encounter").alias("resource_type"))
    conditions = spark.read.table("silver_condition").filter(col("__END_AT").isNull()).select(lit("Condition").alias("resource_type"))
    medication_requests = spark.read.table("silver_medication_request").filter(col("__END_AT").isNull()).select(lit("MedicationRequest").alias("resource_type"))

    return (
        patients
        .union(observations)
        .union(encounters)
        .union(conditions)
        .union(medication_requests)
        .groupBy("resource_type")
        .agg(count("*").alias("record_count"))
        .orderBy("resource_type")
        .withColumn("_refreshed_at", current_timestamp())
    )
