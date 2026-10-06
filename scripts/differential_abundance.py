"""
Step 8: Differential abundance analysis.

Mirrors the thesis's use of ALDEx2 / MaAsLin2 / ANCOM-BC: test each genus
for a significant association with survival. Here we use a simple
Mann-Whitney U test per genus as a lightweight stand-in for those methods,
with Benjamini-Hochberg FDR correction.
"""
import argparse
from pathlib import Path

import pandas as pd
from scipy import stats


def benjamini_hochberg(pvals: pd.Series) -> pd.Series:
    ranked = pvals.rank(method="first")
    n = len(pvals)
    adjusted = pvals * n / ranked
    # enforce monotonicity
    order = ranked.sort_values().index
    running_min = float("inf")
    adj_sorted = []
    for idx in reversed(list(order)):
        running_min = min(running_min, adjusted[idx])
        adj_sorted.append((idx, running_min))
    adj_map = dict(adj_sorted)
    return pvals.index.to_series().map(adj_map).clip(upper=1.0)


def main(input_dir: str, output_dir: str):
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    wide = pd.read_csv(in_dir / "phyloseq_wide.csv")
    metadata = pd.read_csv(in_dir / "phyloseq_metadata.csv")
    merged = wide.merge(metadata, on="sample_id")

    genus_cols = [c for c in wide.columns if c != "sample_id"]
    survivors = merged[merged["survival"] == 1]
    non_survivors = merged[merged["survival"] == 0]

    results = []
    for genus in genus_cols:
        stat, pval = stats.mannwhitneyu(
            survivors[genus], non_survivors[genus], alternative="two-sided"
        )
        direction = "higher_in_survivors" if survivors[genus].mean() > non_survivors[genus].mean() else "higher_in_non_survivors"
        results.append({"genus": genus, "statistic": stat, "p_value": pval, "direction": direction})

    results_df = pd.DataFrame(results)
    results_df["q_value"] = benjamini_hochberg(results_df.set_index("genus")["p_value"]).values
    results_df = results_df.sort_values("p_value")
    results_df.to_csv(out_dir / "differential_abundance_results.csv", index=False)

    significant = results_df[results_df["q_value"] < 0.1]
    print(f"[differential_abundance] tested {len(genus_cols)} genera, "
          f"{len(significant)} significant at q<0.1:")
    if not significant.empty:
        print(significant[["genus", "p_value", "q_value", "direction"]].to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    main(args.input_dir, args.output_dir)
