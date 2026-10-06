# Reindeer Calf Microbiome Pipeline — Orchestrated with Apache Airflow

An Airflow-orchestrated bioinformatics pipeline, adapted from my Master's thesis
*"Microbiota and genetic variation in reindeer calves: analysis of data in
relation to survival"* (Swedish University of Agricultural Sciences, 2026).

The original thesis analysis was a DADA2/R pipeline run manually, step by
step. This project re-implements that pipeline as a set of orchestrated
Airflow tasks — each stage (filtering, denoising, taxonomy assignment,
diversity analysis, differential abundance testing) becomes its own task
with explicit dependencies, automatic retries, logging, and a UI to monitor
every run. It's the same core idea as a bioinformatics pipeline, built with
the tooling used in production data engineering.

**Status:** built, tested end to end, and running locally via Docker + Airflow.

## Why this project

My thesis work was fundamentally a data pipeline: raw sequencing data in,
through cleaning and transformation, out to statistical results. This
project is an exercise in taking that same logic and expressing it the way a
data engineering team would — as a scheduled, monitored, reproducible DAG
rather than a set of scripts run by hand.

## Pipeline structure

```
generate_raw_data → quality_filter → learn_errors → denoise_and_merge
    → remove_chimeras → assign_taxonomy → build_phyloseq
        ├── diversity_analysis        (parallel)
        └── differential_abundance    (parallel)
```

| Stage | Mirrors (from the thesis) |
|---|---|
| `quality_filter` | DADA2 `filterAndTrim()` |
| `learn_errors` | DADA2 `learnErrors()` |
| `denoise_and_merge` | DADA2 `dada()` + `mergePairs()` |
| `remove_chimeras` | DADA2 `removeBimeraDenovo()` |
| `assign_taxonomy` | DADA2 `assignTaxonomy()` against SILVA |
| `build_phyloseq` | Building the combined `phyloseq` object in R |
| `diversity_analysis` | Shannon diversity + binomial GLM vs. survival |
| `differential_abundance` | ALDEx2 / MaAsLin2 / ANCOM-BC-style testing |

**Note on data:** the original raw FASTQ files aren't included here, so
`generate_raw_data` produces a synthetic dataset with the same shape as the
real one (108 samples, oral/rectal site, sex, survival). Every other stage
is genuine working logic — not a mock. Swapping in real FASTQ files or the
original R scripts only requires changing this one step (see **Extending
this project** below).

## Tech stack

Python (pandas, numpy, scipy) · Apache Airflow · Docker · (designed to
extend with R/DADA2)

## Running it

### Option A — Docker (recommended)

```bash
git clone https://github.com/meargbelay/reindeer-microbiome-airflow-pipeline.git
cd reindeer-microbiome-airflow-pipeline
docker compose up
```

Wait a minute or two for Airflow to initialize, then check the logs for a
line like:

```
standalone | Login with username: admin  password: <random-password>
```

Open **http://localhost:8080**, log in, un-pause `reindeer_microbiome_pipeline`
in the DAG list, and click **Trigger DAG** (▶) to run it. Switch to the
**Graph** view to watch each task turn green as it completes; click any task
→ **Logs** to see its output.

Stop with `Ctrl+C`, then `docker compose down`.

### Option B — Local Airflow install (no Docker)

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install "apache-airflow==2.9.3" --constraint \
  "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt"
pip install -r requirements.txt

export AIRFLOW_HOME=$(pwd)/airflow_home
mkdir -p $AIRFLOW_HOME/dags
cp dags/reindeer_microbiome_dag.py $AIRFLOW_HOME/dags/
```

Before starting, open `dags/reindeer_microbiome_dag.py` and change
`PROJECT_DIR` from `/opt/airflow/project` to the absolute path of this
folder on your machine. Then:

```bash
airflow standalone
```

Open **http://localhost:8080** as above.

### Option C — Run the pipeline directly, no Airflow

Useful for checking the pipeline logic in isolation:

```bash
pip install -r requirements.txt
D=./data/manual_run

python3 scripts/generate_raw_data.py --output-dir $D/00_raw
python3 scripts/quality_filter.py --input-dir $D/00_raw --output-dir $D/01_filtered
python3 scripts/learn_errors.py --input-dir $D/01_filtered --output-dir $D/02_errors
python3 scripts/denoise_and_merge.py --filtered-dir $D/01_filtered --errors-dir $D/02_errors --output-dir $D/03_denoised
python3 scripts/remove_chimeras.py --input-dir $D/03_denoised --output-dir $D/04_clean
python3 scripts/assign_taxonomy.py --input-dir $D/04_clean --output-dir $D/05_taxonomy
python3 scripts/build_phyloseq.py --taxonomy-dir $D/05_taxonomy --metadata-dir $D/01_filtered --output-dir $D/06_phyloseq
python3 scripts/diversity_analysis.py --input-dir $D/06_phyloseq --output-dir $D/07_diversity
python3 scripts/differential_abundance.py --input-dir $D/06_phyloseq --output-dir $D/08_diffabund
```

## Extending this project

- **Real data:** replace `generate_raw_data.py`'s output with your actual
  FASTQ files or existing ASV tables.
- **Real DADA2/R:** swap the Python stand-ins for `quality_filter`,
  `learn_errors`, `denoise_and_merge`, and `remove_chimeras` for
  `BashOperator` tasks calling the original R scripts (`Rscript
  filter_and_trim.R ...`) — Airflow doesn't care what language a task runs.
- **Scheduling:** change `schedule=None` to `"@weekly"` (or similar) to
  simulate a recurring pipeline for incoming sequencing batches.
- **Data validation:** add a task after `build_phyloseq` that checks
  invariants (e.g. no sample has zero total reads) and fails the run if
  they're violated — a standard data-quality layer in production pipelines.

## Background

Original thesis: Brhane, M. B. (2026). *Microbiota and genetic variation in
reindeer calves: analysis of data in relation to survival.* Uppsala: SLU,
Institutionen för husdjurens biovetenskaper (HBIO).

## Author

**Mearg Belay Brhane** — Bioinformatics · [GitHub](https://github.com/meargbelay) · [LinkedIn](https://www.linkedin.com/in/mearg-belay-brhane-a1388220a/)
