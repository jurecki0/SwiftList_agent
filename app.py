from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

CSV_PATH = Path("data") / "products_flat.csv"

st.set_page_config(page_title="Stock export viewer", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
    return df

df = load_data()

st.title("Stock export viewer")

# Basic cleanup for grouping
df["category_label"] = df.apply(
    lambda r: f'{r["category_name"]} ({r["category_id"]})' if r["category_name"] else f'Unknown ({r["category_id"]})',
    axis=1
)

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
    st.plotly_chart(fig, use_container_width=True)  # Streamlit renders Plotly charts [web:60][web:57]

with right:
    st.subheader("Products (sorted by category)")
    # Optional filter
    chosen = st.multiselect(
        "Filter by category (optional)",
        options=counts["category_label"].tolist(),
        default=[]
    )
    view = df if not chosen else df[df["category_label"].isin(chosen)]

    view = view.sort_values(["category_name", "product_name_pol", "product_id"], ascending=True)

    st.dataframe(
        view[["product_id", "product_name_pol", "category_id", "category_name"]],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Category summary")
st.dataframe(counts, use_container_width=True, hide_index=True)
