// deno run --allow-read --allow-write .\src\build_products_with_stock.ts

import { SAXParser } from "https://unpkg.com/sax-ts@1.2.8/src/sax.ts"; // sax-ts usage docs: onopentag + onattribute [web:246]

type FullProduct = {
  product_id: string;
  product_name_pol: string;
  category_id: string;
  category: string;
  card_url: string;
  image_url: string;
  icon_url: string;
  vat: string;
  producer: string;
};

type LightAgg = {
  product_id: string;
  total_stock: number;
  price_gross: string;
  price_net: string;
};

function escapeCsv(value: string): string {
  const v = value ?? "";
  if (/[",\n]/.test(v)) return `"${v.replaceAll('"', '""')}"`;
  return v;
}

function attrsGet(attrs: Record<string, string>, name: string): string {
  return attrs[name] ?? "";
}

async function parseFullXml(path: string): Promise<Map<string, FullProduct>> {
  const xml = await Deno.readTextFile(path);
  const out = new Map<string, FullProduct>();

  // State
  let inProduct = false;
  let inDescription = false;

  let currentProductId = "";
  let currentVat = "";
  let currentCategoryId = "";
  let currentCategoryName = "";
  let currentCardUrl = "";
  let currentProducerName = "";
  let currentImageUrl = "";
  let currentIconUrl = "";

  // For Polish name
  let capturePolNameText = false;
  let polName = "";

  // Current open tag + its attributes collected via onattribute
  let openTag = "";
  let openAttrs: Record<string, string> = {};

  const parser = new SAXParser(true, { xmlns: true, position: false });

  // Reset per-tag attribute capture
  parser.onopentagstart = (node: any) => {
    openTag = node.name;
    openAttrs = {};
  };

  parser.onattribute = (a: any) => {
    // a has {name, value} [web:246]
    if (a?.name) openAttrs[a.name] = String(a.value ?? "");
  };

  parser.onopentag = (node: any) => {
    const tag = node.name;

    if (tag === "product") {
      inProduct = true;

      currentProductId = attrsGet(openAttrs, "id");
      currentVat = attrsGet(openAttrs, "vat");

      currentCategoryId = "";
      currentCategoryName = "";
      currentCardUrl = "";
      currentProducerName = "";
      currentImageUrl = "";
      currentIconUrl = "";

      polName = "";
      capturePolNameText = false;
    }

    if (inProduct && tag === "category") {
      currentCategoryId = attrsGet(openAttrs, "id");
      currentCategoryName = attrsGet(openAttrs, "name");
    }

    if (inProduct && tag === "producer") {
      currentProducerName = attrsGet(openAttrs, "name");
    }

    if (inProduct && tag === "card") {
      currentCardUrl = attrsGet(openAttrs, "url");
    }

    // Images from your snippet:
    // <image url="..."/> and <icon url="..."/>
    if (inProduct && tag === "image") {
      const url = attrsGet(openAttrs, "url");
      if (url && !currentImageUrl) currentImageUrl = url;
    }
    if (inProduct && tag === "icon") {
      const url = attrsGet(openAttrs, "url");
      if (url && !currentIconUrl) currentIconUrl = url;
    }

    if (inProduct && tag === "description") {
      inDescription = true;
    }

    if (inProduct && inDescription && tag === "name") {
      const lang = attrsGet(openAttrs, "xml:lang") || attrsGet(openAttrs, "lang");
      if (lang === "pol") {
        capturePolNameText = true;
        polName = "";
      }
    }
  };

  parser.ontext = (t: string) => {
    if (capturePolNameText) polName += t;
  };

  parser.onclosetag = (tagName: string) => {
    if (inProduct && inDescription && tagName === "name" && capturePolNameText) {
      capturePolNameText = false;
      polName = polName.trim();
    }

    if (inProduct && tagName === "description") {
      inDescription = false;
    }

    if (tagName === "product") {
      inProduct = false;

      const p: FullProduct = {
        product_id: currentProductId,
        product_name_pol: polName,
        category_id: currentCategoryId,
        category: currentCategoryName,
        card_url: currentCardUrl,
        image_url: currentImageUrl,
        icon_url: currentIconUrl,
        vat: currentVat,
        producer: currentProducerName,
      };

      if (p.product_id) out.set(p.product_id, p);

      // Reset per product
      currentProductId = "";
      currentVat = "";
      polName = "";
    }
  };

  parser.write(xml).close();
  return out;
}

async function parseLightXml(path: string): Promise<Map<string, LightAgg>> {
  const xml = await Deno.readTextFile(path);
  const out = new Map<string, LightAgg>();

  let currentProductId = "";
  let currentPriceGross = "";
  let currentPriceNet = "";
  let sumQty = 0;

  let openAttrs: Record<string, string> = {};

  const parser = new SAXParser(true, { xmlns: true, position: false });

  parser.onopentagstart = (_node: any) => {
    openAttrs = {};
  };

  parser.onattribute = (a: any) => {
    if (a?.name) openAttrs[a.name] = String(a.value ?? "");
  };

  parser.onopentag = (node: any) => {
    const tag = node.name;

    if (tag === "product") {
      currentProductId = attrsGet(openAttrs, "id");
      currentPriceGross = "";
      currentPriceNet = "";
      sumQty = 0;
    }

    if (tag === "price") {
      currentPriceGross = attrsGet(openAttrs, "gross");
      currentPriceNet = attrsGet(openAttrs, "net");
    }

    if (tag === "stock") {
      const qStr = attrsGet(openAttrs, "quantity") || "0";
      const q = Number.parseInt(qStr, 10);
      if (!Number.isNaN(q)) sumQty += q;
    }
  };

  parser.onclosetag = (tagName: string) => {
    if (tagName === "product") {
      if (currentProductId) {
        out.set(currentProductId, {
          product_id: currentProductId,
          total_stock: sumQty,
          price_gross: currentPriceGross,
          price_net: currentPriceNet,
        });
      }
      currentProductId = "";
    }
  };

  parser.write(xml).close();
  return out;
}

async function main() {
  // Paths relative to TS_PORT/
  const fullXml = "../data/stock_export_full.xml";
  const lightXml = "../data/stock_light_export.xml";
  const outCsv = "./out/products_with_stock.csv";

  const full = await parseFullXml(fullXml);
  const light = await parseLightXml(lightXml);

  const headers = [
    "product_id",
    "product_name_pol",
    "category_id",
    "category",
    "producer",
    "vat",
    "price_gross",
    "price_net",
    "total_stock",
    "card_url",
    "image_url",
    "icon_url",
  ];

  const allIds = new Set<string>([...full.keys(), ...light.keys()]);
  const sortedIds = [...allIds].sort((a, b) => Number(a) - Number(b));

  const lines: string[] = [];
  lines.push(headers.join(","));

  for (const id of sortedIds) {
    const a = full.get(id);
    const b = light.get(id);

    const stock = b?.total_stock ?? 0;
    if (stock <= 0) continue; // ✅ only in-stock products

    const row: Record<string, string> = {
        product_id: id,
        product_name_pol: a?.product_name_pol ?? "",
        category_id: a?.category_id ?? "",
        category: a?.category ?? "",
        producer: a?.producer ?? "",
        vat: a?.vat ?? "",
        price_gross: b?.price_gross ?? "",
        price_net: b?.price_net ?? "",
        total_stock: String(stock),
        card_url: a?.card_url ?? "",
        image_url: a?.image_url ?? "",
        icon_url: a?.icon_url ?? "",
    };

    lines.push(headers.map((h) => escapeCsv(row[h] ?? "")).join(","));
  }

  await Deno.mkdir("./out", { recursive: true });
  await Deno.writeTextFile(outCsv, lines.join("\n"));
  console.log(`Wrote: ${outCsv} (${sortedIds.length} products)`);
}

if (import.meta.main) main();
