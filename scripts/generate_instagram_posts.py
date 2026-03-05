#!/usr/bin/env python3
"""
Instagram Post Generator for The Rider's Gang.

Reads article HTML files, extracts metadata (title, category, description,
hero image, reading time), and generates visually branded Instagram post
HTML files (1080x1080) plus companion caption/hashtag text files.

Posts are saved under social-media/instagram/<date>/ and are NOT linked
from the website.

Usage:
    python scripts/generate_instagram_posts.py --date 2026-03-06 \
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
SOCIAL_DIR = os.path.join(BASE_DIR, "social-media", "instagram")
SITE_URL = "https://theridersgangcontent.com"


# Category-to-hashtag mapping for consistent tagging
CATEGORY_HASHTAGS = {
    "Equestrian Heritage": "#Equestrian #EquestrianHeritage #HorseRiding #HorseCulture",
    "Motorcycle Culture": "#MotorcycleCulture #CafeRacer #BikerLife #RidersOfInstagram",
    "Fashion Heritage": "#FashionHeritage #QuietLuxury #MensFashion #TimelessStyle",
    "Adventure Riding": "#AdventureRiding #MotoTravel #RideToLive #ExploreMore",
    "Style & Craft": "#StyleAndCraft #Craftsmanship #LeatherGoods #Handmade",
}

BASE_HASHTAGS = "#TheRidersGang #RidingCulture #BornInTheSaddle #RiderStyle"


def read_article_metadata(filepath):
    """Extract metadata from an article HTML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    title_el = soup.select_one(".article__title")
    category_el = soup.select_one(".article__category")
    hero_el = soup.select_one(".article__hero-image")
    meta_el = soup.select_one(".article__meta")
    desc_el = soup.find("meta", attrs={"name": "description"})

    title = title_el.text.strip() if title_el else "Untitled"
    category = category_el.text.strip() if category_el else "Uncategorized"
    hero_src = hero_el.get("src", "") if hero_el else ""
    hero_alt = hero_el.get("alt", title) if hero_el else title
    description = desc_el.get("content", "").strip() if desc_el else ""

    read_time = "5 min read"
    if meta_el:
        meta_text = meta_el.text
        match = re.search(r"(\d+)\s*min\s*read", meta_text)
        if match:
            read_time = f"{match.group(1)} min read"

    # Use high-res square crop for Instagram (1080x1080)
    insta_src = re.sub(r"w=\d+", "w=1080", hero_src)
    insta_src = re.sub(r"h=\d+", "h=1080", insta_src)

    # Extract h2 headings for summary
    headings = [h2.get_text(strip=True) for h2 in soup.select("h2")]

    # Build article URL
    rel_path = os.path.relpath(filepath, BASE_DIR)
    article_url = f"{SITE_URL}/{rel_path}"

    return {
        "title": title,
        "category": category,
        "hero_src": insta_src,
        "hero_alt": hero_alt,
        "description": description,
        "read_time": read_time,
        "href": rel_path,
        "headings": headings,
        "article_url": article_url,
    }


def generate_summary(headings):
    """Build a summary section from article h2 headings."""
    if not headings:
        return ""
    lines = ["What's inside:"]
    for h in headings[:5]:
        lines.append(f"  \u2022 {h}")
    return "\n".join(lines)


def generate_caption(meta):
    """Generate Instagram caption text with summary, link, and hashtags."""
    category_tags = CATEGORY_HASHTAGS.get(meta["category"], "#Riding #Heritage")
    summary = generate_summary(meta.get("headings", []))
    parts = [meta["description"]]
    if summary:
        parts.append(summary)
    parts.append(f"Read the full story:\n{meta['article_url']}")
    parts.append(f"{BASE_HASHTAGS} {category_tags}")
    return "\n\n".join(parts)


def _build_summary_html(headings):
    """Build HTML summary bullet points from article headings."""
    if not headings:
        return ""
    items = "\n".join(
        f'        <div class="post__summary-item">\u2022 {h}</div>'
        for h in headings[:5]
    )
    return f"""      <div class="post__summary">
        <div class="post__summary-label">What's Inside</div>
{items}
      </div>"""


def generate_post_html(meta, date_str):
    """Generate a visually branded 1080x1080 Instagram post as an HTML file."""
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %-d, %Y")
    summary_html = _build_summary_html(meta.get("headings", []))
    link_html = f'      <span class="post__link">{meta["article_url"]}</span>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080">
<title>Instagram Post — {meta['title']}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Source+Sans+3:wght@300;400;600;700&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    width: 1080px;
    height: 1080px;
    overflow: hidden;
    font-family: 'Source Sans 3', sans-serif;
    position: relative;
  }}

  .post {{
    width: 1080px;
    height: 1080px;
    position: relative;
    overflow: hidden;
  }}

  .post__image {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }}

  .post__overlay {{
    position: absolute;
    inset: 0;
    background: linear-gradient(
      to top,
      rgba(26, 26, 46, 0.95) 0%,
      rgba(26, 26, 46, 0.75) 35%,
      rgba(26, 26, 46, 0.15) 60%,
      rgba(26, 26, 46, 0.05) 100%
    );
  }}

  .post__content {{
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 60px;
    color: #fff;
  }}

  .post__category {{
    display: inline-block;
    font-family: 'Source Sans 3', sans-serif;
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #c9a96e;
    margin-bottom: 20px;
    border-bottom: 2px solid #c9a96e;
    padding-bottom: 8px;
  }}

  .post__title {{
    font-family: 'Playfair Display', serif;
    font-size: 52px;
    font-weight: 700;
    line-height: 1.15;
    color: #ffffff;
    margin-bottom: 20px;
    max-width: 900px;
  }}

  .post__description {{
    font-family: 'Source Sans 3', sans-serif;
    font-size: 22px;
    font-weight: 300;
    line-height: 1.5;
    color: rgba(255, 255, 255, 0.85);
    margin-bottom: 30px;
    max-width: 850px;
  }}

  .post__summary {{
    font-family: 'Source Sans 3', sans-serif;
    font-size: 17px;
    font-weight: 400;
    line-height: 1.6;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 20px;
    padding: 14px 18px;
    border-left: 3px solid #c9a96e;
    background: rgba(201, 169, 110, 0.08);
  }}

  .post__summary-label {{
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #c9a96e;
    margin-bottom: 8px;
  }}

  .post__summary-item {{
    margin: 4px 0;
  }}

  .post__link {{
    display: inline-block;
    font-family: 'Source Sans 3', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: #c9a96e;
    margin-bottom: 16px;
    letter-spacing: 0.5px;
  }}

  .post__footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(201, 169, 110, 0.4);
    padding-top: 20px;
  }}

  .post__brand {{
    font-family: 'Playfair Display', serif;
    font-size: 20px;
    font-weight: 700;
    color: #c9a96e;
    letter-spacing: 1px;
  }}

  .post__date {{
    font-family: 'Source Sans 3', sans-serif;
    font-size: 16px;
    color: rgba(255, 255, 255, 0.6);
    letter-spacing: 1px;
  }}

  .post__read-time {{
    font-family: 'Source Sans 3', sans-serif;
    font-size: 16px;
    color: rgba(255, 255, 255, 0.6);
  }}

  .post__corner-accent {{
    position: absolute;
    top: 40px;
    right: 40px;
    width: 60px;
    height: 60px;
    border-top: 3px solid #c9a96e;
    border-right: 3px solid #c9a96e;
  }}

  .post__corner-accent--bottom {{
    top: auto;
    right: auto;
    bottom: 40px;
    left: 40px;
    border-top: none;
    border-right: none;
    border-bottom: 3px solid #c9a96e;
    border-left: 3px solid #c9a96e;
  }}
</style>
</head>
<body>
  <div class="post">
    <img class="post__image" src="{meta['hero_src']}" alt="{meta['hero_alt']}">
    <div class="post__overlay"></div>
    <div class="post__corner-accent"></div>
    <div class="post__corner-accent post__corner-accent--bottom"></div>
    <div class="post__content">
      <span class="post__category">{meta['category']}</span>
      <h1 class="post__title">{meta['title']}</h1>
      <p class="post__description">{meta['description']}</p>
{summary_html}
{link_html}
      <div class="post__footer">
        <span class="post__brand">The Rider's Gang</span>
        <span class="post__date">{formatted_date}</span>
        <span class="post__read-time">{meta['read_time']}</span>
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


def generate_instagram_posts(date_str, article_files):
    """Generate Instagram posts for the given articles.

    Returns list of dicts with keys: post_html_path, caption_path, title.
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

        # Generate post HTML
        post_html = generate_post_html(meta, date_str)
        post_path = os.path.join(date_dir, f"{slug}.html")
        with open(post_path, "w", encoding="utf-8") as f:
            f.write(post_html)

        # Generate caption text
        caption = generate_caption(meta)
        caption_path = os.path.join(date_dir, f"{slug}-caption.txt")
        with open(caption_path, "w", encoding="utf-8") as f:
            f.write(caption)

        results.append({
            "post_html_path": post_path,
            "caption_path": caption_path,
            "title": meta["title"],
        })

        print(f"  Instagram post: {os.path.relpath(post_path, BASE_DIR)}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Instagram posts")
    parser.add_argument("--date", required=True, help="Publication date (YYYY-MM-DD)")
    parser.add_argument("--articles", nargs="+", required=True, help="Article file paths")
    args = parser.parse_args()

    posts = generate_instagram_posts(args.date, args.articles)
    print(f"\nGenerated {len(posts)} Instagram posts for {args.date}")
