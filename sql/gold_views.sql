-- Gold-layer SQL views for FHIR analytics
-- These views are created on top of the gold Delta tables.

-- Patient summary by gender
CREATE OR REPLACE VIEW gold_patient_summary AS
SELECT
    gender,
    patient_count
FROM gold_patient_summary
ORDER BY patient_count DESC;

-- Observation summary by status
CREATE OR REPLACE VIEW gold_observation_summary AS
SELECT
    status,
    observation_count
FROM gold_observation_summary
ORDER BY observation_count DESC;

-- Encounter summary by status
CREATE OR REPLACE VIEW gold_encounter_summary AS
SELECT
    status,
    encounter_count
FROM gold_encounter_summary
ORDER BY encounter_count DESC;

-- Combined resource counts across all types
CREATE OR REPLACE VIEW gold_resource_counts AS
SELECT 'Patient' AS resource_type, SUM(patient_count) AS total FROM gold_patient_summary
UNION ALL
SELECT 'Observation', SUM(observation_count) FROM gold_observation_summary
UNION ALL
SELECT 'Encounter', SUM(encounter_count) FROM gold_encounter_summary
ORDER BY total DESC;