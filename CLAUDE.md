# CLAUDE.md — Subscription App Analytics Pipeline

## Project Overview

This is a portfolio analytics engineering project targeting the **Data Scientist, Subscription Analytics** role at Apple. It demonstrates end-to-end data pipeline skills: API ingestion, Snowflake data warehousing, dbt transformation, Streamlit dashboarding, and a Claude Code-powered knowledge base.

**Owner:** Leo Chan  
**Repo:** https://github.com/Leo0111111/Apple-Job-Application  
**Job posting:** `docs/job-posting.pdf`

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data Warehouse | Snowflake (AWS US East 1) |
| Transformation | dbt |
| Orchestration | GitHub Actions (scheduled) |
| Dashboard | Streamlit (deployed to Streamlit Community Cloud) |
| Knowledge Base | Claude Code (scrape → summarize → query) |
| AI Development | Claude Code + Superpowers |

---

## Data Sources

- **Source 1 (API):** iTunes Search API — pulls subscription app data (app name, price, rating, review count, category, seller). No API key required.
- **Source 2 (Web scrape):** Apple newsroom articles, earnings call transcripts, and subscription industry reports. Scraped via Firecrawl or similar.

---

## Directory Structure

```
├── docs/               # Proposal, job posting, resume
├── pipeline/           # Python ingestion scripts
│   ├── itunes_api.py   # Source 1: iTunes Search API → Snowflake raw
│   └── scraper.py      # Source 2: web scrape → knowledge/raw/
├── dbt/                # dbt project (staging + mart models)
├── dashboard/          # Streamlit app
├── knowledge/
│   ├── raw/            # Scraped source documents (15+ files, 3+ sites)
│   ├── wiki/           # Claude Code-generated synthesis pages
│   └── index.md        # Index of all wiki pages with one-line summaries
├── .github/workflows/  # GitHub Actions pipelines
├── .gitignore
├── CLAUDE.md           # This file
└── README.md
```

---

## Snowflake Schema Design

Three-layer architecture:
- **Raw:** Unmodified data as loaded from sources
- **Staging:** Cleaned, renamed, type-cast models (one per source)
- **Mart:** Star schema — fact table(s) + dimension tables for dashboard queries

---

## Knowledge Base

The `knowledge/` folder is a queryable knowledge base about Apple's subscription ecosystem.

### How to query it

Ask questions like:
- "What does my knowledge base say about Apple subscription growth trends?"
- "Summarize the key themes across my wiki pages."
- "What do the raw sources say about Apple One pricing strategy?"

Claude Code reads `knowledge/wiki/` pages first (synthesized insights), then digs into `knowledge/raw/` for supporting evidence. The `knowledge/index.md` lists all wiki pages with one-line summaries.

### Wiki conventions

- Wiki pages synthesize across multiple sources — not just individual summaries
- Each wiki page cites which raw sources it draws from
- When answering questions, prefer wiki pages for high-level answers; use raw sources for specifics

---

## Credentials & Secrets

All credentials stored as environment variables. Never committed to git.

Required env vars:
- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PASSWORD`
- `SNOWFLAKE_DATABASE`
- `SNOWFLAKE_WAREHOUSE`
- `SNOWFLAKE_SCHEMA`

Store locally in `.env` (gitignored). Store in GitHub Actions as repository secrets.
