from pathlib import Path
import csv
import xml.etree.ElementTree as ET

XML_PATH = Path("data") / "stock_export_full.xml"
OUT_CSV = Path("data") / "products_flat.csv"

XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"
TARGET_LANG = "pol"

def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag

def main() -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "product_id",
            "product_name_pol",
            "category_id",
            "category_name",
            "producer_id",
        ])
        w.writeheader()

        product_id = None
        product_name_pol = None
        category_id = None
        category_name = None
        producer_id = None

        in_product = False
        in_description = False

        for event, elem in ET.iterparse(XML_PATH, events=("start", "end")):  # streaming parse [web:7]
            tag = localname(elem.tag)

            if event == "start":
                if tag == "product":
                    in_product = True
                    product_id = elem.get("id")
                    product_name_pol = None
                    category_id = None
                    category_name = None
                    producer_id = None

                elif in_product and tag == "category":
                    # In your snippet: <category id="..." name="..."/> is a direct child of <product>
                    category_id = elem.get("id")
                    category_name = elem.get("name")

                elif in_product and tag == "producer":
                    producer_id = elem.get("id")

                elif in_product and tag == "description":
                    in_description = True

            else:  # end
                if in_product and in_description and tag == "name":
                    if elem.get(XML_LANG_ATTR) == TARGET_LANG:
                        product_name_pol = (elem.text or "").strip()

                elif in_product and tag == "description":
                    in_description = False

                elif tag == "product":
                    w.writerow({
                        "product_id": product_id or "",
                        "product_name_pol": product_name_pol or "",
                        "category_id": category_id or "",
                        "category_name": category_name or "",
                        "producer_id": producer_id or "",
                    })
                    in_product = False
                    elem.clear()  # free memory while iterparsing large XML [web:7]

if __name__ == "__main__":
    main()
