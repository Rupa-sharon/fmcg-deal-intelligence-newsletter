"""
Step 2: Cleaning & Deduplication
Reads data/raw_articles.json, removes exact and near-duplicate articles,
and saves clean results to data/clean_articles.json

Dedup strategy:
1. Exact duplicate URLs -> dropped immediately
2. Near-duplicate titles -> TF-IDF + cosine similarity on title text
   (catches the same story reported by multiple outlets with slightly
   different wording)
"""

import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

RAW_PATH = "data/raw_articles.json"
CLEAN_PATH = "data/clean_articles.json"

# Titles with similarity above this threshold are considered near-duplicates
SIMILARITY_THRESHOLD = 0.75


def load_raw_articles(path=RAW_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def basic_clean(articles):
    """Drop articles missing essential fields, strip whitespace, dedup by exact URL."""
    seen_urls = set()
    cleaned = []

    for a in articles:
        title = (a.get("title") or "").strip()
        url = (a.get("url") or "").strip()
        description = (a.get("description") or "").strip()
        source = (a.get("source", {}) or {}).get("name", "Unknown")
        published_at = a.get("publishedAt", "")

        # Skip articles with no title/url, or NewsAPI's "[Removed]" placeholders
        if not title or not url or title == "[Removed]":
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        cleaned.append({
            "title": title,
            "description": description,
            "url": url,
            "source": source,
            "published_at": published_at,
            "matched_query": a.get("matched_query", ""),
        })

    return cleaned


def remove_near_duplicates(articles, threshold=SIMILARITY_THRESHOLD):
    """Use TF-IDF cosine similarity on titles to catch same story, different outlet."""
    if len(articles) <= 1:
        return articles

    titles = [a["title"] for a in articles]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(titles)
    sim_matrix = cosine_similarity(tfidf_matrix)

    keep = [True] * len(articles)

    for i in range(len(articles)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(articles)):
            if not keep[j]:
                continue
            if sim_matrix[i][j] >= threshold:
                # Keep the one with the longer description (usually more informative)
                if len(articles[i].get("description", "")) >= len(articles[j].get("description", "")):
                    keep[j] = False
                else:
                    keep[i] = False
                    break

    deduped = [a for a, k in zip(articles, keep) if k]
    return deduped


def save_clean_articles(articles, path=CLEAN_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(articles)} clean, deduplicated articles to {path}")


if __name__ == "__main__":
    raw = load_raw_articles()
    print(f"Loaded {len(raw)} raw articles")

    basic_cleaned = basic_clean(raw)
    print(f"After basic cleaning + exact URL dedup: {basic_cleaned.__len__()} articles")

    final = remove_near_duplicates(basic_cleaned)
    print(f"After near-duplicate removal: {len(final)} articles")

    save_clean_articles(final)
