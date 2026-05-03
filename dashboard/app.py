import streamlit as st
import plotly.express as px
from data import load_fct_apps, load_category_summary

st.set_page_config(
    page_title="Apple Subscription App Analytics",
    page_icon="🍎",
    layout="wide",
)

st.title("Apple Subscription App Analytics")
st.caption("Data sourced from iTunes Search API · Transformed via dbt · Powered by Snowflake")

# --- Load data ---
df = load_fct_apps()
cat_df = load_category_summary()

# --- Sidebar filters ---
st.sidebar.header("Filters")
all_categories = sorted(df["category_name"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Category", all_categories, default=all_categories
)
selected_price_tiers = st.sidebar.multiselect(
    "Price Tier", ["Free", "Paid"], default=["Free", "Paid"]
)

filtered = df[
    df["category_name"].isin(selected_categories) &
    df["price_tier"].isin(selected_price_tiers)
]

# --- KPI row ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Apps", f"{len(filtered):,}")
col2.metric("Avg Rating", f"{filtered['rating'].mean():.2f}")
paid_apps = filtered[filtered["price_tier"] == "Paid"]["price"]
avg_paid = paid_apps.mean() if len(paid_apps) > 0 else 0
col3.metric("Avg Price (Paid)", f"${avg_paid:.2f}")
pct_free = (filtered["price_tier"] == "Free").mean() * 100
col4.metric("% Free", f"{pct_free:.0f}%")

st.divider()

# --- Tabs ---
tab1, tab2 = st.tabs(["Descriptive Analytics", "Diagnostic Analytics"])

with tab1:
    st.subheader("Apps by Category")
    cat_counts = (
        filtered.groupby("category_name")
        .size()
        .reset_index(name="app_count")
        .sort_values("app_count", ascending=False)
        .head(15)
    )
    fig1 = px.bar(
        cat_counts, x="app_count", y="category_name", orientation="h",
        labels={"app_count": "Number of Apps", "category_name": "Category"},
        color="app_count", color_continuous_scale="Blues",
    )
    fig1.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Free vs Paid Distribution")
        tier_counts = filtered["price_tier"].value_counts().reset_index()
        tier_counts.columns = ["price_tier", "count"]
        fig2 = px.pie(tier_counts, names="price_tier", values="count",
                      color_discrete_map={"Free": "#4A90D9", "Paid": "#E8734A"})
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.subheader("Rating Distribution")
        fig3 = px.histogram(filtered, x="rating", nbins=20,
                            labels={"rating": "Average Rating", "count": "Apps"},
                            color_discrete_sequence=["#4A90D9"])
        st.plotly_chart(fig3, use_container_width=True)

with tab2:
    st.subheader("Rating vs Price (Paid Apps Only)")
    paid = filtered[filtered["price_tier"] == "Paid"].copy()
    fig4 = px.scatter(
        paid, x="price", y="rating", color="category_name",
        hover_data=["app_name", "seller_name", "rating_count"],
        labels={"price": "Price ($)", "rating": "Avg Rating", "category_name": "Category"},
        opacity=0.6,
    )
    fig4.update_layout(legend_title="Category")
    st.plotly_chart(fig4, use_container_width=True)

    col_c, col_d = st.columns(2)
    top10_cats = cat_counts.head(10)["category_name"].tolist()
    with col_c:
        st.subheader("Rating Bucket by Category (Top 10)")
        bucket_df = filtered[filtered["category_name"].isin(top10_cats)]
        bucket_counts = (
            bucket_df.groupby(["category_name", "rating_bucket"])
            .size()
            .reset_index(name="count")
        )
        fig5 = px.bar(
            bucket_counts, x="category_name", y="count", color="rating_bucket",
            barmode="stack",
            labels={"category_name": "Category", "count": "Apps", "rating_bucket": "Rating"},
            color_discrete_map={
                "Excellent": "#2ecc71", "Good": "#3498db",
                "Average": "#f39c12", "Below Average": "#e74c3c"
            },
        )
        fig5.update_xaxes(tickangle=45)
        st.plotly_chart(fig5, use_container_width=True)

    with col_d:
        st.subheader("Avg Rating by Price Tier & Category (Top 10)")
        tier_rating = (
            filtered[filtered["category_name"].isin(top10_cats)]
            .groupby(["category_name", "price_tier"])["rating"]
            .mean()
            .reset_index()
        )
        fig6 = px.bar(
            tier_rating, x="category_name", y="rating", color="price_tier",
            barmode="group",
            labels={"category_name": "Category", "rating": "Avg Rating", "price_tier": "Price Tier"},
            color_discrete_map={"Free": "#4A90D9", "Paid": "#E8734A"},
        )
        fig6.update_xaxes(tickangle=45)
        st.plotly_chart(fig6, use_container_width=True)

    st.subheader("Top 10 Sellers by App Count")
    top_sellers = (
        filtered.groupby("seller_name")
        .size()
        .reset_index(name="app_count")
        .sort_values("app_count", ascending=False)
        .head(10)
    )
    fig7 = px.bar(
        top_sellers, x="app_count", y="seller_name", orientation="h",
        labels={"app_count": "Number of Apps", "seller_name": "Seller"},
        color="app_count", color_continuous_scale="Oranges",
    )
    fig7.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig7, use_container_width=True)
