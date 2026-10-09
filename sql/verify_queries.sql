-- Run these in Snowflake AFTER the Airflow DAG finishes, to check the load.
USE DATABASE reindeer_db;
USE SCHEMA pipeline;

-- 1. Row counts per table and run (expect 108 samples, 1620 abundance rows, 15 genera)
SELECT 'sample_metadata' AS table_name, run_id, COUNT(*) AS n FROM sample_metadata GROUP BY run_id
UNION ALL SELECT 'asv_abundance', run_id, COUNT(*) FROM asv_abundance GROUP BY run_id
UNION ALL SELECT 'alpha_diversity', run_id, COUNT(*) FROM alpha_diversity GROUP BY run_id
UNION ALL SELECT 'differential_abundance_results', run_id, COUNT(*) FROM differential_abundance_results GROUP BY run_id;

-- 2. Average Shannon diversity by site and survival
SELECT site, survival, ROUND(AVG(shannon), 3) AS avg_shannon, COUNT(*) AS n_samples
FROM alpha_diversity
GROUP BY site, survival
ORDER BY site, survival;

-- 3. Top 5 genera by total abundance, with phylum (join of two tables)
SELECT genus, phylum, SUM(count) AS total_count
FROM asv_abundance
GROUP BY genus, phylum
ORDER BY total_count DESC
LIMIT 5;

-- 4. Smallest p-values from the differential abundance test
SELECT genus, direction, ROUND(p_value, 4) AS p_value, ROUND(q_value, 4) AS q_value
FROM differential_abundance_results
ORDER BY p_value
LIMIT 5;
