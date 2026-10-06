"""
Step 4: Remove chimeric ASVs.

Mirrors DADA2's removeBimeraDenovo(): flag and drop ASVs that look like
artificial hybrids of two real sequences. Here, we flag any genus whose
total abundance is implausibly low and inconsistent across samples
(a simple stand-in rule) and drop it from the table.
"""
import argparse
from pathlib import Path

import pandas as pd


def main(input_dir: str, output_dir: str, min_prevalence: float):
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    asv_table = pd.read_csv(in_dir / "asv_table.csv")
    genus_cols = [c for c in asv_table.columns if c != "sample_id"]

    prevalence = (asv_table[genus_cols] > 0).mean(axis=0)
    chimeric_like = prevalence[prevalence < min_prevalence].index.tolist()

    clean_table = asv_table.drop(columns=chimeric_like)
    clean_table.to_csv(out_dir / "asv_table_clean.csv", index=False)

    print(f"[remove_chimeras] dropped {len(chimeric_like)} low-prevalence genera: "
          f"{chimeric_like if chimeric_like else 'none'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--min-prevalence", type=float, default=0.05)
    args = parser.parse_args()
    main(args.input_dir, args.output_dir, args.min_prevalence)
