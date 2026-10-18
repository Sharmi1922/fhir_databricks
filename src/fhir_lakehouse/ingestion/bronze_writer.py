"""Bronze writer: converts raw FHIR JSON into Delta tables (bronze layer)."""

from __future__ import annotations

from typing import Any, Optional

from fhir_lakehouse.logging_utils import get_logger

logger = get_logger(__name__)


class BronzeWriter:
    """Writes FHIR resources into Delta-format bronze tables.

    Args:
        catalog: Unity Catalog name.
        schema: Schema name.
        table_prefix: Prefix for bronze table names (e.g. "bronze_").
    """

    def __init__(self, catalog: str, schema: str, table_prefix: str = "bronze_") -> None:
        self.catalog = catalog
        self.schema = schema
        self.table_prefix = table_prefix

    @property
    def fully_qualified_schema(self) -> str:
        return f"{self.catalog}.{self.schema}"

    def table_name(self, resource_type: str) -> str:
        """Return the fully-qualified bronze table name for a resource type."""
        return f"{self.fully_qualified_schema}.{self.table_prefix}{resource_type.lower()}"

    def write_dataframe(self, df: Any, resource_type: str, mode: str = "append") -> None:
        """Write a Spark DataFrame to the bronze Delta table.

        Args:
            df: Spark DataFrame containing parsed FHIR resources.
            resource_type: FHIR resource type.
            mode: Write mode ("append" or "overwrite").
        """
        table = self.table_name(resource_type)
        logger.info("Writing %s to %s (mode=%s)", resource_type, table, mode)
        (
            df.write
            .format("delta")
            .mode(mode)
            .option("mergeSchema", "true")
            .saveAsTable(table)
        )

    def read_table(self, resource_type: str) -> Any:
        """Read the bronze table for a resource type as a Spark DataFrame.

        Args:
            resource_type: FHIR resource type.

        Returns:
            Spark DataFrame.
        """
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        table = self.table_name(resource_type)
        logger.info("Reading bronze table %s", table)
        return spark.read.table(table)