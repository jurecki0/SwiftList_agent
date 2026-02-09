from pathlib import Path
import xml.etree.ElementTree as ET

XML_PATH = Path("data") / "stock_export_full.xml"
XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"  # xml:lang
TARGET_LANG = "pol"

def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag

def main() -> None:
    product_id = None
    polish_name = None
    in_product = False
    in_description = False

    product_index = 0

    for event, elem in ET.iterparse(XML_PATH, events=("start", "end")):  # [page:3]
        tag = localname(elem.tag)

        if event == "start":
            if tag == "product":
                in_product = True
                product_id = elem.get("id")
                polish_name = None
            elif in_product and tag == "description":
                in_description = True

        else:  # end
            if in_product and in_description and tag == "name":
                if elem.get(XML_LANG_ATTR) == TARGET_LANG:
                    polish_name = (elem.text or "").strip()

            elif in_product and tag == "description":
                in_description = False

            elif tag == "product":
                product_index += 1
                if product_id is not None and polish_name:
                    print(f"{product_index}) id: {product_id} | Name: \"{polish_name}\"")
                else:
                    # Optional: still show the index even if name is missing
                    print(f"{product_index}) id: {product_id} | Name: \"\"")

                in_product = False
                product_id = None
                polish_name = None
                elem.clear()  # clears subelements/attrs/text to save memory during streaming [page:3]

if __name__ == "__main__":
    main()
