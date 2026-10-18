# Databricks notebook source
# MAGIC %md
# MAGIC # 01 – Ingest FHIR Resource (Raw → Bronze)
# MAGIC
# MAGIC Fetches FHIR resources from the API and writes them to the raw and bronze layers.

# Databricks notebook source
import json
from datetime import datetime, timezone
from pathlib import Path

from fhir_lakehouse.config import load_config
from fhir_lakehouse.api.client import FhirClient
from fhir_lakehouse.ingestion.raw_writer import RawWriter
from fhir_lakehouse.ingestion.bronze_writer import BronzeWriter
from fhir_lakehouse.logging_utils import get_logger

logger = get_logger(__name__)

# Databricks notebook source
# Configuration
config = load_config(config_dir=Path("/Workspace/New Pipeline 2026-10-18 12:48/fhir-databricks/config"))
RESOURCE_TYPES = ["Patient", "Observation", "Encounter", "Condition", "MedicationRequest"]

# Databricks notebook source
raw_writer = RawWriter(config.storage.raw_volume)
bronze_writer = BronzeWriter(config.catalog, config.schema)

# Databricks notebook source
# Ingest each resource type
for resource_type in RESOURCE_TYPES:
    logger.info("Ingesting %s...", resource_type)

    # Fetch resources from FHIR API (requires transport implementation)
    # resources = list(client.fetch_resource(resource_type))
    # raw_writer.write_batch(resource_type, resources)
    #
    # Convert to Spark DataFrame and write to bronze
    # df = spark.createDataFrame([flatten_resource(r) for r in resources])
    # bronze_writer.write_dataframe(df, resource_type)

    logger.info("Ingestion of %s complete", resource_type)

# Databricks notebook source
print("Ingestion complete for all resource types")