# Databricks notebook source
# MAGIC %md
# MAGIC # 02 – Bronze to Silver Transformation
# MAGIC
# MAGIC Reads bronze tables, applies quality checks, deduplication, and SCD2 tracking.
# MAGIC This notebook is a skeleton – fill in the write logic before running.

# Databricks notebook source
from fhir_lakehouse.config import load_config
from fhir_lakehouse.transformations.quality import check_required_fields
from fhir_lakehouse.transformations.scd2 import compute_hash
from fhir_lakehouse.logging_utils import get_logger

logger = get_logger(__name__)

# Databricks notebook source
config = load_config()
RESOURCE_TYPES = ["Patient", "Observation", "Encounter", "Condition", "MedicationRequest"]

# Databricks notebook source
for resource_type in RESOURCE_TYPES:
    logger.info("Transforming %s: bronze -> silver", resource_type)

    bronze_table = f"{config.catalog}.{config.schema}.bronze_{resource_type.lower()}"
    silver_table = f"{config.catalog}.{config.schema}.silver_{resource_type.lower()}"

    df = spark.read.table(bronze_table)

    # Deduplicate: keep latest version per resource_id
    # df_silver = (
    #     df.withColumn("_hash", compute_hash(df))
    #     .dropDuplicates(["resource_id"])
    # )

    # Write to silver (choose mode based on your pipeline requirements)
    # df_silver.write.format("delta").mode("append").saveAsTable(silver_table)

    logger.info("Silver transformation for %s ready to write", resource_type)

# Databricks notebook source
print("Bronze -> Silver transformation skeleton ready")