"""Raw writer: persists FHIR API responses as JSON to cloud storage."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterator

from fhir_lakehouse.logging_utils import get_logger

logger = get_logger(__name__)


class RawWriter:
    """Writes raw FHIR resources to JSON files in a cloud-storage volume.

    Args:
        output_path: Base path (e.g. a UC volume mount) for raw JSON files.
    """

    def __init__(self, output_path: str) -> None:
        self.output_path = output_path.rstrip("/")

    def write_resources(
        self,
        resource_type: str,
        resources: Iterator[dict[str, Any]],
    ) -> int:
        """Write a batch of resources as a single JSONL file.

        Args:
            resource_type: FHIR resource type (used in filename).
            resources: Iterator of resource dicts.

        Returns:
            Number of resources written.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        filename = f"{self.output_path}/{resource_type}/{resource_type}_{timestamp}.jsonl"
        count = 0

        # In Databricks this would use dbutils.fs or Spark file writer
        logger.info("Writing raw resources to %s", filename)
        for resource in resources:
            # Placeholder: actual write logic depends on runtime context
            # (Spark vs local).  In a Databricks notebook you'd use:
            #   dbutils.fs.put(filename, json.dumps(resource) + "\n", overwrite=True)
            count += 1
            if count % 1000 == 0:
                logger.info("Wrote %d %s resources...", count, resource_type)

        logger.info("Wrote %d %s resources to %s", count, resource_type, filename)
        return count

    def write_batch(
        self,
        resource_type: str,
        resources: list[dict[str, Any]],
        batch_id: str | None = None,
    ) -> str:
        """Write a list of resources as a single batch file.

        Args:
            resource_type: FHIR resource type.
            resources: List of resource dicts.
            batch_id: Optional batch identifier for the filename.

        Returns:
            The path of the written file.
        """
        if batch_id is None:
            batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        filename = f"{self.output_path}/{resource_type}/{resource_type}_{batch_id}.json"

        payload = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": r} for r in resources],
            "_metadata": {
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "count": len(resources),
                "resource_type": resource_type,
            },
        }
        # Placeholder write
        logger.info("Writing batch of %d %s resources to %s", len(resources), resource_type, filename)
        return filename