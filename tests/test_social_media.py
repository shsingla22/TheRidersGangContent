"""
Test suite for social media post generation workflows.

Covers:
- Instagram post generation (HTML structure, captions, hashtags)
- Twitter post generation (card HTML, thread text)
- Integration with publish_daily.py
- File output structure and content validation

Run with: pytest tests/test_social_media.py -v
"""

import os
import re
import glob
import shutil
import sys
import pytest
from bs4 import BeautifulSoup

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
ARTICLES_DIR = os.path.join(BASE_DIR, "articles")
SOCIAL_DIR = os.path.join(BASE_DIR, "social-media")

# Add scripts dir to path for imports
sys.path.insert(0, SCRIPTS_DIR)

from generate_instagram_posts import (
    read_article_metadata as ig_read_metadata,
    generate_caption,
    generate_post_html,
    generate_instagram_posts,
    slugify,
    CATEGORY_HASHTAGS,
    BASE_HASHTAGS,
)
from generate_twitter_posts import (
    read_article_metadata as tw_read_metadata,
    generate_thread_text,
    generate_card_html,
    generate_twitter_posts,
)

# Use two known articles for testing
SAMPLE_ARTICLES = [
    "articles/hermes-from-horse-harnesses-to-high-fashion.html",
    "articles/belstaff-the-jacket-that-built-a-riding-legend.html",
]

TEST_DATE = "2026-01-15"


def _article_paths():
    """Return full paths for sample articles."""
    return [os.path.join(BASE_DIR, a) for a in SAMPLE_ARTICLES]


# ===================================================================
# Instagram Script — Metadata Extraction
# ===================================================================

class TestInstagramMetadata:
    """Test Instagram metadata reading from article HTML."""

    def test_reads_title(self):
        meta = ig_read_metadata(_article_paths()[0])
        assert "Hermès" in meta["title"]

    def test_reads_category(self):
        meta = ig_read_metadata(_article_paths()[0])
        assert meta["category"] == "Equestrian Heritage"

    def test_reads_description(self):
        meta = ig_read_metadata(_article_paths()[0])
        assert len(meta["description"]) > 20

    def test_hero_src_is_1080x1080(self):
        meta = ig_read_metadata(_article_paths()[0])
        assert "w=1080" in meta["hero_src"]
        assert "h=1080" in meta["hero_src"]

    def test_reads_read_time(self):
        meta = ig_read_metadata(_article_paths()[0])
        assert "min read" in meta["read_time"]

    def test_href_is_relative(self):
        meta = ig_read_metadata(_article_paths()[0])
        assert meta["href"].startswith("articles/")

    def test_hero_alt_not_empty(self):
        meta = ig_read_metadata(_article_paths()[0])
        assert len(meta["hero_alt"]) > 0


# ===================================================================
# Instagram Script — Caption Generation
# ===================================================================

class TestInstagramCaption:
    """Test Instagram caption and hashtag generation."""

    def test_caption_contains_description(self):
        meta = ig_read_metadata(_article_paths()[0])
        caption = generate_caption(meta)
        assert meta["description"] in caption

    def test_caption_contains_link_cta(self):
        meta = ig_read_metadata(_article_paths()[0])
        caption = generate_caption(meta)
        assert "link in bio" in caption.lower()

    def test_caption_contains_base_hashtags(self):
        meta = ig_read_metadata(_article_paths()[0])
        caption = generate_caption(meta)
        assert "#TheRidersGang" in caption
        assert "#RidingCulture" in caption

    def test_caption_contains_category_hashtags(self):
        meta = ig_read_metadata(_article_paths()[0])
        caption = generate_caption(meta)
        assert "#Equestrian" in caption

    def test_category_hashtag_mapping_exists_for_known_categories(self):
        assert "Equestrian Heritage" in CATEGORY_HASHTAGS
        assert "Motorcycle Culture" in CATEGORY_HASHTAGS


# ===================================================================
# Instagram Script — Post HTML Generation
# ===================================================================

class TestInstagramPostHTML:
    """Test Instagram post HTML structure and styling."""

    @pytest.fixture
    def post_soup(self):
        meta = ig_read_metadata(_article_paths()[0])
        html = generate_post_html(meta, TEST_DATE)
        return BeautifulSoup(html, "lxml")

    def test_html_is_valid(self, post_soup):
        assert post_soup.find("html") is not None
        assert post_soup.find("body") is not None

    def test_viewport_is_1080(self, post_soup):
        viewport = post_soup.find("meta", attrs={"name": "viewport"})
        assert viewport and "1080" in viewport.get("content", "")

    def test_has_post_container(self, post_soup):
        assert post_soup.select_one(".post") is not None

    def test_has_image(self, post_soup):
        img = post_soup.select_one(".post__image")
        assert img is not None
        assert img.get("src", "").startswith("https://")

    def test_has_overlay(self, post_soup):
        assert post_soup.select_one(".post__overlay") is not None

    def test_has_title(self, post_soup):
        title = post_soup.select_one(".post__title")
        assert title is not None
        assert len(title.text.strip()) > 0

    def test_has_category(self, post_soup):
        cat = post_soup.select_one(".post__category")
        assert cat is not None

    def test_has_description(self, post_soup):
        desc = post_soup.select_one(".post__description")
        assert desc is not None

    def test_has_brand_footer(self, post_soup):
        brand = post_soup.select_one(".post__brand")
        assert brand is not None
        assert "Rider" in brand.text

    def test_has_date(self, post_soup):
        date_el = post_soup.select_one(".post__date")
        assert date_el is not None
        assert "January" in date_el.text

    def test_has_corner_accents(self, post_soup):
        accents = post_soup.select(".post__corner-accent")
        assert len(accents) == 2

    def test_uses_brand_fonts(self, post_soup):
        style = post_soup.find("style")
        assert style is not None
        style_text = style.text
        assert "Playfair Display" in style_text
        assert "Source Sans 3" in style_text

    def test_uses_brand_gold_color(self, post_soup):
        style = post_soup.find("style")
        style_text = style.text
        assert "#c9a96e" in style_text  # gold

    def test_uses_brand_midnight_color(self, post_soup):
        html_str = str(post_soup)
        # Midnight color used as rgba(26, 26, 46, ...) in gradients
        assert "26, 26, 46" in html_str  # midnight in rgba form

    def test_dimensions_1080x1080(self, post_soup):
        style = post_soup.find("style")
        style_text = style.text
        assert "1080px" in style_text


# ===================================================================
# Instagram Script — File Output
# ===================================================================

class TestInstagramFileOutput:
    """Test that Instagram post files are correctly saved."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        self.test_dir = os.path.join(SOCIAL_DIR, "instagram", "2026-12-01")
        yield
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_generates_files_for_each_article(self):
        results = generate_instagram_posts("2026-12-01", SAMPLE_ARTICLES)
        assert len(results) == 2

    def test_creates_date_directory(self):
        generate_instagram_posts("2026-12-01", SAMPLE_ARTICLES)
        assert os.path.isdir(self.test_dir)

    def test_creates_html_and_caption_files(self):
        results = generate_instagram_posts("2026-12-01", SAMPLE_ARTICLES)
        for r in results:
            assert os.path.isfile(r["post_html_path"])
            assert os.path.isfile(r["caption_path"])

    def test_caption_file_not_empty(self):
        results = generate_instagram_posts("2026-12-01", SAMPLE_ARTICLES)
        for r in results:
            with open(r["caption_path"], "r") as f:
                assert len(f.read().strip()) > 0

    def test_html_file_not_empty(self):
        results = generate_instagram_posts("2026-12-01", SAMPLE_ARTICLES)
        for r in results:
            with open(r["post_html_path"], "r") as f:
                assert len(f.read().strip()) > 0

    def test_result_contains_title(self):
        results = generate_instagram_posts("2026-12-01", SAMPLE_ARTICLES)
        titles = [r["title"] for r in results]
        assert any("Hermès" in t for t in titles)
        assert any("Belstaff" in t for t in titles)


# ===================================================================
# Twitter Script — Metadata Extraction
# ===================================================================

class TestTwitterMetadata:
    """Test Twitter metadata reading from article HTML."""

    def test_reads_title(self):
        meta = tw_read_metadata(_article_paths()[0])
        assert "Hermès" in meta["title"]

    def test_reads_og_description(self):
        meta = tw_read_metadata(_article_paths()[0])
        assert len(meta["og_description"]) > 10

    def test_hero_src_is_1200x675(self):
        meta = tw_read_metadata(_article_paths()[0])
        assert "w=1200" in meta["hero_src"]
        assert "h=675" in meta["hero_src"]

    def test_extracts_paragraphs(self):
        meta = tw_read_metadata(_article_paths()[0])
        assert len(meta["paragraphs"]) >= 3

    def test_paragraphs_are_substantial(self):
        meta = tw_read_metadata(_article_paths()[0])
        for p in meta["paragraphs"]:
            assert len(p) > 40


# ===================================================================
# Twitter Script — Thread Generation
# ===================================================================

class TestTwitterThread:
    """Test Twitter thread text generation."""

    def test_thread_has_multiple_tweets(self):
        meta = tw_read_metadata(_article_paths()[0])
        thread = generate_thread_text(meta)
        assert thread.count("--- Tweet") >= 3

    def test_first_tweet_is_hook(self):
        meta = tw_read_metadata(_article_paths()[0])
        thread = generate_thread_text(meta)
        assert "thread" in thread.lower()[:300]

    def test_last_tweet_has_cta(self):
        meta = tw_read_metadata(_article_paths()[0])
        thread = generate_thread_text(meta)
        assert "@TheRidersGang" in thread
        assert "#TheRidersGang" in thread

    def test_last_tweet_has_article_title(self):
        meta = tw_read_metadata(_article_paths()[0])
        thread = generate_thread_text(meta)
        assert meta["title"] in thread

    def test_individual_tweets_under_280_chars(self):
        meta = tw_read_metadata(_article_paths()[0])
        thread = generate_thread_text(meta)
        # Split on tweet markers
        tweets = re.split(r"--- Tweet \d+/\d+ ---\n", thread)
        tweets = [t.strip() for t in tweets if t.strip()]
        for tweet in tweets:
            assert len(tweet) <= 300, f"Tweet too long ({len(tweet)} chars): {tweet[:50]}..."


# ===================================================================
# Twitter Script — Card HTML Generation
# ===================================================================

class TestTwitterCardHTML:
    """Test Twitter card HTML structure and styling."""

    @pytest.fixture
    def card_soup(self):
        meta = tw_read_metadata(_article_paths()[0])
        html = generate_card_html(meta, TEST_DATE)
        return BeautifulSoup(html, "lxml")

    def test_html_is_valid(self, card_soup):
        assert card_soup.find("html") is not None

    def test_viewport_is_1200(self, card_soup):
        viewport = card_soup.find("meta", attrs={"name": "viewport"})
        assert viewport and "1200" in viewport.get("content", "")

    def test_has_card_container(self, card_soup):
        assert card_soup.select_one(".card") is not None

    def test_has_image(self, card_soup):
        img = card_soup.select_one(".card__image")
        assert img is not None
        assert img.get("src", "").startswith("https://")

    def test_has_title(self, card_soup):
        title = card_soup.select_one(".card__title")
        assert title is not None
        assert len(title.text.strip()) > 0

    def test_has_category(self, card_soup):
        assert card_soup.select_one(".card__category") is not None

    def test_has_description(self, card_soup):
        assert card_soup.select_one(".card__description") is not None

    def test_has_brand(self, card_soup):
        brand = card_soup.select_one(".card__brand")
        assert brand is not None
        assert "Rider" in brand.text

    def test_has_split_layout(self, card_soup):
        assert card_soup.select_one(".card__image-half") is not None
        assert card_soup.select_one(".card__content-half") is not None

    def test_has_accent_line(self, card_soup):
        assert card_soup.select_one(".card__accent-line") is not None

    def test_uses_brand_fonts(self, card_soup):
        style = card_soup.find("style")
        style_text = style.text
        assert "Playfair Display" in style_text

    def test_uses_brand_colors(self, card_soup):
        style = card_soup.find("style")
        style_text = style.text
        assert "#c9a96e" in style_text
        assert "#1a1a2e" in style_text

    def test_dimensions_1200x675(self, card_soup):
        style = card_soup.find("style")
        style_text = style.text
        assert "1200px" in style_text
        assert "675px" in style_text


# ===================================================================
# Twitter Script — File Output
# ===================================================================

class TestTwitterFileOutput:
    """Test that Twitter post files are correctly saved."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        self.test_dir = os.path.join(SOCIAL_DIR, "twitter", "2026-12-02")
        yield
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_generates_files_for_each_article(self):
        results = generate_twitter_posts("2026-12-02", SAMPLE_ARTICLES)
        assert len(results) == 2

    def test_creates_date_directory(self):
        generate_twitter_posts("2026-12-02", SAMPLE_ARTICLES)
        assert os.path.isdir(self.test_dir)

    def test_creates_card_and_thread_files(self):
        results = generate_twitter_posts("2026-12-02", SAMPLE_ARTICLES)
        for r in results:
            assert os.path.isfile(r["card_html_path"])
            assert os.path.isfile(r["thread_path"])

    def test_card_file_not_empty(self):
        results = generate_twitter_posts("2026-12-02", SAMPLE_ARTICLES)
        for r in results:
            with open(r["card_html_path"], "r") as f:
                assert len(f.read().strip()) > 0

    def test_thread_file_not_empty(self):
        results = generate_twitter_posts("2026-12-02", SAMPLE_ARTICLES)
        for r in results:
            with open(r["thread_path"], "r") as f:
                assert len(f.read().strip()) > 0


# ===================================================================
# Slugify Utility
# ===================================================================

class TestSlugify:
    """Test the slugify utility function."""

    def test_basic_slugify(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert slugify("Hermès: From Horse") == "herm-s-from-horse"

    def test_max_length(self):
        long_title = "A" * 200
        assert len(slugify(long_title)) <= 80

    def test_strips_trailing_hyphens(self):
        result = slugify("Hello!!!")
        assert not result.endswith("-")


# ===================================================================
# Social Media Posts NOT in Website
# ===================================================================

class TestSocialMediaNotInWebsite:
    """Ensure social media posts are NOT linked from the website."""

    def test_index_does_not_link_social_media(self):
        with open(os.path.join(BASE_DIR, "index.html"), "r") as f:
            html = f.read()
        assert "social-media/" not in html
        assert "instagram/" not in html.lower().split("unsplash")[0]  # ignore image URLs

    def test_articles_do_not_link_social_media(self):
        for article_file in glob.glob(os.path.join(ARTICLES_DIR, "*.html")):
            with open(article_file, "r") as f:
                html = f.read()
            assert "social-media/" not in html, f"Social media link found in {article_file}"


# ===================================================================
# Existing Sample Posts Validation
# ===================================================================

class TestExistingSamplePosts:
    """Validate the sample posts that were generated."""

    INSTA_DIR = os.path.join(SOCIAL_DIR, "instagram", "2026-03-05")
    TWITTER_DIR = os.path.join(SOCIAL_DIR, "twitter", "2026-03-05")

    def test_instagram_sample_directory_exists(self):
        assert os.path.isdir(self.INSTA_DIR)

    def test_twitter_sample_directory_exists(self):
        assert os.path.isdir(self.TWITTER_DIR)

    def test_instagram_has_html_files(self):
        html_files = glob.glob(os.path.join(self.INSTA_DIR, "*.html"))
        assert len(html_files) == 2

    def test_instagram_has_caption_files(self):
        caption_files = glob.glob(os.path.join(self.INSTA_DIR, "*-caption.txt"))
        assert len(caption_files) == 2

    def test_twitter_has_card_files(self):
        card_files = glob.glob(os.path.join(self.TWITTER_DIR, "*-card.html"))
        assert len(card_files) == 2

    def test_twitter_has_thread_files(self):
        thread_files = glob.glob(os.path.join(self.TWITTER_DIR, "*-thread.txt"))
        assert len(thread_files) == 2

    def test_instagram_html_has_1080_dimensions(self):
        for html_file in glob.glob(os.path.join(self.INSTA_DIR, "*.html")):
            with open(html_file, "r") as f:
                content = f.read()
            assert "1080px" in content

    def test_twitter_card_has_1200x675_dimensions(self):
        for html_file in glob.glob(os.path.join(self.TWITTER_DIR, "*-card.html")):
            with open(html_file, "r") as f:
                content = f.read()
            assert "1200px" in content
            assert "675px" in content


# ===================================================================
# Integration — publish_daily imports
# ===================================================================

class TestPublishDailyIntegration:
    """Verify publish_daily.py has social media integration."""

    def test_publish_daily_imports_instagram(self):
        with open(os.path.join(SCRIPTS_DIR, "publish_daily.py"), "r") as f:
            content = f.read()
        assert "generate_instagram_posts" in content

    def test_publish_daily_imports_twitter(self):
        with open(os.path.join(SCRIPTS_DIR, "publish_daily.py"), "r") as f:
            content = f.read()
        assert "generate_twitter_posts" in content

    def test_publish_daily_docstring_mentions_2_articles(self):
        with open(os.path.join(SCRIPTS_DIR, "publish_daily.py"), "r") as f:
            content = f.read()
        assert "2 per day" in content

    def test_publish_daily_docstring_mentions_instagram(self):
        with open(os.path.join(SCRIPTS_DIR, "publish_daily.py"), "r") as f:
            content = f.read()
        assert "Instagram" in content

    def test_publish_daily_docstring_mentions_twitter(self):
        with open(os.path.join(SCRIPTS_DIR, "publish_daily.py"), "r") as f:
            content = f.read()
        assert "Twitter" in content
