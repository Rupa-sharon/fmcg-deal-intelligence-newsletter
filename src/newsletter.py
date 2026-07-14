"""
Step 4: Newsletter Generation
Reads data/scored_articles.json, sends the structured article data to
Gemini, and generates a business-readable FMCG deal-intelligence newsletter.
Saves output to data/newsletter.md
"""

import os
import json
from google import genai

SCORED_PATH = "data/scored_articles.json"
OUTPUT_PATH = "data/newsletter.md"

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY environment variable not set. "
            "Run: $env:GEMINI_API_KEY='your_key_here'  (PowerShell)"
        )
    return key

MODEL_NAME = "gemini-3.5-flash"


def load_scored_articles(path=SCORED_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_prompt(articles):
    """Constructs a prompt with structured article data for the LLM to summarize."""
    article_blocks = []
    for i, a in enumerate(articles, 1):
        block = (
            f"{i}. Title: {a['title']}\n"
            f"   Description: {a.get('description', 'N/A')}\n"
            f"   Source: {a['source']} ({a['credibility_tier']})\n"
            f"   Published: {a.get('published_at', 'N/A')}\n"
            f"   URL: {a['url']}"
        )
        article_blocks.append(block)

    articles_text = "\n\n".join(article_blocks)

    prompt = f"""You are a business analyst writing a concise FMCG industry
intelligence newsletter for busy executives who want to skim recent M&A and
investment activity in 2 minutes.

Below is a list of relevant, deduplicated news articles about FMCG deals,
each tagged with a source credibility tier (Tier 1 = highly trusted business
outlets, Tier 2 = other sources).

Using ONLY the information provided below (do not invent facts), write a
newsletter with this structure:

1. A short title and one-line intro (today's date context: recent weeks)
2. A "Top Highlights" section: 2-3 bullet points on the most significant deals
3. A "Deal Roundup" section: for each article, write a 2-3 line summary
   covering who, what, and why it matters. Include the source name and
   credibility tier in parentheses. Flag Tier 2 sourced items with a note
   that the info hasn't been independently corroborated by a Tier-1 outlet.
4. A short closing note if there are notable patterns (e.g. many deals in
   one FMCG sub-sector)

Keep the tone professional, concise, and skimmable. Use markdown formatting
with headers and bullet points. Do not use overly promotional language.

Articles:
{articles_text}
"""
    return prompt


def generate_newsletter(articles):
    client = genai.Client(api_key=get_api_key())
    prompt = build_prompt(articles)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    return response.text


def save_newsletter(text, path=OUTPUT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Newsletter saved to {path}")


if __name__ == "__main__":
    articles = load_scored_articles()
    print(f"Loaded {len(articles)} scored articles")

    print("Generating newsletter with Gemini...")
    newsletter_text = generate_newsletter(articles)

    save_newsletter(newsletter_text)
    print("\n--- Newsletter Preview ---\n")
    print(newsletter_text[:500])
