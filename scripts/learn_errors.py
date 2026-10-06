"""
Step 2: Learn an error model from the filtered data.

Mirrors DADA2's learnErrors(): estimate a noise profile (here, just mean and
std of counts per genus) that the next step uses to separate signal from
sequencing noise.
"""
import argparse
import json
from pathlib import Path

import pandas as pd


def main(input_dir: str, output_dir: str):
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    counts = pd.read_csv(in_dir / "filtered_counts.csv")
    genus_cols = [c for c in counts.columns if c != "sample_id"]

    error_model = {
        genus: {
            "mean": float(counts[genus].mean()),
            "std": float(counts[genus].std()),
            "noise_floor": float(counts[genus].quantile(0.05)),
        }
        for genus in genus_cols
    }

    (out_dir / "error_model.json").write_text(json.dumps(error_model, indent=2))
    print(f"[learn_errors] learned noise profile for {len(genus_cols)} genera")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    main(args.input_dir, args.output_dir)
