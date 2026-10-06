"""
Airflow DAG: Reindeer Calf Microbiome Pipeline

Orchestrates a stand-in version of the thesis pipeline end to end:

    generate_raw_data
          |
    quality_filter
          |
    learn_errors
          |
    denoise_and_merge
          |
    remove_chimeras
          |
    assign_taxonomy
          |
    build_phyloseq
         / \
 diversity  differential_abundance

Each task shells out to one of the scripts in ../scripts/, passing along a
shared working directory so artifacts flow from one step to the next --
exactly the role Airflow plays in a real data engineering pipeline: it
doesn't do the data work itself, it decides *when* and *in what order*
each step runs, retries failures, and gives you a UI to see what happened.

To adapt this to the REAL thesis pipeline: replace generate_raw_data with
a sensor/task that waits for real FASTQ files, and swap each BashOperator's
command for a call to the real R scripts (Rscript dada2_filter.R ...),
keeping the same dependency structure.
"""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"  # mounted project root inside the Airflow container
SCRIPTS = f"{PROJECT_DIR}/scripts"
DATA = f"{PROJECT_DIR}/data/run_{{{{ ds_nodash }}}}"  # one output folder per DAG run date

default_args = {
    "owner": "mearg",
    "retries": 1,
}

with DAG(
    dag_id="reindeer_microbiome_pipeline",
    description="Orchestrated reindeer calf microbiome pipeline (DADA2-style stand-in)",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule=None,  # trigger manually; set to "@weekly" etc. for a real recurring pipeline
    catchup=False,
    tags=["bioinformatics", "microbiome", "demo"],
) as dag:

    generate_raw_data = BashOperator(
        task_id="generate_raw_data",
        bash_command=(
            f"python3 {SCRIPTS}/generate_raw_data.py "
            f"--output-dir {DATA}/00_raw --n-samples 108 --seed 42"
        ),
    )

    quality_filter = BashOperator(
        task_id="quality_filter",
        bash_command=(
            f"python3 {SCRIPTS}/quality_filter.py "
            f"--input-dir {DATA}/00_raw --output-dir {DATA}/01_filtered --min-total-reads 300"
        ),
    )

    learn_errors = BashOperator(
        task_id="learn_errors",
        bash_command=(
            f"python3 {SCRIPTS}/learn_errors.py "
            f"--input-dir {DATA}/01_filtered --output-dir {DATA}/02_errors"
        ),
    )

    denoise_and_merge = BashOperator(
        task_id="denoise_and_merge",
        bash_command=(
            f"python3 {SCRIPTS}/denoise_and_merge.py "
            f"--filtered-dir {DATA}/01_filtered --errors-dir {DATA}/02_errors "
            f"--output-dir {DATA}/03_denoised"
        ),
    )

    remove_chimeras = BashOperator(
        task_id="remove_chimeras",
        bash_command=(
            f"python3 {SCRIPTS}/remove_chimeras.py "
            f"--input-dir {DATA}/03_denoised --output-dir {DATA}/04_clean"
        ),
    )

    assign_taxonomy = BashOperator(
        task_id="assign_taxonomy",
        bash_command=(
            f"python3 {SCRIPTS}/assign_taxonomy.py "
            f"--input-dir {DATA}/04_clean --output-dir {DATA}/05_taxonomy"
        ),
    )

    build_phyloseq = BashOperator(
        task_id="build_phyloseq",
        bash_command=(
            f"python3 {SCRIPTS}/build_phyloseq.py "
            f"--taxonomy-dir {DATA}/05_taxonomy --metadata-dir {DATA}/01_filtered "
            f"--output-dir {DATA}/06_phyloseq"
        ),
    )

    diversity_analysis = BashOperator(
        task_id="diversity_analysis",
        bash_command=(
            f"python3 {SCRIPTS}/diversity_analysis.py "
            f"--input-dir {DATA}/06_phyloseq --output-dir {DATA}/07_diversity"
        ),
    )

    differential_abundance = BashOperator(
        task_id="differential_abundance",
        bash_command=(
            f"python3 {SCRIPTS}/differential_abundance.py "
            f"--input-dir {DATA}/06_phyloseq --output-dir {DATA}/08_diffabund"
        ),
    )

    # Linear chain up through build_phyloseq, then it fans out into two
    # independent analyses that can run in parallel.
    (
        generate_raw_data
        >> quality_filter
        >> learn_errors
        >> denoise_and_merge
        >> remove_chimeras
        >> assign_taxonomy
        >> build_phyloseq
        >> [diversity_analysis, differential_abundance]
    )
