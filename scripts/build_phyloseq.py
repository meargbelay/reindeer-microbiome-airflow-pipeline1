"""
Step 6: Build the combined analysis object.

Mirrors building a phyloseq object in R: merge the ASV abundance table,
taxonomy assignments, and sample metadata into one tidy, long-format table
that every downstream analysis step reads from.
"""
import argparse
from pathlib import Path

import pandas as pd


def main(taxonomy_dir: str, metadata_dir: str, output_dir: str):
    tax_dir = Path(taxonomy_dir)
    meta_dir = Path(metadata_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    asv_table = pd.read_csv(tax_dir / "asv_table_taxonomy_ready.csv")
    taxonomy = pd.read_csv(tax_dir / "taxonomy.csv")
    metadata = pd.read_csv(meta_dir / "filtered_metadata.csv")

    genus_cols = [c for c in asv_table.columns if c != "sample_id"]

    long = asv_table.melt(id_vars="sample_id", value_vars=genus_cols,
                           var_name="genus", value_name="count")
    long = long.merge(taxonomy, on="genus", how="left")
    long = long.merge(metadata, on="sample_id", how="left")

    long.to_csv(out_dir / "phyloseq_long.csv", index=False)
    asv_table.to_csv(out_dir / "phyloseq_wide.csv", index=False)
    metadata.to_csv(out_dir / "phyloseq_metadata.csv", index=False)

    print(f"[build_phyloseq] combined object: {asv_table.shape[0]} samples x "
          f"{len(genus_cols)} genera, {len(long)} long-format rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--taxonomy-dir", required=True)
    parser.add_argument("--metadata-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    main(args.taxonomy_dir, args.metadata_dir, args.output_dir)
