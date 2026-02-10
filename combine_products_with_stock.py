from pathlib import Path
import pandas as pd

FLAT = Path("data") / "products_flat.csv"
SIZES = Path("data") / "products_sizes.csv"
OUT_COMBINED = Path("data") / "products_with_stock.csv"

def main() -> None:
    products = pd.read_csv(FLAT, dtype=str).fillna("")
    print(f"Loaded {len(products)} products from {FLAT}")

    sizes = pd.read_csv(SIZES, dtype=str).fillna("")
    sizes["quantity"] = pd.to_numeric(sizes["quantity"], errors="coerce").fillna(0)

    # Sum quantity per product (across all sizes), call it `total_stock`
    stock_per_product = (
        sizes.groupby("product_id")["quantity"]
        .sum()
        .reset_index()
        .rename(columns={"quantity": "total_stock"})
    )

    merged = products.merge(stock_per_product, on="product_id", how="left")
    merged["total_stock"] = merged["total_stock"].fillna(0).astype(int)

    merged.to_csv(OUT_COMBINED, index=False, encoding="utf-8")
    print(f"Saved: {OUT_COMBINED}")
    print("First 5 rows:")
    print(merged.head())

if __name__ == "__main__":
    main()
