"""Gold-layer analytics queries for FHIR data."""

from __future__ import annotations

from typing import Any

from fhir_lakehouse.logging_utils import get_logger

logger = get_logger(__name__)


class GoldAggregator:
    """Builds gold-layer aggregation views from silver tables.

    Args:
        catalog: Unity Catalog name.
        schema: Schema name.
    """

    def __init__(self, catalog: str, schema: str) -> None:
        self.catalog = catalog
        self.schema = schema

    @property
    def fully_qualified_schema(self) -> str:
        return f"{self.catalog}.{self.schema}"

    def _silver_table(self, resource_type: str) -> str:
        return f"{self.fully_qualified_schema}.silver_{resource_type.lower()}"

    def _gold_table(self, name: str) -> str:
        return f"{self.fully_qualified_schema}.gold_{name}"

    def patient_summary(self, spark: Any) -> Any:
        """Create a patient summary aggregation.

        Args:
            spark: SparkSession instance.

        Returns:
            Spark DataFrame with patient summary.
        """
        silver_patient = self._silver_table("patient")
        logger.info("Building patient summary from %s", silver_patient)

        return (
            spark.read.table(silver_patient)
            .groupBy("gender")
            .count()
            .withColumnRenamed("count", "patient_count")
            .orderBy("gender")
        )

    def observation_summary(self, spark: Any) -> Any:
        """Create an observation summary aggregation.

        Args:
            spark: SparkSession instance.

        Returns:
            Spark DataFrame with observation counts by status.
        """
        silver_obs = self._silver_table("observation")
        logger.info("Building observation summary from %s", silver_obs)

        return (
            spark.read.table(silver_obs)
            .groupBy("status")
            .count()
            .withColumnRenamed("count", "observation_count")
            .orderBy("status")
        )

    def encounter_summary(self, spark: Any) -> Any:
        """Create an encounter summary aggregation.

        Args:
            spark: SparkSession instance.

        Returns:
            Spark DataFrame with encounter counts by status.
        """
        silver_enc = self._silver_table("encounter")
        logger.info("Building encounter summary from %s", silver_enc)

        return (
            spark.read.table(silver_enc)
            .groupBy("status")
            .count()
            .withColumnRenamed("count", "encounter_count")
            .orderBy("status")
        )

    def write_gold_table(self, df: Any, table_name: str, mode: str = "overwrite") -> None:
        """Write a gold DataFrame to a Delta table.

        Args:
            df: Spark DataFrame.
            table_name: Gold table name (without gold_ prefix).
            mode: Write mode.
        """
        table = self._gold_table(table_name)
        logger.info("Writing gold table %s (mode=%s)", table, mode)
        (
            df.write
            .format("delta")
            .mode(mode)
            .saveAsTable(table)
        )