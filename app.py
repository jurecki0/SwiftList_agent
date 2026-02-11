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
    df["total_stock"] = pd.to_numeric(df["total_stock"], errors="coerce").fillna(0).astype(int)
    df["category_label"] = df.apply(
        lambda r:
            f'{r["category_name"]} ({r["category_id"]})'
            if r["category_name"] else f'Unknown ({r["category_id"]})',
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

    view = view.sort_values(["category_name", "product_name_pol", "product_id"], ascending=True)

    st.dataframe(
        view[["product_id", "product_name_pol", "category_id", "category_name", "producer", "total_stock"]],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Category summary")
st.dataframe(counts, use_container_width=True, hide_index=True)

# Extra: high‑level stock view
st.subheader("Stock at a glance")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total products", f"{len(df):,}")
with col2:
    st.metric("With non‑zero stock", f"{(df['total_stock'] > 0).sum():,}")
with col3:
    st.metric("Total stock", f"{int(df['total_stock'].sum()):,}")
