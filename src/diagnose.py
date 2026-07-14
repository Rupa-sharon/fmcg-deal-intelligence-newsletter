"""
Diagnostic: shows titles of clean articles that got REJECTED by the relevance
filter, so we can see if the filter is too strict.
"""

import json
from score import is_relevant, FMCG_TERMS, DEAL_TERMS

with open("data/clean_articles.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

rejected = [a for a in articles if not is_relevant(a)]

print(f"Total articles: {len(articles)}")
print(f"Rejected: {len(rejected)}\n")
print("--- Sample of rejected titles ---")
for a in rejected[:20]:
    print(f"- {a['title']}")
