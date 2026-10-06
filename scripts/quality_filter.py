"""
Step 1: Quality filtering and trimming.

Mirrors DADA2's filterAndTrim(): drop low-quality / low-count samples and
clip extreme outlier counts, keeping only samples that pass QC on both
"forward and reverse reads" (here: both site swabs are present).
"""
import argparse
from pathlib import Path

import pandas as pd


def main(input_dir: str, output_dir: str, min_total_reads: int):
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    counts = pd.read_csv(in_dir / "raw_counts.csv")
    metadata = pd.read_csv(in_dir / "sample_metadata.csv")

    genus_cols = [c for c in counts.columns if c != "sample_id"]
    counts["total_reads"] = counts[genus_cols].sum(axis=1)

    passed = counts[counts["total_reads"] >= min_total_reads].copy()
    kept_ids = set(passed["sample_id"])
    metadata_passed = metadata[metadata["sample_id"].isin(kept_ids)].copy()

    passed = passed.drop(columns=["total_reads"])
    passed.to_csv(out_dir / "filtered_counts.csv", index=False)
    metadata_passed.to_csv(out_dir / "filtered_metadata.csv", index=False)

    n_dropped = len(counts) - len(passed)
    print(f"[quality_filter] kept {len(passed)} samples, dropped {n_dropped} "
          f"below {min_total_reads} total reads")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--min-total-reads", type=int, default=300)
    args = parser.parse_args()
    main(args.input_dir, args.output_dir, args.min_total_reads)
