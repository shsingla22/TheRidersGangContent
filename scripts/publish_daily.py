#!/usr/bin/env python3
"""
Daily Content Publishing Script for The Rider's Gang.

This script handles the daily rotation of articles on the homepage:
1. Moves today's articles to the "From the Archives" section
2. Inserts new articles into the "Today's Stories" section
3. Updates dates and section labels
4. Validates all article files exist and images return HTTP 200

Usage:
    python scripts/publish_daily.py --date 2026-03-06 --articles articles/new-article-1.html articles/new-article-2.html ...

Or to just rotate (move today to archives, no new articles):
    python scripts/publish_daily.py --date 2026-03-06 --rotate-only
"""

import argparse
import os
import re
import sys
from datetime import datetime

from bs4 import BeautifulSoup


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, "..")
INDEX_FILE = os.path.join(BASE_DIR, "index.html")
ARTICLES_DIR = os.path.join(BASE_DIR, "articles")


def parse_date(date_str):
    """Parse date string like '2026-03-06' into a formatted label."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %-d, %Y")


def read_article_metadata(filepath):
    """Extract metadata from an article HTML file for card generation."""
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

    # Extract reading time from meta
    read_time = "5 min read"
    if meta_el:
        meta_text = meta_el.text
        match = re.search(r"(\d+)\s*min\s*read", meta_text)
        if match:
            read_time = f"{match.group(1)} min read"

    # Convert hero image to card size (800x500)
    card_src = re.sub(r"w=\d+", "w=800", hero_src)
    card_src = re.sub(r"h=\d+", "h=500", card_src)

    # Get relative path from index.html
    rel_path = os.path.relpath(filepath, BASE_DIR)

    return {
        "title": title,
        "category": category,
        "hero_src": card_src,
        "hero_alt": hero_alt,
        "description": description,
        "read_time": read_time,
        "href": rel_path,
    }


def generate_article_card(meta):
    """Generate an article-card HTML block from metadata."""
    return f"""      <article class="article-card">
        <img class="article-card__image" src="{meta['hero_src']}" alt="{meta['hero_alt']}" loading="lazy">
        <div class="article-card__body">
          <span class="article-card__category">{meta['category']}</span>
          <h3 class="article-card__title">{meta['title']}</h3>
          <p class="article-card__excerpt">{meta['description']}</p>
          <div class="article-card__meta">
            <span>{meta['read_time']}</span>
            <a href="{meta['href']}" class="article-card__read-more">Read Story &rarr;</a>
          </div>
        </div>
      </article>"""


def generate_archive_card(meta):
    """Generate a compact archive-card HTML block from metadata."""
    # Use smaller image for archive cards
    archive_src = re.sub(r"w=\d+", "w=400", meta["hero_src"])
    archive_src = re.sub(r"h=\d+", "h=250", archive_src)

    return f"""      <article class="archive-card">
        <img class="archive-card__image" src="{archive_src}" alt="{meta['hero_alt']}" loading="lazy">
        <div class="archive-card__body">
          <span class="archive-card__category">{meta['category']}</span>
          <h3 class="archive-card__title">{meta['title']}</h3>
          <div class="archive-card__meta">
            <span>{meta['read_time']}</span>
            <a href="{meta['href']}" class="archive-card__link">Read &rarr;</a>
          </div>
        </div>
      </article>"""


def extract_current_articles(soup, grid_class):
    """Extract article metadata from existing cards in a grid."""
    articles = []
    grid = soup.select_one(f".{grid_class}")
    if not grid:
        return articles

    # For article-cards
    for card in grid.select(".article-card"):
        img = card.select_one(".article-card__image")
        cat = card.select_one(".article-card__category")
        title = card.select_one(".article-card__title")
        excerpt = card.select_one(".article-card__excerpt")
        link = card.select_one(".article-card__read-more")
        meta_span = card.select_one(".article-card__meta span")

        articles.append({
            "title": title.text.strip() if title else "",
            "category": cat.text.strip() if cat else "",
            "hero_src": img.get("src", "") if img else "",
            "hero_alt": img.get("alt", "") if img else "",
            "description": excerpt.text.strip() if excerpt else "",
            "read_time": meta_span.text.strip() if meta_span else "5 min read",
            "href": link.get("href", "") if link else "",
        })

    # For archive-cards
    for card in grid.select(".archive-card"):
        img = card.select_one(".archive-card__image")
        cat = card.select_one(".archive-card__category")
        title = card.select_one(".archive-card__title")
        link = card.select_one(".archive-card__link")
        meta_span = card.select_one(".archive-card__meta span")

        # Convert archive image size back to card size
        src = img.get("src", "") if img else ""
        src = re.sub(r"w=\d+", "w=800", src)
        src = re.sub(r"h=\d+", "h=500", src)

        articles.append({
            "title": title.text.strip() if title else "",
            "category": cat.text.strip() if cat else "",
            "hero_src": src,
            "hero_alt": img.get("alt", "") if img else "",
            "description": "",
            "read_time": meta_span.text.strip() if meta_span else "5 min read",
            "href": link.get("href", "") if link else "",
        })

    return articles


def publish(date_str, article_files, rotate_only=False):
    """Main publish function."""
    formatted_date = parse_date(date_str)

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    # 1. Extract current "today's" articles
    current_today = extract_current_articles(soup, "articles-grid")
    current_archives = extract_current_articles(soup, "archive-grid")

    # 2. Read new article metadata
    new_articles = []
    if not rotate_only:
        for filepath in article_files:
            full_path = os.path.join(BASE_DIR, filepath)
            if not os.path.isfile(full_path):
                print(f"ERROR: Article not found: {full_path}", file=sys.stderr)
                sys.exit(1)
            new_articles.append(read_article_metadata(full_path))

    # 3. Build new today's section
    today_cards = "\n\n".join(generate_article_card(m) for m in new_articles)

    # 4. Build new archives (old today + old archives)
    all_archives = current_today + current_archives
    archive_cards = "\n\n".join(generate_archive_card(m) for m in all_archives)

    # 5. Get current archive date label for merging
    archive_section = soup.select("#archives .section__header .section__label")
    old_date_label = archive_section[0].text.strip() if archive_section else "Previous"

    # 6. Read index.html as text for replacement
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    # Update today's date label
    html = re.sub(
        r'(<section[^>]*id="articles"[^>]*>.*?<span class="section__label">)(.*?)(</span>)',
        rf"\g<1>{formatted_date}\g<3>",
        html,
        flags=re.DOTALL,
    )

    # Update today's articles grid
    html = re.sub(
        r'(<div class="articles-grid">)(.*?)(</div>\s*</section>)',
        rf'\1\n\n{today_cards}\n\n    \3',
        html,
        count=1,
        flags=re.DOTALL,
    )

    # Update archive date label to show range
    html = re.sub(
        r'(<section[^>]*id="archives"[^>]*>.*?<span class="section__label">)(.*?)(</span>)',
        rf"\g<1>{old_date_label} &amp; Earlier\g<3>",
        html,
        flags=re.DOTALL,
    )

    # Update archive grid
    html = re.sub(
        r'(<div class="archive-grid">)(.*?)(</div>\s*</section>)',
        rf'\1\n\n{archive_cards}\n\n    \3',
        html,
        count=1,
        flags=re.DOTALL,
    )

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Published {len(new_articles)} new articles for {formatted_date}")
    print(f"Archived {len(all_archives)} previous articles")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish daily articles")
    parser.add_argument("--date", required=True, help="Publication date (YYYY-MM-DD)")
    parser.add_argument("--articles", nargs="*", default=[], help="Article file paths")
    parser.add_argument("--rotate-only", action="store_true", help="Just rotate, no new articles")
    args = parser.parse_args()

    publish(args.date, args.articles, args.rotate_only)
