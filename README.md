# FHIR Databricks Lakehouse

A Databricks lakehouse for ingesting, transforming, and analyzing FHIR (Fast Healthcare Interoperability Resources) data using a Spark Declarative Pipeline (SDP) with Medallion Architecture and SCD Type 2 change tracking.

## Requirements Checklist

| # | Requirement | Status |
|---|---|---|
| 1 | Ingest and transform 2-3 days of data with pagination | Done |
| 2 | Create Medallion Architecture (Raw → Bronze → Silver → Gold) | Done |
| 3 | Add metadata and versioning to all tables | Done |
| 4 | Ensure modular and reusable code (no hardcoding) | Done |
| 5 | SCD Type 2 in silver layer | Done |

---

## Architecture

```
FHIR API (pagination) → Raw Volume (JSON) → Bronze (Auto Loader) → Silver (SCD2 Auto CDC) → Gold (Aggregations)
```

### Medallion Architecture

| Layer | Storage | Technology | Tables |
|---|---|---|---|
| **Raw** | UC Volume `/Volumes/workspace/default/raw` | JSON files | 10 files (3 days) |
| **Bronze** | Delta streaming table | Auto Loader (`cloudFiles`) | `bronze_fhir_raw` |
| **Silver** | Delta streaming table (SCD2) | Auto CDC (`stored_as_scd_type=2`) | `silver_patient`, `silver_observation`, `silver_encounter`, `silver_condition`, `silver_medication_request` |
| **Gold** | Materialized views | Batch aggregations | `gold_patient_summary`, `gold_observation_summary`, `gold_encounter_summary`, `gold_condition_summary`, `gold_resource_overview` |

---

## Requirement 1: Ingest 2-3 Days with Pagination

### Pagination Implementation

The `fhir_lakehouse/api/` module provides production-ready FHIR API pagination:

- **`pagination.py`** – `paginate_bundles()` generator follows FHIR Bundle `link[next]` URLs to fetch all pages automatically.
- **`client.py`** – `FhirClient.fetch_resource()` yields individual resources across all pages with configurable retry logic and page size.

### Multi-Day Data

Sample data spans **3 days** (2024-01-15 to 2024-01-17):
- 10 FHIR JSON files across 5 resource types
- 3 versions of `patient-001` (address changed each day) to demonstrate SCD2
- Each file includes `meta.lastUpdated` and `meta.versionId` for change tracking

### Ingestion Workflow

1. **Notebook** (`notebooks/01_ingest_resource.py`) uses `FhirClient` with pagination to fetch resources from the FHIR API
2. **RawWriter** writes raw JSON to the UC volume
3. **SDP Pipeline** picks up files via Auto Loader and processes through bronze → silver → gold

---

## Requirement 2: Medallion Architecture

### Bronze Layer (`src/pipeline/bronze.py`)

- Uses **Auto Loader** (`cloudFiles` format) to incrementally read JSON from the raw volume
- Schema inference with `inferColumnTypes=true` and `multiLine=true` for pretty-printed JSON
- Creates a single streaming table `bronze_fhir_raw` containing all resource types

### Silver Layer (`src/pipeline/silver.py`)

- Creates **5 streaming tables** (one per FHIR resource type) using `dp.create_streaming_table()`
- Uses **Auto CDC** (`dp.create_auto_cdc_flow`) with `stored_as_scd_type=2` for full change history
- Temporary views filter bronze by `resourceType` and add `_processed_at` metadata
- SCD2 automatically adds `__START_AT` and `__END_AT` columns

### Gold Layer (`src/pipeline/gold.py`)

- 5 **materialized views** aggregating current silver data
- Filters for current SCD2 records only (`__END_AT IS NULL`)
- Supports incremental refresh on serverless compute

---

## Requirement 3: Metadata and Versioning

### Metadata Columns on All Tables

| Layer | Column | Description |
|---|---|---|
| Bronze | `_ingested_at` | Pipeline processing timestamp |
| Bronze | `_source_timestamp` | FHIR `meta.lastUpdated` (falls back to `_ingested_at`) |
| Bronze | `_source_file` | Source JSON file path (from `_metadata.file_path`) |
| Bronze | `_pipeline_version` | Version string from pipeline config |
| Silver | `_processed_at` | Silver layer processing timestamp |
| Silver | `__START_AT` | SCD2 validity start (Auto CDC) |
| Silver | `__END_AT` | SCD2 validity end – NULL means current (Auto CDC) |
| Gold | `_refreshed_at` | Materialized view refresh timestamp |

### SCD2 Versioning Example

`silver_patient` table for `patient-001`:

| Address | `__START_AT` | `__END_AT` | Status |
|---|---|---|---|
| Boston, MA | 2024-01-15 10:00 | 2024-01-16 11:00 | Superseded |
| New York, NY | 2024-01-16 11:00 | 2024-01-17 14:00 | Superseded |
| Chicago, IL | 2024-01-17 14:00 | NULL | Current |

---

## Requirement 4: Modular and Reusable Code

### No Hardcoding – Parameterized via Pipeline Configuration

All configurable values are defined in the pipeline settings (`configuration` field) and accessed via `spark.conf.get()`:

| Parameter | Default | Used In |
|---|---|---|
| `fhir.raw_volume.path` | `/Volumes/workspace/default/raw` | `bronze.py` |
| `fhir.pipeline.version` | `1.0.0` | `bronze.py` |

### Single Source of Truth for Resource Types

`silver.py` defines `RESOURCE_TYPES` as a Python list – no duplicated string literals across tables.

### Config System (`config/dev.yaml`)

The `fhir_lakehouse.config` module loads YAML configuration for API endpoints, storage paths, and resource types. Used by notebooks and utility code.

### Utility Package (`src/fhir_lakehouse/`)

Reusable Python package with dependency-injected components:
- `api/` – FHIR client with pagination and retry
- `ingestion/` – Raw and bronze writers
- `transformations/` – Resource parsers, quality checks, SCD2 hashing
- `analytics/` – Gold aggregation utilities

---

## Requirement 5: SCD Type 2 in Silver Layer

### Implementation

Silver tables use **Auto CDC** (`dp.create_auto_cdc_flow`) with `stored_as_scd_type=2`:

```python
# 1. Create target streaming table
dp.create_streaming_table(name="silver_patient", cluster_by=["id"])

# 2. Define CDC flow with SCD Type 2
dp.create_auto_cdc_flow(
    target="silver_patient",
    source="bronze_patient_changes",
    keys=["id"],
    sequence_by="_source_timestamp",  # FHIR meta.lastUpdated
    stored_as_scd_type=2,             # Full history with __START_AT/__END_AT
)
```

### How It Works

1. **Bronze** ingests raw JSON files via Auto Loader with `_source_timestamp` from `meta.lastUpdated`
2. **Temporary views** filter bronze by `resourceType` and add `_processed_at`
3. **Auto CDC** compares incoming records against the target by `keys=["id"]`
4. When a resource changes, Auto CDC closes the current version (`__END_AT` set) and inserts a new version (`__END_AT = NULL`)
5. **Gold views** filter `__END_AT IS NULL` to show only current state

### Querying SCD2 Tables

```sql
-- Current records only
SELECT * FROM silver_patient WHERE __END_AT IS NULL;

-- Point-in-time lookup (what was the address on Jan 16?)
SELECT * FROM silver_patient
WHERE id = 'patient-001'
  AND __START_AT <= '2024-01-16'
  AND (__END_AT > '2024-01-16' OR __END_AT IS NULL);
```

---

## Project Structure

```
fhir-databricks/
├── config/                    – YAML config (dev.yaml, resources.yaml)
├── src/
│   ├── fhir_lakehouse/        – Reusable Python package
│   │   ├── api/                – FHIR client + pagination
│   │   ├── ingestion/          – Raw + bronze writers
│   │   ├── transformations/    – Parsers, quality, SCD2 hashing
│   │   └── analytics/          – Gold aggregation utilities
│   └── pipeline/               – SDP source files
│       ├── bronze.py          – Auto Loader streaming table
│       ├── silver.py          – SCD2 Auto CDC streaming tables
│       └── gold.py            – Materialized view aggregations
├── notebooks/                  – Databricks notebooks (ingestion, setup, DQ)
├── resources/                  – Databricks job definitions
├── sql/                        – Gold-layer SQL views
├── tests/                      – Unit tests
├── requirements.txt            – Python dependencies
├── pyproject.toml             – Package metadata
└── databricks.yml             – Declarative Automation Bundle config
```

---

## Pipeline Settings

| Setting | Value |
|---|---|
| Name | FHIR Lakehouse Pipeline |
| Catalog | `workspace` |
| Schema | `default` |
| Serverless | `true` |
| Photon | `true` |
| Channel | `CURRENT` |
| Libraries | `fhir-databricks/src/pipeline/**` |
| Environment | `requests`, `pyyaml`, `databricks-sdk`, `fhir-resources` |
| Config: `fhir.raw_volume.path` | `/Volumes/workspace/default/raw` |
| Config: `fhir.pipeline.version` | `1.0.0` |

---

## How to Run

### 1. Set Up the Raw Volume

```sql
CREATE VOLUME IF NOT EXISTS workspace.default.raw;
```

Drop FHIR JSON files into `/Volumes/workspace/default/raw`.

### 2. Run the Pipeline

- In the Databricks UI, open the **FHIR Lakehouse Pipeline** and click **Start** (triggered mode)
- Or use the API: a full refresh rebuilds all tables from scratch

### 3. Query the Results

```sql
-- Bronze: all raw resources
SELECT resourceType, id, _ingested_at, _source_timestamp FROM workspace.default.bronze_fhir_raw;

-- Silver: SCD2 patient history (all versions)
SELECT id, gender, address, __START_AT, __END_AT FROM workspace.default.silver_patient ORDER BY __START_AT;

-- Gold: current patient summary
SELECT * FROM workspace.default.gold_patient_summary;

-- Gold: resource overview
SELECT * FROM workspace.default.gold_resource_overview;
```

---

## License

MIT