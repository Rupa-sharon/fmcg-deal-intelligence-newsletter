"""
Step 3: Relevance Filtering + Credibility Scoring
Reads data/clean_articles.json, filters for genuine FMCG-deal relevance,
tags each article with a credibility tier, and saves to data/scored_articles.json

Relevance logic (transparent, rule-based):
- Must mention at least one known FMCG company/brand/sector term
- Must mention at least one deal-related term (acquisition, merger, funding, etc.)
- Both title AND description are checked

Credibility logic (transparent, rule-based):
- Tier 1: well-established, high-trust business/financial news outlets
- Tier 2: everything else (not excluded, just labeled lower-confidence)
"""

import json
import os

CLEAN_PATH = "data/clean_articles.json"
SCORED_PATH = "data/scored_articles.json"

# Known FMCG companies/brands (extend as needed)
FMCG_COMPANIES = [
    "fmcg", "hul", "hindustan unilever", "itc", "nestle", "britannia",
    "dabur", "marico", "godrej consumer", "colgate", "p&g", "procter & gamble",
    "patanjali", "emami", "tata consumer", "adani wilmar", "varun beverages",
    "parle", "haldiram", "amul", "mother dairy", "zydus wellness",
]

# Broader FMCG category/sector terms (catches deals that don't name a big
# company but are clearly in the FMCG space, e.g. a coffee brand or D2C
# food startup being acquired)
FMCG_CATEGORY_TERMS = [
    "consumer goods", "consumer product", "personal care", "home care",
    "beverage", "snack", "dairy", "d2c", "skincare", "consumer packaged goods",
    "cpg", "grocery", "household product", "confectionery", "coffee", "tea",
    "nutrition", "wellness", "food", "bakery", "f&b", "juice",
]

FMCG_TERMS = FMCG_COMPANIES + FMCG_CATEGORY_TERMS

# Deal-related terms
DEAL_TERMS = [
    "acquisition", "acquire", "acquires", "acquired", "merger", "merge",
    "funding", "invest", "investment", "stake", "buyout", "takeover",
    "raises", "raised", "valuation", "deal", "ipo",
]

# Source credibility tiers
TIER_1_SOURCES = {
    "reuters", "the economic times", "economic times", "mint", "livemint",
    "business standard", "the hindu businessline", "bloomberg", "bloombergquint",
    "financial times", "moneycontrol", "cnbc", "cnbc-tv18", "the times of india",
    "business today", "forbes india", "vccircle",
}

# Terms that signal the article is NOT actually about FMCG, even if it
# briefly mentions an FMCG company name (e.g. multi-stock market roundups
# that mention "Marico" alongside unrelated oil/petroleum/banking news)
NEGATIVE_TERMS = [
    "petroleum", "refinery", "crude oil", "bpcl", "ongc", "hpcl", "iocl",
    "natural gas", "coal india", "steel plant", "cement plant",
    "telecom spectrum", "banking license", "insurance regulator",
]


def load_clean_articles(path=CLEAN_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_relevant(article):
    """Check article mentions both an FMCG term and a deal term, and does
    NOT contain negative terms that signal it's a different-sector story
    that just happens to mention an FMCG name in passing (e.g. multi-stock
    market roundup articles)."""
    text = f"{article['title']} {article.get('description', '')}".lower()

    has_fmcg_term = any(term in text for term in FMCG_TERMS)
    has_deal_term = any(term in text for term in DEAL_TERMS)
    has_negative_term = any(term in text for term in NEGATIVE_TERMS)

    return has_fmcg_term and has_deal_term and not has_negative_term


def credibility_tier(source_name):
    """Return 'Tier 1' for known trusted outlets, 'Tier 2' otherwise."""
    normalized = (source_name or "").strip().lower()
    if normalized in TIER_1_SOURCES:
        return "Tier 1"
    return "Tier 2"


def score_articles(articles):
    scored = []
    for a in articles:
        if not is_relevant(a):
            continue
        a["credibility_tier"] = credibility_tier(a["source"])
        scored.append(a)
    return scored


def save_scored_articles(articles, path=SCORED_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(articles)} relevant, scored articles to {path}")


if __name__ == "__main__":
    clean = load_clean_articles()
    print(f"Loaded {len(clean)} clean articles")

    scored = score_articles(clean)
    print(f"After relevance filtering: {len(scored)} articles remain")

    tier1_count = sum(1 for a in scored if a["credibility_tier"] == "Tier 1")
    tier2_count = len(scored) - tier1_count
    print(f"  Tier 1 sources: {tier1_count} | Tier 2 sources: {tier2_count}")

    save_scored_articles(scored)
