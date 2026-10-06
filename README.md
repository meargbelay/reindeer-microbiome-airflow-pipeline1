# Reindeer Calf Microbiome Pipeline — Orchestrated with Airflow

This project takes the bioinformatics pipeline from the thesis *"Microbiota
and genetic variation in reindeer calves"* and re-implements it as an
**Airflow-orchestrated pipeline**, so each DADA2/phyloseq-style step becomes
an Airflow task with explicit dependencies, retries, logging, and a UI to
monitor runs — the same orchestration pattern used in data engineering.

Since we don't have the original raw FASTQ files here, the `generate_raw_data`
step fabricates a synthetic dataset with the same shape (108 samples, mouth/
anus site, sex, survival). Every other step is genuine working logic (quality
filtering, denoising, chimera removal, taxonomy assignment, diversity
analysis, differential abundance testing) — just swap the synthetic
generator for your real FASTQ inputs (or real DADA2 R scripts) when you're
ready to run it on real data. That's the only step you'd ever need to
replace.

## Pipeline structure

```
generate_raw_data → quality_filter → learn_errors → denoise_and_merge
    → remove_chimeras → assign_taxonomy → build_phyloseq
        → diversity_analysis       (parallel)
        → differential_abundance   (parallel)
```

This mirrors the thesis sections 4.4–5.7: DADA2 processing → ASV table →
taxonomy → combined phyloseq object → alpha diversity/GLM → differential
abundance (ALDEx2/MaAsLin2/ANCOM-BC stand-in).

## Option A: Run with Docker (recommended, easiest)

Requires Docker Desktop installed and running.

```bash
cd reindeer-microbiome-airflow
docker compose up
```

Wait ~1–2 minutes for Airflow to initialize. The first time it starts, it
prints an admin username/password in the logs — look for a line like:

```
standalone | Login with username: admin  password: <random-password>
```

Then open **http://localhost:8080**, log in, find `reindeer_microbiome_pipeline`
in the DAG list, un-pause it (toggle on the left), and click the ▶ (trigger)
button to run it manually.

Click into the run to see the graph view — each box is a task, and you can
watch them turn green as they complete. Click any task → "Logs" to see its
print output.

To stop: `Ctrl+C`, then `docker compose down`.

## Option B: Run without Docker (local Airflow install)

```bash
cd reindeer-microbiome-airflow
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install "apache-airflow==2.9.3" --constraint \
  "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt"
pip install -r requirements.txt

export AIRFLOW_HOME=$(pwd)/airflow_home
mkdir -p $AIRFLOW_HOME/dags
cp dags/reindeer_microbiome_dag.py $AIRFLOW_HOME/dags/

# IMPORTANT: edit dags/reindeer_microbiome_dag.py and change PROJECT_DIR
# from "/opt/airflow/project" to the absolute path of this folder, e.g.
# PROJECT_DIR = "/Users/yourname/reindeer-microbiome-airflow"

airflow standalone
```

Then open **http://localhost:8080** as above.

## Option C: Just run the pipeline directly (no Airflow at all)

Useful for quickly checking the pipeline logic works before wiring it into
Airflow:

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

This exact sequence has been tested and runs end to end successfully.

## Next steps (to make this a genuinely strong portfolio project)

1. **Swap in real data**: replace `generate_raw_data.py` with your actual
   FASTQ files / existing ASV tables from the thesis project.
2. **Swap in real DADA2**: replace the Python stand-ins for `quality_filter`,
   `learn_errors`, `denoise_and_merge`, and `remove_chimeras` with
   `BashOperator` calls to your actual R scripts (`Rscript filter_and_trim.R`),
   since Airflow doesn't care what language a task runs in.
3. **Add a schedule**: change `schedule=None` to e.g. `"@weekly"` if this
   were a recurring pipeline (e.g. new sequencing batches arriving regularly).
4. **Add data quality checks**: add a task after `build_phyloseq` that
   asserts things like "no sample has zero total reads" and fails loudly if
   not — this is the "data validation" layer from a full data engineering
   pipeline.
5. **Push to GitHub** with this README, and link it on your CV/LinkedIn as a
   concrete "orchestrated a bioinformatics pipeline with Apache Airflow"
   project.
