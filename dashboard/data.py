import streamlit as st
import snowflake.connector
import pandas as pd


def _get_conn():
    cfg = st.secrets["snowflake"]
    return snowflake.connector.connect(
        account=cfg["account"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        warehouse=cfg["warehouse"],
        schema=cfg["schema"],
    )


@st.cache_data(ttl=600)
def load_fct_apps() -> pd.DataFrame:
    conn = _get_conn()
    query = """
        SELECT
            f.app_id,
            f.app_name,
            f.price,
            f.currency,
            f.rating,
            f.rating_count,
            f.content_rating,
            f.price_tier,
            f.rating_bucket,
            c.category_name,
            s.seller_name
        FROM fct_apps f
        LEFT JOIN dim_category c ON f.category_id = c.category_id
        LEFT JOIN dim_seller s ON f.seller_id = s.seller_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df.columns = [col.lower() for col in df.columns]
    return df


@st.cache_data(ttl=600)
def load_category_summary() -> pd.DataFrame:
    conn = _get_conn()
    query = """
        SELECT
            c.category_name,
            COUNT(*) AS app_count,
            ROUND(AVG(f.rating), 2) AS avg_rating,
            ROUND(AVG(f.price), 2) AS avg_price,
            SUM(CASE WHEN f.price_tier = 'Free' THEN 1 ELSE 0 END) AS free_count,
            SUM(CASE WHEN f.price_tier = 'Paid' THEN 1 ELSE 0 END) AS paid_count
        FROM fct_apps f
        LEFT JOIN dim_category c ON f.category_id = c.category_id
        GROUP BY c.category_name
        ORDER BY app_count DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df.columns = [col.lower() for col in df.columns]
    return df
