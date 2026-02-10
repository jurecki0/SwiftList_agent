from pathlib import Path
import csv
import xml.etree.ElementTree as ET

LIGHT_XML = Path("data") / "stock_light_export.xml"
OUT_SIZES = Path("data") / "products_sizes.csv"

def main() -> None:
    OUT_SIZES.parent.mkdir(parents=True, exist_ok=True)

    with OUT_SIZES.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["product_id", "size_id", "code", "quantity"])
        w.writeheader()

        for event, elem in ET.iterparse(LIGHT_XML, events=("start", "end")):
            tag = elem.tag

            if event == "start" and tag == "product":
                product_id = elem.get("id")

            elif tag == "size":
                size_id = elem.get("id")
                code = elem.get("code")
                # <stock id="1" quantity="1008"/>
                stock = elem.find("stock")
                qty = stock.get("quantity") if stock is not None else ""

                w.writerow({
                    "product_id": product_id or "",
                    "size_id": size_id or "",
                    "code": code or "",
                    "quantity": qty or "",
                })
                elem.clear()

if __name__ == "__main__":
    main()
