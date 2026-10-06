"""
Step 5: Assign taxonomy.

Mirrors DADA2's assignTaxonomy() against the SILVA reference database:
maps each ASV/genus to its higher-level taxonomy (phylum). Here we use a
small fixed lookup table instead of a real reference database.
"""
import argparse
from pathlib import Path

import pandas as pd

PHYLUM_LOOKUP = {
    "Alysiella": "Proteobacteria",
    "Capnocytophaga": "Bacteroidota",
    "Pseudomonas": "Proteobacteria",
    "Sphingomonas": "Proteobacteria",
    "Xylophilus": "Proteobacteria",
    "Olsenella": "Actinobacteriota",
    "Monoglobus": "Firmicutes",
    "Roseisolibacter": "Gemmatimonadota",
    "Parafilimonas": "Bacteroidota",
    "Desulfovibrio": "Desulfobacterota",
    "Chitinophaga": "Bacteroidota",
    "Flexivirga": "Actinobacteriota",
    "Nocardia": "Actinobacteriota",
    "Fusobacterium": "Fusobacteriota",
    "Proteobacteria_other": "Proteobacteria",
}


def main(input_dir: str, output_dir: str):
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    asv_table = pd.read_csv(in_dir / "asv_table_clean.csv")
    genus_cols = [c for c in asv_table.columns if c != "sample_id"]

    taxonomy = pd.DataFrame({
        "genus": genus_cols,
        "phylum": [PHYLUM_LOOKUP.get(g, "Unassigned") for g in genus_cols],
    })
    taxonomy.to_csv(out_dir / "taxonomy.csv", index=False)

    # Pass the ASV table through unchanged so downstream steps have one place to read from
    asv_table.to_csv(out_dir / "asv_table_taxonomy_ready.csv", index=False)

    print(f"[assign_taxonomy] assigned phylum for {len(genus_cols)} genera")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    main(args.input_dir, args.output_dir)
