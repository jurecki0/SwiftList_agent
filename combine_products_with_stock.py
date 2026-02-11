from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd

FLAT = Path("data") / "products_flat.csv"
SIZES = Path("data") / "products_sizes.csv"
PRODUCERS_XML = Path("data") / "producers.xml"
OUT_COMBINED = Path("data") / "products_with_stock.csv"


def load_producer_names() -> dict[str, str]:
    """Load producer id -> name from producers.xml."""
    tree = ET.parse(PRODUCERS_XML)
    root = tree.getroot()
    producers = root.findall("producer") or root.findall(".//producer")
    return {p.get("id", ""): (p.get("name") or "") for p in producers if p.get("id")}


def main() -> None:
    products = pd.read_csv(FLAT, dtype=str).fillna("")
    print(f"Loaded {len(products)} products from {FLAT}")

    producer_names = load_producer_names()
    if "producer_id" in products.columns:
        products["producer"] = products["producer_id"].map(producer_names).fillna("")
    else:
        products["producer"] = ""

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
