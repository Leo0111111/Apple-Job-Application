import os
import requests
import snowflake.connector
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SEARCH_TERMS = [
    "subscription", "streaming", "music", "fitness", "meditation",
    "productivity", "news", "education", "entertainment", "health"
]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS RAW_ITUNES_APPS (
    app_id          VARCHAR,
    app_name        VARCHAR,
    seller_name     VARCHAR,
    category        VARCHAR,
    price           FLOAT,
    currency        VARCHAR,
    rating          FLOAT,
    rating_count    INTEGER,
    description     VARCHAR,
    release_date    VARCHAR,
    version         VARCHAR,
    content_rating  VARCHAR,
    loaded_at       TIMESTAMP_NTZ,
    PRIMARY KEY (app_id)
)
"""


def fetch_apps(term: str, limit: int = 200) -> list[dict]:
    url = "https://itunes.apple.com/search"
    params = {
        "term": term,
        "entity": "software",
        "limit": limit,
        "country": "us",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])


def parse_app(app: dict) -> dict:
    return {
        "app_id": str(app.get("trackId", "")),
        "app_name": app.get("trackName", ""),
        "seller_name": app.get("sellerName", ""),
        "category": app.get("primaryGenreName", ""),
        "price": float(app.get("price", 0.0)),
        "currency": app.get("currency", "USD"),
        "rating": float(app.get("averageUserRating", 0.0)),
        "rating_count": int(app.get("userRatingCount", 0)),
        "description": (app.get("description", "") or "")[:4000],
        "release_date": app.get("releaseDate", ""),
        "version": app.get("version", ""),
        "content_rating": app.get("contentAdvisoryRating", ""),
        "loaded_at": datetime.utcnow(),
    }


def load_to_snowflake(records: list[dict]) -> int:
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
    )
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)

    insert_sql = """
    MERGE INTO RAW_ITUNES_APPS t
    USING (SELECT %(app_id)s AS app_id) s ON t.app_id = s.app_id
    WHEN MATCHED THEN UPDATE SET
        app_name       = %(app_name)s,
        seller_name    = %(seller_name)s,
        category       = %(category)s,
        price          = %(price)s,
        currency       = %(currency)s,
        rating         = %(rating)s,
        rating_count   = %(rating_count)s,
        description    = %(description)s,
        release_date   = %(release_date)s,
        version        = %(version)s,
        content_rating = %(content_rating)s,
        loaded_at      = %(loaded_at)s
    WHEN NOT MATCHED THEN INSERT (
        app_id, app_name, seller_name, category, price, currency,
        rating, rating_count, description, release_date, version,
        content_rating, loaded_at
    ) VALUES (
        %(app_id)s, %(app_name)s, %(seller_name)s, %(category)s, %(price)s, %(currency)s,
        %(rating)s, %(rating_count)s, %(description)s, %(release_date)s, %(version)s,
        %(content_rating)s, %(loaded_at)s
    )
    """
    for record in records:
        cur.execute(insert_sql, record)

    conn.commit()
    cur.close()
    conn.close()
    return len(records)


def main():
    seen = set()
    all_apps = []

    for term in SEARCH_TERMS:
        print(f"Fetching: {term}")
        results = fetch_apps(term)
        for app in results:
            app_id = str(app.get("trackId", ""))
            if app_id and app_id not in seen:
                seen.add(app_id)
                all_apps.append(parse_app(app))

    print(f"Unique apps fetched: {len(all_apps)}")
    loaded = load_to_snowflake(all_apps)
    print(f"Loaded {loaded} records to Snowflake RAW_ITUNES_APPS")


if __name__ == "__main__":
    main()
