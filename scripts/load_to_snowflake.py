"""
Step 9: Load pipeline results into Snowflake.

Reads the final CSV outputs of one pipeline run and loads them into four
Snowflake tables (REINDEER_DB.PIPELINE.*). Every row is tagged with a
`run_id`, and each load first deletes any rows already stored for that
run_id inside the same transaction. This makes the load IDEMPOTENT:
re-running the same run replaces its rows instead of duplicating them.

Two ways to use this file:
  1. Inside Airflow: the DAG imports `load_run()` and passes in a connection
     built from the Airflow connection "snowflake_default".
  2. From the command line (for quick testing without Airflow): set the
     SNOWFLAKE_* environment variables and run this file directly.
     Credentials are never written in code.
"""
import argparse
import os
from pathlib import Path

import pandas as pd

DATABASE = "REINDEER_DB"
SCHEMA = "PIPELINE"

# table name -> (csv path relative to the run folder, columns to load)
TABLES = {
    "SAMPLE_METADATA": (
        "06_phyloseq/phyloseq_metadata.csv",
        ["sample_id", "site", "sex", "survival"],
    ),
    "ASV_ABUNDANCE": (
        "06_phyloseq/phyloseq_long.csv",
        ["sample_id", "genus", "count", "phylum"],
    ),
    "ALPHA_DIVERSITY": (
        "07_diversity/alpha_diversity.csv",
        ["sample_id", "shannon", "site", "sex", "survival"],
    ),
    "DIFFERENTIAL_ABUNDANCE_RESULTS": (
        "08_diffabund/differential_abundance_results.csv",
        ["genus", "statistic", "p_value", "q_value", "direction"],
    ),
}


def prepare_tables(run_dir: str) -> dict:
    """Read and validate the CSVs. Returns {table: (columns, rows)}.

    Validation happens BEFORE touching Snowflake, so a missing file or
    wrong column fails fast with a clear message and nothing is half-loaded.
    """
    run_path = Path(run_dir)
    prepared = {}
    for table, (rel_path, columns) in TABLES.items():
        csv_path = run_path / rel_path
        if not csv_path.exists():
            raise FileNotFoundError(f"[{table}] expected file not found: {csv_path}")

        df = pd.read_csv(csv_path)
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise ValueError(f"[{table}] {csv_path.name} is missing columns: {missing}")
        if df.empty:
            raise ValueError(f"[{table}] {csv_path.name} has no rows; refusing to load an empty table")

        df = df[columns].astype(object).where(df[columns].notna(), None)
        rows = list(df.itertuples(index=False, name=None))
        prepared[table] = (columns, rows)
    return prepared


def load_run(conn, run_dir: str, run_key: str) -> dict:
    """Load one pipeline run into Snowflake. Returns {table: rows_loaded}."""
    prepared = prepare_tables(run_dir)
    counts = {}

    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        for table, (columns, rows) in prepared.items():
            full_name = f"{DATABASE}.{SCHEMA}.{table}"

            # 1. remove anything this run already loaded (makes re-runs safe)
            cur.execute(f"DELETE FROM {full_name} WHERE run_id = %s", (run_key,))

            # 2. insert the fresh rows, tagged with the run id
            col_list = ", ".join(columns + ["run_id"])
            placeholders = ", ".join(["%s"] * (len(columns) + 1))
            cur.executemany(
                f"INSERT INTO {full_name} ({col_list}) VALUES ({placeholders})",
                [tuple(row) + (run_key,) for row in rows],
            )
            counts[table] = len(rows)
            print(f"[load_to_snowflake] {full_name}: loaded {len(rows)} rows for run_id={run_key}")
        cur.execute("COMMIT")
    except Exception:
        cur.execute("ROLLBACK")
        print("[load_to_snowflake] error, transaction rolled back; no partial data left in Snowflake")
        raise
    finally:
        cur.close()
    return counts


def connect_from_env():
    """Build a Snowflake connection from environment variables (CLI use only)."""
    import snowflake.connector

    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ.get("SNOWFLAKE_ROLE"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "REINDEER_WH"),
        database=DATABASE,
        schema=SCHEMA,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, help="folder holding 06_phyloseq, 07_diversity, 08_diffabund")
    parser.add_argument("--run-key", required=True, help="label for this load, e.g. 20261008")
    args = parser.parse_args()

    connection = connect_from_env()
    try:
        load_run(connection, args.run_dir, args.run_key)
    finally:
        connection.close()
