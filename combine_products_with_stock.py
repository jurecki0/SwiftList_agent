from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd

FLAT = Path("data") / "products_flat.csv"
SIZES_CSV = Path("data") / "products_sizes.csv"
PRODUCERS_XML = Path("data") / "producers.xml"
CATEGORIES_XML = Path("data") / "categories.xml"
SIZES_XML = Path("data") / "sizes.xml"
OUT_COMBINED = Path("data") / "products_with_stock.csv"


def load_producer_names() -> dict[str, str]:
    """Load producer id -> name from producers.xml."""
    tree = ET.parse(PRODUCERS_XML)
    root = tree.getroot()
    producers = root.findall("producer") or root.findall(".//producer")
    return {p.get("id", ""): (p.get("name") or "") for p in producers if p.get("id")}


def load_category_names() -> dict[str, str]:
    """Load category id -> name from categories.xml."""
    tree = ET.parse(CATEGORIES_XML)
    root = tree.getroot()
    categories = root.findall("category") or root.findall(".//category")
    return {c.get("id", ""): (c.get("name") or "") for c in categories if c.get("id")}


def load_size_names() -> dict[str, str]:
    """Load size id -> name from sizes.xml."""
    tree = ET.parse(SIZES_XML)
    root = tree.getroot()
    sizes = root.findall(".//size") or root.findall("size")
    return {str(s.get("id", "")): (s.get("name") or "") for s in sizes if s.get("id") is not None}


def main() -> None:
    products = pd.read_csv(FLAT, dtype=str).fillna("")
    print(f"Loaded {len(products)} products from {FLAT}")

    producer_names = load_producer_names()
    if "producer_id" in products.columns:
        products["producer"] = products["producer_id"].map(producer_names).fillna("")
    else:
        products["producer"] = ""

    category_names = load_category_names()
    if "category_id" in products.columns:
        products["category"] = products["category_id"].map(category_names).fillna("")
    else:
        products["category"] = ""

    sizes = pd.read_csv(SIZES_CSV, dtype=str).fillna("")
    sizes["quantity"] = pd.to_numeric(sizes["quantity"], errors="coerce").fillna(0)

    # Resolve size names from sizes.xml if not already in CSV
    size_names = load_size_names()
    if "size" not in sizes.columns and "size_id" in sizes.columns:
        sizes["size"] = sizes["size_id"].map(lambda x: size_names.get(str(x).strip(), "")).fillna("")
    elif "size_id" in sizes.columns:
        sizes["size"] = sizes["size_id"].map(lambda x: size_names.get(str(x).strip(), ""))

    # Per-product size breakdown: "70X140: 1008" or "70X140: 100; 50X100: 200"
    def format_sizes(g):
        parts = []
        for _, row in g.iterrows():
            if row["quantity"] <= 0:
                continue
            label = (row.get("size") or "").strip() or (row.get("size_id") or "")
            parts.append(f"{label}: {int(row['quantity'])}")
        return "; ".join(parts) if parts else ""

    sizes_summary = sizes.groupby("product_id", group_keys=False).apply(format_sizes, include_groups=False).reset_index(name="sizes")

    # Sum quantity per product (across all sizes), call it `total_stock`
    stock_per_product = (
        sizes.groupby("product_id")["quantity"]
        .sum()
        .reset_index()
        .rename(columns={"quantity": "total_stock"})
    )

    merged = products.merge(stock_per_product, on="product_id", how="left")
    merged["total_stock"] = merged["total_stock"].fillna(0).astype(int)
    merged = merged.merge(sizes_summary, on="product_id", how="left")
    merged["sizes"] = merged["sizes"].fillna("")

    merged.to_csv(OUT_COMBINED, index=False, encoding="utf-8")
    print(f"Saved: {OUT_COMBINED}")
    print("First 5 rows:")
    print(merged.head())

if __name__ == "__main__":
    main()
