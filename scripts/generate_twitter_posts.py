#!/usr/bin/env python3
"""
Twitter/X Post Generator for The Rider's Gang.

Reads article HTML files, extracts metadata, and generates:
1. A visually branded Twitter card HTML file (1200x675)
2. A thread text file with hook tweet + follow-up tweets

Posts are saved under social-media/twitter/<date>/ and are NOT linked
from the website.

Usage:
    python scripts/generate_twitter_posts.py --date 2026-03-06 \
        --articles articles/article-1.html articles/article-2.html
"""

import argparse
import os
import re
import sys
from datetime import datetime

from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, "..")
SOCIAL_DIR = os.path.join(BASE_DIR, "social-media", "twitter")


def read_article_metadata(filepath):
    """Extract metadata from an article HTML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    title_el = soup.select_one(".article__title")
    category_el = soup.select_one(".article__category")
    hero_el = soup.select_one(".article__hero-image")
    meta_el = soup.select_one(".article__meta")
    desc_el = soup.find("meta", attrs={"name": "description"})
    og_desc_el = soup.find("meta", attrs={"property": "og:description"})

    title = title_el.text.strip() if title_el else "Untitled"
    category = category_el.text.strip() if category_el else "Uncategorized"
    hero_src = hero_el.get("src", "") if hero_el else ""
    hero_alt = hero_el.get("alt", title) if hero_el else title
    description = desc_el.get("content", "").strip() if desc_el else ""
    og_description = og_desc_el.get("content", "").strip() if og_desc_el else description

    read_time = "5 min read"
    if meta_el:
        meta_text = meta_el.text
        match = re.search(r"(\d+)\s*min\s*read", meta_text)
        if match:
            read_time = f"{match.group(1)} min read"

    # Use 1200x675 (Twitter card ratio 16:9)
    twitter_src = re.sub(r"w=\d+", "w=1200", hero_src)
    twitter_src = re.sub(r"h=\d+", "h=675", twitter_src)

    # Extract first few paragraphs for thread content
    paragraphs = []
    for p in soup.select(".article__content p"):
        text = p.get_text(strip=True)
        if text and len(text) > 40:
            paragraphs.append(text)
        if len(paragraphs) >= 6:
            break

    return {
        "title": title,
        "category": category,
        "hero_src": twitter_src,
        "hero_alt": hero_alt,
        "description": description,
        "og_description": og_description,
        "read_time": read_time,
        "href": os.path.relpath(filepath, BASE_DIR),
        "paragraphs": paragraphs,
    }


def generate_thread_text(meta):
    """Generate a Twitter thread text file with hook + follow-up tweets."""
    tweets = []

    # Tweet 1: Hook using the description
    hook = f"{meta['description']}\n\nA thread. 🧵"
    tweets.append(hook)

    # Build follow-up tweets from article paragraphs
    for i, para in enumerate(meta["paragraphs"][:3]):
        # Trim to fit tweet length (280 chars minus some buffer)
        text = para[:260]
        if len(para) > 260:
            text = text.rsplit(" ", 1)[0] + "…"
        tweets.append(text)

    # Final tweet: CTA
    cta = (
        f"Read the full story: {meta['title']}\n\n"
        f"Link in bio. @TheRidersGang\n\n"
        f"#TheRidersGang #RidingCulture"
    )
    tweets.append(cta)

    # Format as numbered thread
    lines = []
    for i, tweet in enumerate(tweets, 1):
        lines.append(f"--- Tweet {i}/{len(tweets)} ---")
        lines.append(tweet)
        lines.append("")

    return "\n".join(lines)


def generate_card_html(meta, date_str):
    """Generate a visually branded Twitter card HTML (1200x675)."""
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %-d, %Y")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1200">
<title>Twitter Card — {meta['title']}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Source+Sans+3:wght@300;400;600;700&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    width: 1200px;
    height: 675px;
    overflow: hidden;
    font-family: 'Source Sans 3', sans-serif;
  }}

  .card {{
    width: 1200px;
    height: 675px;
    position: relative;
    overflow: hidden;
    display: flex;
  }}

  .card__image-half {{
    width: 55%;
    height: 100%;
    position: relative;
    overflow: hidden;
  }}

  .card__image {{
    width: 100%;
    height: 100%;
    object-fit: cover;
  }}

  .card__image-fade {{
    position: absolute;
    top: 0;
    right: 0;
    width: 120px;
    height: 100%;
    background: linear-gradient(to right, transparent, #1a1a2e);
  }}

  .card__content-half {{
    width: 45%;
    height: 100%;
    background: #1a1a2e;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 50px 50px 50px 30px;
    position: relative;
  }}

  .card__accent-line {{
    position: absolute;
    top: 50px;
    left: 0;
    width: 4px;
    height: 80px;
    background: #c9a96e;
  }}

  .card__category {{
    font-family: 'Source Sans 3', sans-serif;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #c9a96e;
    margin-bottom: 18px;
  }}

  .card__title {{
    font-family: 'Playfair Display', serif;
    font-size: 36px;
    font-weight: 700;
    line-height: 1.2;
    color: #ffffff;
    margin-bottom: 18px;
  }}

  .card__description {{
    font-family: 'Source Sans 3', sans-serif;
    font-size: 17px;
    font-weight: 300;
    line-height: 1.55;
    color: rgba(255, 255, 255, 0.75);
    margin-bottom: 30px;
  }}

  .card__footer {{
    display: flex;
    align-items: center;
    gap: 20px;
    border-top: 1px solid rgba(201, 169, 110, 0.3);
    padding-top: 18px;
  }}

  .card__brand {{
    font-family: 'Playfair Display', serif;
    font-size: 16px;
    font-weight: 700;
    color: #c9a96e;
  }}

  .card__date {{
    font-size: 14px;
    color: rgba(255, 255, 255, 0.5);
  }}

  .card__read-time {{
    font-size: 14px;
    color: rgba(255, 255, 255, 0.5);
    margin-left: auto;
  }}
</style>
</head>
<body>
  <div class="card">
    <div class="card__image-half">
      <img class="card__image" src="{meta['hero_src']}" alt="{meta['hero_alt']}">
      <div class="card__image-fade"></div>
    </div>
    <div class="card__content-half">
      <div class="card__accent-line"></div>
      <span class="card__category">{meta['category']}</span>
      <h1 class="card__title">{meta['title']}</h1>
      <p class="card__description">{meta['og_description']}</p>
      <div class="card__footer">
        <span class="card__brand">The Rider's Gang</span>
        <span class="card__date">{formatted_date}</span>
        <span class="card__read-time">{meta['read_time']}</span>
      </div>
    </div>
  </div>
</body>
</html>"""


def slugify(title):
    """Convert title to a URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:80]


def generate_twitter_posts(date_str, article_files):
    """Generate Twitter posts for the given articles.

    Returns list of dicts with keys: card_html_path, thread_path, title.
    """
    date_dir = os.path.join(SOCIAL_DIR, date_str)
    os.makedirs(date_dir, exist_ok=True)

    results = []

    for filepath in article_files:
        full_path = os.path.join(BASE_DIR, filepath)
        if not os.path.isfile(full_path):
            print(f"ERROR: Article not found: {full_path}", file=sys.stderr)
            sys.exit(1)

        meta = read_article_metadata(full_path)
        slug = slugify(meta["title"])

        # Generate card HTML
        card_html = generate_card_html(meta, date_str)
        card_path = os.path.join(date_dir, f"{slug}-card.html")
        with open(card_path, "w", encoding="utf-8") as f:
            f.write(card_html)

        # Generate thread text
        thread = generate_thread_text(meta)
        thread_path = os.path.join(date_dir, f"{slug}-thread.txt")
        with open(thread_path, "w", encoding="utf-8") as f:
            f.write(thread)

        results.append({
            "card_html_path": card_path,
            "thread_path": thread_path,
            "title": meta["title"],
        })

        print(f"  Twitter card: {os.path.relpath(card_path, BASE_DIR)}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Twitter/X posts")
    parser.add_argument("--date", required=True, help="Publication date (YYYY-MM-DD)")
    parser.add_argument("--articles", nargs="+", required=True, help="Article file paths")
    args = parser.parse_args()

    posts = generate_twitter_posts(args.date, args.articles)
    print(f"\nGenerated {len(posts)} Twitter posts for {args.date}")
