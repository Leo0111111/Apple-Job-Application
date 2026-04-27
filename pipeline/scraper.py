import os
import re
import time
import requests
import snowflake.connector
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

RAW_DIR = Path(__file__).parent.parent / "knowledge" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; research-scraper/1.0)"}

SOURCES = [
    # Apple Newsroom — earnings & services
    {"url": "https://www.apple.com/newsroom/2024/01/apple-services-hit-all-time-revenue-record/", "site": "apple_newsroom"},
    {"url": "https://www.apple.com/newsroom/2023/08/apple-reports-third-quarter-results/", "site": "apple_newsroom"},
    {"url": "https://www.apple.com/newsroom/2024/02/apple-reports-first-quarter-results/", "site": "apple_newsroom"},
    {"url": "https://www.apple.com/newsroom/2023/11/apple-reports-fourth-quarter-results/", "site": "apple_newsroom"},
    {"url": "https://www.apple.com/newsroom/2023/05/apple-reports-second-quarter-results/", "site": "apple_newsroom"},
    {"url": "https://www.apple.com/newsroom/2022/10/apple-reports-fourth-quarter-results/", "site": "apple_newsroom"},
    {"url": "https://www.apple.com/newsroom/2022/07/apple-reports-third-quarter-results/", "site": "apple_newsroom"},
    {"url": "https://www.apple.com/newsroom/2024/05/apple-reports-second-quarter-results/", "site": "apple_newsroom"},
    # Business of Apps — subscription industry data
    {"url": "https://www.businessofapps.com/data/app-revenues/", "site": "businessofapps"},
    {"url": "https://www.businessofapps.com/data/apple-music-statistics/", "site": "businessofapps"},
    {"url": "https://www.businessofapps.com/data/apple-tv-statistics/", "site": "businessofapps"},
    {"url": "https://www.businessofapps.com/data/apple-arcade-statistics/", "site": "businessofapps"},
    {"url": "https://www.businessofapps.com/marketplace/app-subscription/research/app-subscription-statistics/", "site": "businessofapps"},
    {"url": "https://www.businessofapps.com/data/spotify-statistics/", "site": "businessofapps"},
    {"url": "https://www.businessofapps.com/data/netflix-statistics/", "site": "businessofapps"},
    # MacRumors — Apple subscription product news
    {"url": "https://www.macrumors.com/guide/apple-one/", "site": "macrumors"},
    {"url": "https://www.macrumors.com/guide/apple-tv-plus/", "site": "macrumors"},
    {"url": "https://www.macrumors.com/guide/apple-music/", "site": "macrumors"},
    {"url": "https://www.macrumors.com/guide/apple-arcade/", "site": "macrumors"},
    {"url": "https://www.macrumors.com/guide/apple-fitness-plus/", "site": "macrumors"},
]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS RAW_SCRAPED_ARTICLES (
    source_id       VARCHAR,
    url             VARCHAR,
    site            VARCHAR,
    title           VARCHAR,
    body_text       VARCHAR,
    word_count      INTEGER,
    scraped_at      TIMESTAMP_NTZ,
    PRIMARY KEY (source_id)
)
"""


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "_", text)[:80]


def scrape(url: str, site: str) -> dict | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"  SKIP {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove nav/footer/script noise
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    title = (soup.find("h1") or soup.find("title") or soup.new_tag("x"))
    title_text = title.get_text(strip=True)

    body = soup.find("article") or soup.find("main") or soup.body
    body_text = body.get_text(separator="\n", strip=True) if body else ""
    word_count = len(body_text.split())

    return {
        "url": url,
        "site": site,
        "title": title_text[:500],
        "body_text": body_text[:50000],
        "word_count": word_count,
        "scraped_at": datetime.now(timezone.utc),
    }


def save_to_file(record: dict, index: int) -> str:
    slug = slugify(record["title"]) or f"article_{index}"
    filename = f"{record['site']}_{slug}.md"
    filepath = RAW_DIR / filename

    content = f"# {record['title']}\n\n"
    content += f"**Source:** {record['site']}  \n"
    content += f"**URL:** {record['url']}  \n"
    content += f"**Scraped:** {record['scraped_at'].strftime('%Y-%m-%d')}  \n"
    content += f"**Words:** {record['word_count']}\n\n"
    content += "---\n\n"
    content += record["body_text"]

    filepath.write_text(content, encoding="utf-8")
    return filename


def load_to_snowflake(records: list[dict]):
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
    MERGE INTO RAW_SCRAPED_ARTICLES t
    USING (SELECT %(source_id)s AS source_id) s ON t.source_id = s.source_id
    WHEN MATCHED THEN UPDATE SET
        url        = %(url)s,
        site       = %(site)s,
        title      = %(title)s,
        body_text  = %(body_text)s,
        word_count = %(word_count)s,
        scraped_at = %(scraped_at)s
    WHEN NOT MATCHED THEN INSERT (
        source_id, url, site, title, body_text, word_count, scraped_at
    ) VALUES (
        %(source_id)s, %(url)s, %(site)s, %(title)s, %(body_text)s, %(word_count)s, %(scraped_at)s
    )
    """
    for r in records:
        cur.execute(insert_sql, r)

    conn.commit()
    cur.close()
    conn.close()


def main():
    scraped = []
    for i, source in enumerate(SOURCES):
        print(f"Scraping ({i+1}/{len(SOURCES)}): {source['url']}")
        record = scrape(source["url"], source["site"])
        if record is None:
            continue

        filename = save_to_file(record, i)
        source_id = f"{source['site']}_{i:03d}"
        record["source_id"] = source_id
        scraped.append(record)
        print(f"  Saved: knowledge/raw/{filename} ({record['word_count']} words)")
        time.sleep(1)

    print(f"\nTotal scraped: {len(scraped)} articles")
    print("Loading to Snowflake...")
    load_to_snowflake(scraped)
    print(f"Loaded {len(scraped)} records to Snowflake RAW_SCRAPED_ARTICLES")


if __name__ == "__main__":
    main()
