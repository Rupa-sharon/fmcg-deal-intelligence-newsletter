"""
Step 1: Ingestion
Fetches FMCG deal-related news articles from NewsAPI.org
Saves raw results to data/raw_articles.json
"""

import os
import json
import requests
from datetime import datetime, timedelta

# API key is read from environment variable — never hardcode it
def get_api_key():
    key = os.environ.get("NEWSAPI_KEY")
    if not key:
        raise ValueError(
            "NEWSAPI_KEY environment variable not set. "
            "Run: export NEWSAPI_KEY='your_key_here'"
        )
    return key

# Search queries targeting FMCG deal activity specifically
QUERIES = [
    "FMCG acquisition",
    "FMCG merger",
    "FMCG funding",
    "FMCG investment",
    "FMCG stake acquisition",
    "consumer goods acquisition India",
]

BASE_URL = "https://newsapi.org/v2/everything"


def fetch_articles_for_query(query, from_date, page_size=20):
    """Fetch articles for a single query from NewsAPI."""
    params = {
        "q": query,
        "from": from_date,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": page_size,
        "apiKey": get_api_key(),
    }
    response = requests.get(BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "ok":
        print(f"  Warning: query '{query}' returned status={data.get('status')}, "
              f"message={data.get('message')}")
        return []

    return data.get("articles", [])


def fetch_all_articles(days_back=14):
    """Fetch articles across all queries, tagging each with the query that found it."""
    from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    all_articles = []

    for query in QUERIES:
        print(f"Fetching: '{query}' (since {from_date})...")
        try:
            articles = fetch_articles_for_query(query, from_date)
            for a in articles:
                a["matched_query"] = query
            all_articles.extend(articles)
            print(f"  -> {len(articles)} articles found")
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching '{query}': {e}")

    return all_articles


def save_raw_articles(articles, path="data/raw_articles.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(articles)} raw articles to {path}")


if __name__ == "__main__":
    articles = fetch_all_articles(days_back=14)
    save_raw_articles(articles)
