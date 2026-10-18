# Databricks notebook source
# MAGIC %md
# MAGIC # 03 – Silver to Gold Aggregation
# MAGIC
# MAGIC Creates gold-layer summary tables from silver for analytics and dashboards.

# Databricks notebook source
from fhir_lakehouse.config import load_config
from fhir_lakehouse.analytics.gold import GoldAggregator
from fhir_lakehouse.logging_utils import get_logger

logger = get_logger(__name__)

# Databricks notebook source
config = load_config()
aggregator = GoldAggregator(config.catalog, config.schema)

# Databricks notebook source
# Patient summary
df_patient = aggregator.patient_summary(spark)
aggregator.write_gold_table(df_patient, "patient_summary")

# Databricks notebook source
# Observation summary
df_obs = aggregator.observation_summary(spark)
aggregator.write_gold_table(df_obs, "observation_summary")

# Databricks notebook source
# Encounter summary
df_enc = aggregator.encounter_summary(spark)
aggregator.write_gold_table(df_enc, "encounter_summary")

# Databricks notebook source
print("Silver → Gold aggregation complete")