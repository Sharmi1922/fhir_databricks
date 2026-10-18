# Databricks notebook source
from fhir_lakehouse.config import load_config, load_resource_config
from fhir_lakehouse.transformations.quality import check_quality
from fhir_lakehouse.logging_utils import get_logger

logger = get_logger(__name__)

# Databricks notebook source
config = load_config()
resource_config = load_resource_config()

# Databricks notebook source
for resource_type, settings in resource_config.get("resources", {}).items():
    logger.info("Running DQ checks for %s", resource_type)

    silver_table = f"{config.catalog}.{config.schema}.silver_{resource_type.lower()}"
    df = spark.read.table(silver_table)

    expected_fields = settings.get("expected_fields", [])
    total_count = df.count()

    # Check for nulls in expected fields
    for field in expected_fields:
        null_count = df.filter(f"{field} IS NULL").count()
        if null_count > 0:
            logger.warning(
                "%s.%s has %d nulls out of %d rows",
                resource_type, field, null_count, total_count,
            )

    logger.info("DQ check for %s complete (%d rows)", resource_type, total_count)

# Databricks notebook source
print("Data quality checks complete")