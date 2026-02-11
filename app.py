from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

CSV_PATH = Path("data") / "products_with_stock.csv"

st.set_page_config(page_title="Stock export viewer", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
    if "producer" not in df.columns:
        df["producer"] = ""
    if "category" not in df.columns:
        df["category"] = ""
    if "sizes" not in df.columns:
        df["sizes"] = ""
    for c in ("price_gross", "price_net", "vat", "stock_value", "image_url", "icon_url", "card_url"):
        if c not in df.columns:
            df[c] = ""
    df["total_stock"] = pd.to_numeric(df["total_stock"], errors="coerce").fillna(0).astype(int)
    df["category_label"] = df.apply(
        lambda r:
            f'{r["category"]} ({r["category_id"]})'
            if r.get("category") else f'Unknown ({r["category_id"]})',
        axis=1
    )
    return df

df = load_data()

st.title("Stock export viewer")



left, right = st.columns([1, 2])

with left:
    st.subheader("Category distribution")
    counts = (
        df.groupby("category_label", dropna=False)
          .size()
          .reset_index(name="products")
          .sort_values("products", ascending=False)
    )

    top_n = st.slider("Show top N categories", 1, 20, 10)
    counts_top = counts.head(top_n)

    fig = px.pie(counts_top, names="category_label", values="products")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Products (sorted by category)")

    only_in_stock = st.checkbox("Show only products with stock > 0", value=False)

    chosen = st.multiselect(
        "Filter by category (optional)",
        options=counts["category_label"].tolist(),
        default=[]
    )

    view = df if not chosen else df[df["category_label"].isin(chosen)]

    if only_in_stock:
        view = view[view["total_stock"] > 0]

    view = view.sort_values(["category", "product_name_pol", "product_id"], ascending=True)

    display_cols = ["product_id", "product_name_pol", "category", "producer", "sizes", "total_stock"]
    for c in ("price_gross", "price_net", "vat", "stock_value"):
        if c in view.columns:
            display_cols.append(c)
    st.dataframe(
        view[display_cols],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Category summary")
st.dataframe(counts, use_container_width=True, hide_index=True)

# Extra: high‑level stock view
st.subheader("Stock at a glance")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total products", f"{len(df):,}")
with col2:
    st.metric("With non‑zero stock", f"{(df['total_stock'] > 0).sum():,}")
with col3:
    st.metric("Total stock", f"{int(df['total_stock'].sum()):,}")
with col4:
    stock_val = pd.to_numeric(df["stock_value"], errors="coerce").fillna(0).sum()
    st.metric("Stock value (PLN)", f"{stock_val:,.2f}" if stock_val else "—")

# Product images — check out images and product page
st.subheader("Product images")
products_with_images = df[(df["image_url"].str.strip() != "") | (df["icon_url"].str.strip() != "")]
if products_with_images.empty:
    st.caption("No product image URLs in data. Re-run parse_to_csv.py and combine_products_with_stock.py after adding image extraction.")
else:
    options = products_with_images.apply(
        lambda r: f"{r['product_id']} — {(str(r.get('product_name_pol') or ''))[:50]}{'…' if len(str(r.get('product_name_pol') or '')) > 50 else ''}",
        axis=1,
    ).tolist()
    option_to_row = dict(zip(options, products_with_images.to_dict("records")))
    selected_label = st.selectbox("Choose a product to view image and link", options=options, key="image_product")
    if selected_label and selected_label in option_to_row:
        row = option_to_row[selected_label]
        img_col, link_col = st.columns([1, 2])
        with img_col:
            url = (row.get("icon_url") or "").strip() or (row.get("image_url") or "").strip()
            if url:
                st.image(url, caption=f"Product {row.get('product_id', '')}", use_container_width=True)
            else:
                st.caption("No image URL")
        with link_col:
            card = (row.get("card_url") or "").strip()
            if card:
                st.markdown(f"**Product page:** [Open in browser]({card})")
            image_url = (row.get("image_url") or "").strip()
            if image_url and image_url != url:
                st.markdown(f"**Full image:** [Open image]({image_url})")
            st.caption(f"ID: {row.get('product_id')} · {row.get('product_name_pol', '')[:80]}")
