-- Run ONCE in a Snowflake worksheet, using the same role that created the tables.
-- Adds a run_id column to each table so every load can be tagged and safely re-run.
USE DATABASE reindeer_db;
USE SCHEMA pipeline;

ALTER TABLE sample_metadata                ADD COLUMN IF NOT EXISTS run_id VARCHAR;
ALTER TABLE asv_abundance                  ADD COLUMN IF NOT EXISTS run_id VARCHAR;
ALTER TABLE alpha_diversity                ADD COLUMN IF NOT EXISTS run_id VARCHAR;
ALTER TABLE differential_abundance_results ADD COLUMN IF NOT EXISTS run_id VARCHAR;

-- Check: each table should now list run_id as its last column
DESCRIBE TABLE sample_metadata;
