"""Explore the Indian medicines dataset (read-only; no cleaning)."""

from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent / "data" / "Extensive_A_Z_medicines_dataset_of_India.csv"

BRANDS_TO_CHECK = [
    "Dolo 650",
    "Crocin Advance",
    "Augmentin 625 Duo",
    "Calpol 500",
    "Combiflam",
    "Brufen 400",
    "Pantop 40",
    "Ecosprin 75",
]


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    df = df.drop_duplicates(subset=["id"])

    print("=" * 60)
    print("SHAPE")
    print("=" * 60)
    print(df.shape)

    print("\n" + "=" * 60)
    print("COLUMNS AND DTYPES")
    print("=" * 60)
    for col, dtype in df.dtypes.items():
        print(f"{col}: {dtype}")

    print("\n" + "=" * 60)
    print("NULL COUNTS PER COLUMN")
    print("=" * 60)
    print(df.isnull().sum().to_string())

    print("\n" + "=" * 60)
    print("10 RANDOM ROWS")
    print("=" * 60)
    print(df.sample(n=10, random_state=42).to_string())

    print("\n" + "=" * 60)
    print("20 MOST COMMON VALUES OF short_composition2")
    print("=" * 60)
    if "short_composition2" in df.columns:
        print(df["short_composition2"].value_counts(dropna=False).head(20).to_string())
    else:
        print("Column 'short_composition2' not found.")

    print("\n" + "=" * 60)
    print("BRAND EXISTENCE CHECK (case-insensitive partial match on name)")
    print("=" * 60)
    names = df["name"].astype(str)
    for brand in BRANDS_TO_CHECK:
        mask = names.str.contains(brand, case=False, na=False, regex=False)
        matches = df.loc[mask, "name"]
        count = int(mask.sum())
        print(f"\n[{brand}] found={count > 0} (matches={count})")
        if count > 0:
            # Show a few matching names for clarity
            for n in matches.head(5).tolist():
                print(f"  - {n}")
            if count > 5:
                print(f"  ... and {count - 5} more")


if __name__ == "__main__":
    main()
