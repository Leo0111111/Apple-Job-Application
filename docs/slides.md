---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', sans-serif;
    background: #ffffff;
    color: #1d1d1f;
  }
  section.lead {
    background: #1d1d1f;
    color: #f5f5f7;
    text-align: center;
  }
  section.lead h1 {
    font-size: 2.4em;
    font-weight: 700;
    color: #f5f5f7;
  }
  section.lead h2 {
    font-size: 1.1em;
    font-weight: 300;
    color: #a1a1a6;
    margin-top: 0.5em;
  }
  section.lead p {
    color: #a1a1a6;
    font-size: 0.9em;
  }
  h1 {
    font-size: 1.6em;
    font-weight: 600;
    color: #1d1d1f;
    border-bottom: 2px solid #0071e3;
    padding-bottom: 0.2em;
  }
  h2 {
    font-size: 1.1em;
    color: #0071e3;
    font-weight: 500;
  }
  table {
    font-size: 0.85em;
    width: 100%;
  }
  th {
    background: #0071e3;
    color: white;
    padding: 8px 12px;
  }
  td {
    padding: 6px 12px;
    border-bottom: 1px solid #e5e5ea;
  }
  code {
    background: #f5f5f7;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 0.85em;
    color: #0071e3;
  }
  .insight-box {
    background: #f5f5f7;
    border-left: 4px solid #0071e3;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin: 8px 0;
  }
  strong {
    color: #0071e3;
  }
  footer {
    font-size: 0.7em;
    color: #a1a1a6;
  }
---

<!-- _class: lead -->

# Apple Subscription App Analytics Pipeline

## Data Scientist, Subscription Analytics

Leo Chan · ISBA 4715 · May 2026

---

# What Problem Does This Solve?

Apple's Subscription Analytics team needs to understand **which apps drive subscriber growth** and **what separates high-quality apps from low ones** across the App Store ecosystem.

This project builds a production-style analytics pipeline that answers:

- What does the subscription app landscape look like across categories?
- Do paid apps earn better ratings than free apps — and why?
- Where do pricing and quality signals cluster?

**Data sources:** iTunes Search API (1,779 apps, 25 categories) + 15 industry reports scraped from Apple Newsroom, Business of Apps, and MacRumors.

---

# Pipeline Architecture

```
iTunes Search API          pipeline/itunes_api.py
      │                              │
Web Scraper                 pipeline/scraper.py
  (15 sources)                       │
      │                              ▼
      │                   Snowflake RAW layer
      │                   RAW_ITUNES_APPS
      │                   RAW_SCRAPED_ARTICLES
      │                              │
      │                        dbt models
      │                   ┌──────────┴──────────┐
      │              STAGING views          MART tables
      │              stg_itunes_apps        fct_apps
      │              stg_scraped_articles   dim_category
      │                                     dim_seller
      │                              │
      │                    Streamlit Dashboard
      ▼
knowledge/raw/ → Claude Code → knowledge/wiki/
```

**Orchestration:** GitHub Actions runs both pipelines every Monday at 6–7am UTC.

---

# Data Model (Star Schema)

```
┌─────────────────┐       ┌──────────────────┐
│  dim_category   │       │   dim_seller     │
│─────────────────│       │──────────────────│
│ category_id  PK │       │ seller_id     PK │
│ category_name   │       │ seller_name      │
└────────┬────────┘       └────────┬─────────┘
         │                         │
         └──────────┬──────────────┘
                    │
         ┌──────────▼──────────────┐
         │       fct_apps          │
         │─────────────────────────│
         │ app_id          PK      │
         │ app_name                │
         │ category_id     FK      │
         │ seller_id       FK      │
         │ price                   │
         │ rating                  │
         │ rating_count            │
         │ price_tier  (Free/Paid) │
         │ rating_bucket           │
         └─────────────────────────┘
```

Three layers: **RAW** (unmodified) → **STAGING** (cleaned) → **MART** (star schema for analytics)

---

# Insight 1 — Descriptive

## Free Apps Dominate, But Paid Apps Rate Higher

The App Store catalog is overwhelmingly free-tier: the majority of the 1,779 apps ingested carry a `price = 0`. Yet when segmented by `price_tier`, paid apps consistently earn higher average ratings.

Top-performing categories by average rating trend toward paid or premium subscription models — **Productivity** and **Finance** apps earn the highest average ratings, while **Games** and **Entertainment** (heavily free) show the widest rating variance.

**So what?** Price tier is a signal of both quality investment and user intent — and both predict higher ratings.

---

# Insight 2 — Diagnostic

## Paid Users Are Higher-Signal Raters

The rating gap between free and paid apps isn't random. Two compounding effects drive it:

1. **Selection bias:** Users who pay for an app are more invested. They're less likely to leave a reflexive 1-star review and more likely to leave considered feedback.

2. **Developer incentive:** Developers who charge premium prices invest more in quality, support, and updates — because a bad review directly costs revenue.

This mirrors findings from the broader subscription market: Spotify's 44% DAU-to-MAU ratio and Apple Music's premium-only model both reflect that **paying users are higher-engagement users**, which correlates with retention and satisfaction.

---

# Recommendation

## Prioritize 4.0+ Rating Before Monetizing

**Finding:** Rating is the strongest observable predictor of App Store discoverability and user acquisition.

**Action:** Subscription app developers entering competitive categories (Games, Entertainment) should target a **4.0+ average rating** before introducing paid tiers or in-app purchases.

**Expected outcome:** Apps that hit the 4.0 threshold first see higher organic chart placement, which compounds into more reviews, which sustains the rating — a flywheel that mirrors Apple's own installed base → attach rate → services revenue model.

> *"The analytical framework Apple uses: installed base sets the ceiling; attach rate measures penetration efficiency."*
> — knowledge/wiki/subscription_analytics_kpis.md

---

# Knowledge Base

A Claude Code-curated wiki built from **15 scraped sources** across 3 sites.

| Wiki Page | Covers |
|---|---|
| Apple Services Overview | Music, TV+, Arcade, Fitness+, iCloud+, Apple One tiers |
| Subscription Market Landscape | Apple Music vs Spotify, Apple TV+ vs Netflix |
| Subscription Analytics KPIs | MAU, ARPU, churn, LTV, installed base flywheel |

**Query it in Claude Code:**
- *"What does my knowledge base say about Apple subscription growth?"*
- *"Summarize competitive landscape between Apple Music and Spotify."*
- *"What KPIs should a subscription analytics team track?"*

---

# Live Dashboard & Repo

## Dashboard

**URL:** https://apple-job-application-etjahl3bwgw9zkrnpqomyg.streamlit.app/

Charts: app distribution by category, rating by price tier, top sellers by rating count, price distribution.

## Repository

**GitHub:** https://github.com/Leo0111111/Apple-Job-Application

Includes full dbt project, pipeline scripts, GitHub Actions workflows, knowledge base, and this README.

---

<!-- _class: lead -->

# Thank You

**Leo Chan** · leo.chan9904@gmail.com

*Built with: Snowflake · dbt · Streamlit · GitHub Actions · Claude Code*
