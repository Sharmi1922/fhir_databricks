"""Configuration loading utilities for the FHIR Lakehouse."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


@dataclass
class FhirApiConfig:
    base_url: str = ""
    auth_token: str = ""
    page_size: int = 100
    rate_limit_per_second: int = 10
    timeout_seconds: int = 30
    retry_max: int = 3


@dataclass
class StorageConfig:
    raw_volume: str = ""
    bronze_volume: str = ""
    checkpoint_location: str = ""


@dataclass
class Scd2Config:
    effective_from_col: str = "__START_AT"
    effective_to_col: str = "__END_AT"
    key_columns: list[str] = field(default_factory=lambda: ["resource_id"])
    sequence_by: str = "last_updated"


@dataclass
class AppConfig:
    environment: str = "dev"
    catalog: str = ""
    schema: str = ""
    fhir_api: FhirApiConfig = field(default_factory=FhirApiConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    scd2: Scd2Config = field(default_factory=Scd2Config)


def load_config(env: str | None = None, config_dir: Path | None = None) -> AppConfig:
    """Load YAML configuration for the given environment.

    Args:
        env: Environment name (e.g. "dev", "prod"). Defaults to ``FHIR_ENV`` or ``dev``.
        config_dir: Directory containing YAML files. Defaults to the project config/ folder.

    Returns:
        Parsed AppConfig instance.
    """
    env = env or os.getenv("FHIR_ENV", "dev")
    config_dir = config_dir or DEFAULT_CONFIG_DIR
    config_path = config_dir / f"{env}.yaml"

    with open(config_path, "r") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    return AppConfig(
        environment=raw.get("environment", env),
        catalog=raw.get("catalog", ""),
        schema=raw.get("schema", ""),
        fhir_api=FhirApiConfig(**raw.get("fhir_api", {})),
        storage=StorageConfig(**raw.get("storage", {})),
        scd2=Scd2Config(**raw.get("scd2", {})),
    )


def load_resource_config(config_dir: Path | None = None) -> dict[str, Any]:
    """Load the resource-type configuration (field mappings, partition keys).

    Returns:
        Dict keyed by FHIR resource type.
    """
    config_dir = config_dir or DEFAULT_CONFIG_DIR
    resources_path = config_dir / "resources.yaml"
    with open(resources_path, "r") as f:
        return yaml.safe_load(f) or {}