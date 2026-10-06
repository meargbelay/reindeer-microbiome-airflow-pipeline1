"""
Step 0: Generate synthetic raw data.

In the real thesis pipeline, this step doesn't exist -- raw paired-end FASTQ
files come straight from the sequencer. Since we don't have the real FASTQ
files in this demo, this script fabricates a stand-in dataset with the same
*shape* as the real one (108 samples, mouth/anus site, sex, survival) so the
rest of the pipeline has something real to chew on.

Swap this step out entirely once you point the pipeline at real FASTQ files.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

GENERA = [
    "Alysiella", "Capnocytophaga", "Pseudomonas", "Sphingomonas", "Xylophilus",
    "Olsenella", "Monoglobus", "Roseisolibacter", "Parafilimonas", "Desulfovibrio",
    "Chitinophaga", "Flexivirga", "Nocardia", "Fusobacterium", "Proteobacteria_other",
]


def main(output_dir: str, n_samples: int, seed: int):
    rng = np.random.default_rng(seed)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    sites = rng.choice(["mouth", "anus"], size=n_samples)
    sexes = rng.choice(["F", "M"], size=n_samples)
    survival = rng.choice([0, 1], size=n_samples)

    metadata = pd.DataFrame({
        "sample_id": [f"R-{i+401:03d}" for i in range(n_samples)],
        "site": sites,
        "sex": sexes,
        "survival": survival,
    })

    # Raw (noisy) read counts per genus per sample -- stand-in for raw ASV counts
    raw_counts = rng.poisson(lam=50, size=(n_samples, len(GENERA))) + rng.integers(
        0, 20, size=(n_samples, len(GENERA))
    )
    counts_df = pd.DataFrame(raw_counts, columns=GENERA)
    counts_df.insert(0, "sample_id", metadata["sample_id"])

    metadata.to_csv(out / "sample_metadata.csv", index=False)
    counts_df.to_csv(out / "raw_counts.csv", index=False)

    manifest = {
        "n_samples": n_samples,
        "genera": GENERA,
        "seed": seed,
        "note": "Synthetic stand-in data for demo purposes only.",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"[generate_raw_data] wrote {n_samples} samples x {len(GENERA)} genera to {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--n-samples", type=int, default=108)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(args.output_dir, args.n_samples, args.seed)
