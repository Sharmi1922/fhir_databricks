"""Bronze layer: Raw FHIR resources ingested via Auto Loader.

All paths and version info are parameterized via Spark conf:
  - fhir.raw_volume.path  (default /Volumes/workspace/default/raw)
  - fhir.pipeline.version (default 1.0.0)
"""

from pyspark import pipelines as dp
from pyspark.sql.functions import coalesce, col, current_timestamp, lit, to_timestamp


@dp.table(
    name="bronze_fhir_raw",
    comment="Raw FHIR resources ingested via Auto Loader with full metadata",
)
def bronze_fhir_raw():
    """Read raw FHIR JSON files from the configured volume using Auto Loader.

    Metadata columns added:
      _ingested_at       - pipeline processing timestamp
      _source_timestamp  - FHIR meta.lastUpdated (falls back to _ingested_at)
      _source_file       - path of the source JSON file
      _pipeline_version  - version string from pipeline config
    """
    raw_path = spark.conf.get("fhir.raw_volume.path", "/Volumes/workspace/default/raw")
    pipeline_version = spark.conf.get("fhir.pipeline.version", "1.0.0")

    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("multiLine", "true")
        .load(raw_path)
        .withColumn("_ingested_at", current_timestamp())
        .withColumn("_source_timestamp", coalesce(to_timestamp(col("meta.lastUpdated")), current_timestamp()))
        .withColumn("_source_file", col("_metadata.file_path"))
        .withColumn("_pipeline_version", lit(pipeline_version))
    )
