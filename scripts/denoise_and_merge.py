"""
Step 3: Denoise and merge.

Mirrors DADA2's dada() (denoising using the error model) + mergePairs()
(combining forward/reverse read inference into one ASV table). Here, we
subtract the learned noise floor from each genus's counts, which stands in
for removing sequencing-error-derived artifacts.
"""
import argparse
import json
from pathlib import Path

import pandas as pd


def main(filtered_dir: str, errors_dir: str, output_dir: str):
    filtered_dir = Path(filtered_dir)
    errors_dir = Path(errors_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    counts = pd.read_csv(filtered_dir / "filtered_counts.csv")
    error_model = json.loads((errors_dir / "error_model.json").read_text())

    genus_cols = [c for c in counts.columns if c != "sample_id"]
    denoised = counts.copy()
    for genus in genus_cols:
        floor = error_model[genus]["noise_floor"]
        denoised[genus] = (counts[genus] - floor).clip(lower=0).round().astype(int)

    denoised.to_csv(out_dir / "asv_table.csv", index=False)
    print(f"[denoise_and_merge] denoised {len(denoised)} samples x {len(genus_cols)} ASVs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filtered-dir", required=True)
    parser.add_argument("--errors-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    main(args.filtered_dir, args.errors_dir, args.output_dir)
