# Databricks notebook source
CATALOG = "fhir_catalog_dev"
SCHEMA = "fhir_schema_dev"

# Databricks notebook source
spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
spark.sql(f"USE SCHEMA {SCHEMA}")

# Databricks notebook source
# Create volumes for raw, bronze, and checkpoint storage
for volume in ["raw", "bronze", "silver", "gold", "checkpoints"]:
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {volume}")

# Databricks notebook source
print(f"Setup complete: {CATALOG}.{SCHEMA}")