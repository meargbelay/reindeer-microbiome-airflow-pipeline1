"""
Step 7: Alpha diversity + survival association.

Mirrors the thesis's Shannon diversity calculation (estimate_richness in
phyloseq) and the GLM linking diversity to survival.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import statsmodels.api as sm
    HAVE_STATSMODELS = True
except ImportError:
    HAVE_STATSMODELS = False


def shannon(counts_row: pd.Series) -> float:
    counts = counts_row[counts_row > 0]
    if counts.sum() == 0:
        return 0.0
    p = counts / counts.sum()
    return float(-(p * np.log(p)).sum())


def main(input_dir: str, output_dir: str):
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    wide = pd.read_csv(in_dir / "phyloseq_wide.csv")
    metadata = pd.read_csv(in_dir / "phyloseq_metadata.csv")

    genus_cols = [c for c in wide.columns if c != "sample_id"]
    wide["shannon"] = wide[genus_cols].apply(shannon, axis=1)

    diversity = wide[["sample_id", "shannon"]].merge(metadata, on="sample_id")
    diversity.to_csv(out_dir / "alpha_diversity.csv", index=False)

    # GLM: survival ~ shannon + site + sex (mirrors the thesis GLM)
    model_df = diversity.copy()
    model_df["site_mouth"] = (model_df["site"] == "mouth").astype(int)
    model_df["sex_m"] = (model_df["sex"] == "M").astype(int)

    if HAVE_STATSMODELS:
        X = sm.add_constant(model_df[["shannon", "site_mouth", "sex_m"]])
        y = model_df["survival"]
        try:
            glm = sm.GLM(y, X, family=sm.families.Binomial()).fit()
            summary_text = glm.summary().as_text()
        except Exception as e:  # small synthetic data can be separable / non-converging
            summary_text = f"GLM did not converge on this synthetic sample: {e}"
    else:
        summary_text = (
            "statsmodels not installed -- run `pip install statsmodels` and "
            "re-run this step to get the GLM summary. Skipped for now."
        )

    (out_dir / "glm_survival_summary.txt").write_text(summary_text)

    print(f"[diversity_analysis] computed Shannon diversity for {len(diversity)} samples")
    print(f"[diversity_analysis] mean Shannon by survival:\n"
          f"{diversity.groupby('survival')['shannon'].mean()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    main(args.input_dir, args.output_dir)
