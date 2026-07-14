"""
FMCG Deal Intelligence Newsletter — Streamlit Demo App

Runs the full pipeline live on button click:
Ingestion -> Cleaning/Dedup -> Relevance & Credibility Scoring -> Newsletter Generation

Run locally:
    streamlit run app/app.py

Requires environment variables (or Streamlit secrets):
    NEWSAPI_KEY
    GEMINI_API_KEY
"""

import os
import sys
import json

import streamlit as st

# Allow importing modules from the sibling src/ folder
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import ingest
import clean
import score
import newsletter as newsletter_module


st.set_page_config(page_title="FMCG Deal Intelligence", page_icon="📰", layout="wide")


def get_api_key(name):
    """Check Streamlit secrets first (for cloud deployment), then env vars (for local)."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        # No secrets.toml file present (expected for local runs) — fall through to env vars
        pass
    return os.environ.get(name)


NEWSAPI_KEY = get_api_key("NEWSAPI_KEY")
GEMINI_API_KEY = get_api_key("GEMINI_API_KEY")

# Make keys available to the imported modules (they read from os.environ)
if NEWSAPI_KEY:
    os.environ["NEWSAPI_KEY"] = NEWSAPI_KEY
if GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY


st.title("📰 FMCG Deal Intelligence Newsletter")
st.caption(
    "An agentic pipeline that sources, cleans, filters, and summarizes "
    "recent FMCG M&A and investment news into a skimmable newsletter."
)

with st.sidebar:
    st.header("Pipeline Settings")
    days_back = st.slider("Days of news to search", min_value=3, max_value=30, value=14)
    st.markdown("---")
    st.markdown("**Pipeline stages:**")
    st.markdown("1. Ingestion (NewsAPI)\n2. Clean & Deduplicate\n3. Relevance & Credibility Scoring\n4. Newsletter Generation (Gemini)")

missing_keys = []
if not NEWSAPI_KEY:
    missing_keys.append("NEWSAPI_KEY")
if not GEMINI_API_KEY:
    missing_keys.append("GEMINI_API_KEY")

if missing_keys:
    st.error(
        f"Missing API key(s): {', '.join(missing_keys)}. "
        "Set them as environment variables before running, or add them to "
        "Streamlit secrets when deploying."
    )
    st.stop()

run_button = st.button("🚀 Generate Latest Newsletter", type="primary")

if run_button:
    progress = st.progress(0, text="Starting pipeline...")

    # Stage 1: Ingestion
    progress.progress(10, text="Stage 1/4: Fetching FMCG news articles...")
    raw_articles = ingest.fetch_all_articles(days_back=days_back)
    st.session_state["raw_count"] = len(raw_articles)

    # Stage 2: Cleaning & Dedup
    progress.progress(40, text="Stage 2/4: Cleaning and deduplicating...")
    basic_cleaned = clean.basic_clean(raw_articles)
    clean_articles = clean.remove_near_duplicates(basic_cleaned)
    st.session_state["clean_count"] = len(clean_articles)

    # Stage 3: Relevance + Credibility Scoring
    progress.progress(65, text="Stage 3/4: Filtering for relevance & scoring credibility...")
    scored_articles = score.score_articles(clean_articles)
    st.session_state["scored_count"] = len(scored_articles)
    st.session_state["scored_articles"] = scored_articles

    if not scored_articles:
        progress.empty()
        st.warning(
            "No relevant FMCG deal articles found in this time window. "
            "Try increasing 'Days of news to search' in the sidebar."
        )
        st.stop()

    # Stage 4: Newsletter Generation
    progress.progress(85, text="Stage 4/4: Generating newsletter with Gemini...")
    newsletter_text = newsletter_module.generate_newsletter(scored_articles)
    st.session_state["newsletter_text"] = newsletter_text

    progress.progress(100, text="Done!")
    progress.empty()

# Display results if available in session state
if "newsletter_text" in st.session_state:
    col1, col2, col3 = st.columns(3)
    col1.metric("Raw articles fetched", st.session_state.get("raw_count", "-"))
    col2.metric("After cleaning/dedup", st.session_state.get("clean_count", "-"))
    col3.metric("Relevant deal articles", st.session_state.get("scored_count", "-"))

    st.markdown("---")
    st.markdown(st.session_state["newsletter_text"])

    st.markdown("---")
    st.download_button(
        "⬇️ Download Newsletter (Markdown)",
        data=st.session_state["newsletter_text"],
        file_name="fmcg_newsletter.md",
        mime="text/markdown",
    )

    with st.expander("View raw scored article data (JSON)"):
        st.json(st.session_state["scored_articles"])

    scored_json = json.dumps(st.session_state["scored_articles"], indent=2, ensure_ascii=False)
    st.download_button(
        "⬇️ Download Raw Data (JSON)",
        data=scored_json,
        file_name="scored_articles.json",
        mime="application/json",
    )
else:
    st.info("Click **Generate Latest Newsletter** above to run the pipeline live.")
