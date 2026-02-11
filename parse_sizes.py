from pathlib import Path
import csv
import xml.etree.ElementTree as ET

LIGHT_XML = Path("data") / "stock_light_export.xml"
SIZES_XML = Path("data") / "sizes.xml"
OUT_SIZES = Path("data") / "products_sizes.csv"


def load_size_names() -> dict[str, str]:
    """Load size id -> name from sizes.xml (nested under group/size)."""
    tree = ET.parse(SIZES_XML)
    root = tree.getroot()
    sizes = root.findall(".//size") or root.findall("size")
    return {s.get("id", ""): (s.get("name") or "") for s in sizes if s.get("id") is not None}


def main() -> None:
    OUT_SIZES.parent.mkdir(parents=True, exist_ok=True)
    size_names = load_size_names()

    with OUT_SIZES.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "product_id", "size_id", "code", "quantity", "size",
            "price_gross", "price_net", "vat",
        ])
        w.writeheader()

        product_id = None
        price_gross = ""
        price_net = ""
        vat = ""

        for event, elem in ET.iterparse(LIGHT_XML, events=("start", "end")):
            tag = elem.tag

            if event == "start" and tag == "product":
                product_id = elem.get("id")
                vat = elem.get("vat") or ""

            elif event == "start" and tag == "price" and product_id:
                price_gross = elem.get("gross") or ""
                price_net = elem.get("net") or ""

            elif event == "end" and tag == "size":
                size_id = elem.get("id") or ""
                code = elem.get("code")
                # <stock id="1" quantity="1008"/>
                stock = elem.find("stock")
                qty = stock.get("quantity") if stock is not None else ""
                size_name = size_names.get(str(size_id), "") if size_id else ""

                w.writerow({
                    "product_id": product_id or "",
                    "size_id": size_id,
                    "code": code or "",
                    "quantity": qty or "",
                    "size": size_name,
                    "price_gross": price_gross,
                    "price_net": price_net,
                    "vat": vat,
                })
                elem.clear()

if __name__ == "__main__":
    main()
