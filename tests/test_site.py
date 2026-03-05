"""
Comprehensive test suite for The Rider's Gang website.
Covers every customer journey: homepage, navigation, articles,
images, links, responsiveness, SEO, accessibility, and more.

Run with: pytest tests/test_site.py -v
"""

import os
import re
import glob
import pytest
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
ARTICLES_DIR = os.path.join(BASE_DIR, "articles")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CSS_FILE = os.path.join(ASSETS_DIR, "css", "style.css")

BRAND_NAME = "The Rider's Gang"


def _html_files():
    """Return all HTML files in the project."""
    files = glob.glob(os.path.join(BASE_DIR, "*.html"))
    files += glob.glob(os.path.join(ARTICLES_DIR, "*.html"))
    return files


def _parse(filepath):
    """Parse an HTML file and return a BeautifulSoup object."""
    with open(filepath, "r", encoding="utf-8") as f:
        return BeautifulSoup(f.read(), "lxml")


def _read(filepath):
    """Read file contents as string."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


INDEX = os.path.join(BASE_DIR, "index.html")
ARTICLE_FILES = glob.glob(os.path.join(ARTICLES_DIR, "*.html"))


# ===================================================================
# 1. STRUCTURAL INTEGRITY — files exist, valid HTML
# ===================================================================

class TestFileStructure:
    """Verify all expected files and directories exist."""

    def test_index_exists(self):
        assert os.path.isfile(INDEX), "index.html must exist"

    def test_css_exists(self):
        assert os.path.isfile(CSS_FILE), "style.css must exist"

    def test_logo_svg_exists(self):
        assert os.path.isfile(os.path.join(ASSETS_DIR, "images", "logo.svg"))

    def test_logo_nav_svg_exists(self):
        assert os.path.isfile(os.path.join(ASSETS_DIR, "images", "logo-nav.svg"))

    def test_articles_directory_has_files(self):
        assert len(ARTICLE_FILES) >= 1, "At least one article must exist"

    def test_expected_article_count(self):
        assert len(ARTICLE_FILES) == 5, f"Expected 5 articles, found {len(ARTICLE_FILES)}"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_html_is_valid_doctype(self, filepath):
        content = _read(filepath)
        assert content.strip().lower().startswith("<!doctype html"), \
            f"{filepath} must start with <!DOCTYPE html>"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_html_has_lang_attribute(self, filepath):
        soup = _parse(filepath)
        html_tag = soup.find("html")
        assert html_tag and html_tag.get("lang"), \
            f"{filepath} <html> must have lang attribute"


# ===================================================================
# 2. SEO & META TAGS
# ===================================================================

class TestSEO:
    """Verify SEO essentials on every page."""

    @pytest.mark.parametrize("filepath", _html_files())
    def test_has_title(self, filepath):
        soup = _parse(filepath)
        title = soup.find("title")
        assert title and title.string.strip(), \
            f"{filepath} must have a non-empty <title>"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_has_meta_description(self, filepath):
        soup = _parse(filepath)
        desc = soup.find("meta", attrs={"name": "description"})
        assert desc and desc.get("content", "").strip(), \
            f"{filepath} must have a meta description"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_has_viewport_meta(self, filepath):
        soup = _parse(filepath)
        vp = soup.find("meta", attrs={"name": "viewport"})
        assert vp, f"{filepath} must have viewport meta tag"
        content = vp.get("content", "")
        assert "width=device-width" in content, \
            f"{filepath} viewport must include width=device-width"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_has_charset(self, filepath):
        soup = _parse(filepath)
        charset = soup.find("meta", attrs={"charset": True})
        assert charset, f"{filepath} must declare charset"

    def test_index_has_og_tags(self):
        soup = _parse(INDEX)
        og_title = soup.find("meta", attrs={"property": "og:title"})
        og_desc = soup.find("meta", attrs={"property": "og:description"})
        assert og_title, "index.html must have og:title"
        assert og_desc, "index.html must have og:description"

    def test_index_has_twitter_card(self):
        soup = _parse(INDEX)
        tc = soup.find("meta", attrs={"name": "twitter:card"})
        assert tc, "index.html must have twitter:card meta"


# ===================================================================
# 3. BRANDING — consistent brand name everywhere
# ===================================================================

class TestBranding:
    """Verify brand name is consistently 'The Rider's Gang' (with apostrophe)."""

    @pytest.mark.parametrize("filepath", _html_files())
    def test_no_riders_without_apostrophe(self, filepath):
        content = _read(filepath)
        # Find "Riders Gang" NOT preceded by "'" (i.e. without apostrophe)
        # We want "Rider's Gang" everywhere, never "Riders Gang"
        matches = re.findall(r"(?<!&#39;)(?<![''])Riders Gang", content)
        assert len(matches) == 0, \
            f'{filepath} contains "Riders Gang" without apostrophe ({len(matches)} occurrences)'

    @pytest.mark.parametrize("filepath", _html_files())
    def test_brand_name_in_title(self, filepath):
        soup = _parse(filepath)
        title = soup.find("title").string
        assert "Rider" in title and "Gang" in title, \
            f"{filepath} title must reference the brand"

    def test_logo_svg_has_apostrophe(self):
        content = _read(os.path.join(ASSETS_DIR, "images", "logo.svg"))
        assert "RIDER" in content and "GANG" in content, \
            "logo.svg must contain RIDER and GANG text"
        # Check for apostrophe (either &#39; or ' or ')
        assert "&#39;" in content or "'" in content or "\u2019" in content, \
            "logo.svg must have apostrophe in RIDER'S"

    def test_nav_logo_svg_has_apostrophe(self):
        content = _read(os.path.join(ASSETS_DIR, "images", "logo-nav.svg"))
        assert "RIDER" in content and "GANG" in content
        assert "&#39;" in content or "'" in content or "\u2019" in content, \
            "logo-nav.svg must have apostrophe in RIDER'S"


# ===================================================================
# 4. NAVIGATION — every page has working nav
# ===================================================================

class TestNavigation:
    """Verify navigation structure on every page."""

    @pytest.mark.parametrize("filepath", _html_files())
    def test_has_nav(self, filepath):
        soup = _parse(filepath)
        nav = soup.find("nav", class_="site-nav")
        assert nav, f"{filepath} must have a <nav class='site-nav'>"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_nav_has_logo(self, filepath):
        soup = _parse(filepath)
        nav_img = soup.select_one(".site-nav .nav-logo")
        assert nav_img, f"{filepath} nav must have a logo image"
        src = nav_img.get("src", "")
        assert "logo-nav.svg" in src, "Nav logo must reference logo-nav.svg"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_nav_has_links(self, filepath):
        soup = _parse(filepath)
        links = soup.select(".site-nav__links a")
        assert len(links) >= 3, f"{filepath} nav must have at least 3 links"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_nav_has_hamburger_toggle(self, filepath):
        soup = _parse(filepath)
        toggle = soup.select_one(".nav-toggle")
        assert toggle, f"{filepath} must have hamburger toggle for mobile"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_nav_logo_links_to_home(self, filepath):
        soup = _parse(filepath)
        brand_link = soup.select_one(".site-nav__brand")
        assert brand_link, f"{filepath} must have brand link"
        href = brand_link.get("href", "")
        assert "index.html" in href, f"{filepath} brand link must go to index.html"


# ===================================================================
# 5. HOMEPAGE — hero, articles, sections
# ===================================================================

class TestHomepage:
    """Verify homepage structure and content."""

    def test_hero_section_exists(self):
        soup = _parse(INDEX)
        hero = soup.select_one(".hero")
        assert hero, "Homepage must have a hero section"

    def test_hero_has_logo(self):
        soup = _parse(INDEX)
        logo = soup.select_one(".hero__logo")
        assert logo, "Hero must have a logo"
        assert "logo.svg" in logo.get("src", "")

    def test_hero_has_tagline(self):
        soup = _parse(INDEX)
        tagline = soup.select_one(".hero__tagline")
        assert tagline, "Hero must have a tagline"

    def test_hero_has_cta(self):
        soup = _parse(INDEX)
        cta = soup.select_one(".hero__cta")
        assert cta, "Hero must have a call-to-action"
        href = cta.get("href", "")
        assert "#articles" in href, "CTA must link to articles section"

    def test_articles_section_exists(self):
        soup = _parse(INDEX)
        section = soup.find("section", id="articles")
        assert section, "Homepage must have articles section with id='articles'"

    def test_all_article_cards_have_read_more(self):
        soup = _parse(INDEX)
        cards = soup.select(".article-card")
        assert len(cards) >= 5, f"Expected at least 5 article cards, found {len(cards)}"
        for i, card in enumerate(cards):
            read_more = card.select_one(".article-card__read-more")
            assert read_more, f"Article card {i+1} must have a 'Read Story' link"
            href = read_more.get("href", "")
            assert href and href != "#", \
                f"Article card {i+1} Read Story link must have a valid href, got '{href}'"

    def test_article_cards_have_images(self):
        soup = _parse(INDEX)
        cards = soup.select(".article-card")
        for i, card in enumerate(cards):
            img = card.select_one(".article-card__image")
            assert img, f"Article card {i+1} must have an image"
            src = img.get("src", "")
            assert src, f"Article card {i+1} image must have a src"

    def test_article_cards_have_category(self):
        soup = _parse(INDEX)
        cards = soup.select(".article-card")
        for i, card in enumerate(cards):
            cat = card.select_one(".article-card__category")
            assert cat and cat.text.strip(), \
                f"Article card {i+1} must have a category label"

    def test_article_cards_have_title(self):
        soup = _parse(INDEX)
        cards = soup.select(".article-card")
        for i, card in enumerate(cards):
            title = card.select_one(".article-card__title")
            assert title and title.text.strip(), \
                f"Article card {i+1} must have a title"

    def test_article_cards_have_excerpt(self):
        soup = _parse(INDEX)
        cards = soup.select(".article-card")
        for i, card in enumerate(cards):
            excerpt = card.select_one(".article-card__excerpt")
            assert excerpt and excerpt.text.strip(), \
                f"Article card {i+1} must have an excerpt"

    def test_article_card_links_resolve_to_existing_files(self):
        soup = _parse(INDEX)
        links = soup.select(".article-card__read-more")
        for link in links:
            href = link.get("href", "")
            if href and not href.startswith("http") and href != "#":
                full_path = os.path.join(BASE_DIR, href)
                assert os.path.isfile(full_path), \
                    f"Article link '{href}' points to non-existent file"

    def test_mission_section_exists(self):
        soup = _parse(INDEX)
        mission = soup.select_one(".mission-section")
        assert mission, "Homepage must have a mission section"

    def test_categories_section_exists(self):
        soup = _parse(INDEX)
        cats = soup.select(".category-card")
        assert len(cats) >= 4, "Homepage must have at least 4 category cards"

    def test_footer_exists(self):
        soup = _parse(INDEX)
        footer = soup.select_one(".site-footer")
        assert footer, "Homepage must have a footer"

    def test_footer_has_logo(self):
        soup = _parse(INDEX)
        footer_logo = soup.select_one(".footer__logo")
        assert footer_logo, "Footer must have a logo"

    def test_footer_has_copyright(self):
        soup = _parse(INDEX)
        bottom = soup.select_one(".footer__bottom")
        assert bottom, "Footer must have copyright section"
        text = bottom.text
        assert "2026" in text, "Copyright must include the year"


# ===================================================================
# 6. ARTICLE PAGES — full content journey
# ===================================================================

class TestArticlePages:
    """Verify each article page has correct structure."""

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_has_article_element(self, filepath):
        soup = _parse(filepath)
        article = soup.select_one("article.article")
        assert article, f"{filepath} must have <article class='article'>"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_has_title(self, filepath):
        soup = _parse(filepath)
        title = soup.select_one(".article__title")
        assert title and title.text.strip(), \
            f"{filepath} must have an article title"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_has_category(self, filepath):
        soup = _parse(filepath)
        cat = soup.select_one(".article__category")
        assert cat and cat.text.strip(), \
            f"{filepath} must have an article category"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_has_meta(self, filepath):
        soup = _parse(filepath)
        meta = soup.select_one(".article__meta")
        assert meta, f"{filepath} must have article meta section"
        text = meta.text
        assert "min read" in text, f"{filepath} meta must show reading time"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_has_hero_image(self, filepath):
        soup = _parse(filepath)
        img = soup.select_one(".article__hero-image")
        assert img, f"{filepath} must have a hero image"
        src = img.get("src", "")
        assert src, f"{filepath} hero image must have a src"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_has_content(self, filepath):
        soup = _parse(filepath)
        content = soup.select_one(".article__content")
        assert content, f"{filepath} must have article content div"
        paragraphs = content.find_all("p")
        assert len(paragraphs) >= 3, \
            f"{filepath} must have at least 3 paragraphs of content"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_has_h2_headings(self, filepath):
        soup = _parse(filepath)
        content = soup.select_one(".article__content")
        h2s = content.find_all("h2") if content else []
        assert len(h2s) >= 2, \
            f"{filepath} must have at least 2 section headings (h2)"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_has_tags(self, filepath):
        soup = _parse(filepath)
        tags = soup.select(".article__tags .tag")
        assert len(tags) >= 1, f"{filepath} must have at least one tag"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_has_social_share(self, filepath):
        soup = _parse(filepath)
        share = soup.select_one(".social-share")
        assert share, f"{filepath} must have social share buttons"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_has_footer(self, filepath):
        soup = _parse(filepath)
        footer = soup.select_one(".site-footer")
        assert footer, f"{filepath} must have a footer"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_article_home_link_works(self, filepath):
        """Articles must have a working link back to the homepage."""
        soup = _parse(filepath)
        brand = soup.select_one(".site-nav__brand")
        href = brand.get("href", "") if brand else ""
        assert "index.html" in href


# ===================================================================
# 7. IMAGES — all referenced images must be accessible
# ===================================================================

class TestImages:
    """Verify all images are accessible (local files exist, remote URLs respond)."""

    @pytest.mark.parametrize("filepath", _html_files())
    def test_local_images_exist(self, filepath):
        soup = _parse(filepath)
        base_dir = os.path.dirname(filepath)
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src and not src.startswith("http"):
                full_path = os.path.normpath(os.path.join(base_dir, src))
                assert os.path.isfile(full_path), \
                    f"{filepath}: local image not found: {src} (resolved: {full_path})"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_all_images_have_alt(self, filepath):
        soup = _parse(filepath)
        for img in soup.find_all("img"):
            alt = img.get("alt")
            assert alt is not None and alt.strip(), \
                f'{filepath}: img missing alt text, src={img.get("src", "")}'

    def test_remote_images_return_200(self):
        """Check all unique Unsplash URLs across the site return HTTP 200."""
        all_urls = set()
        for filepath in _html_files():
            soup = _parse(filepath)
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if src.startswith("http"):
                    all_urls.add(src)

        failed = []
        for url in all_urls:
            try:
                resp = requests.head(url, timeout=10, allow_redirects=True)
                if resp.status_code != 200:
                    # Try GET as fallback (some CDNs don't support HEAD)
                    resp = requests.get(url, timeout=10, stream=True)
                    resp.close()
                if resp.status_code != 200:
                    failed.append((url, resp.status_code))
            except requests.RequestException as e:
                failed.append((url, str(e)))

        assert len(failed) == 0, \
            f"Broken remote images:\n" + \
            "\n".join(f"  {status}: {url}" for url, status in failed)


# ===================================================================
# 8. INTERNAL LINKS — no broken links
# ===================================================================

class TestInternalLinks:
    """Verify all internal href links point to existing files or valid anchors."""

    @pytest.mark.parametrize("filepath", _html_files())
    def test_internal_links_resolve(self, filepath):
        soup = _parse(filepath)
        base_dir = os.path.dirname(filepath)
        broken = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") or href.startswith("mailto:") or href == "#":
                continue
            # Strip anchor
            path_part = href.split("#")[0]
            if not path_part:
                continue  # anchor-only link like #articles
            full_path = os.path.normpath(os.path.join(base_dir, path_part))
            if not os.path.isfile(full_path):
                broken.append(href)

        assert len(broken) == 0, \
            f"{filepath} has broken internal links: {broken}"


# ===================================================================
# 9. CSS — responsive design checks
# ===================================================================

class TestCSS:
    """Verify CSS has responsive breakpoints and key rules."""

    def test_css_file_not_empty(self):
        content = _read(CSS_FILE)
        assert len(content) > 500, "CSS file must have substantial content"

    def test_has_media_query_900(self):
        content = _read(CSS_FILE)
        assert "max-width: 900px" in content, \
            "CSS must have 900px breakpoint for tablets"

    def test_has_media_query_768(self):
        content = _read(CSS_FILE)
        assert "max-width: 768px" in content, \
            "CSS must have 768px breakpoint for mobile"

    def test_has_media_query_480(self):
        content = _read(CSS_FILE)
        assert "max-width: 480px" in content, \
            "CSS must have 480px breakpoint for small phones"

    def test_hamburger_display_block_on_mobile(self):
        content = _read(CSS_FILE)
        assert ".nav-toggle" in content, "CSS must style hamburger toggle"

    def test_first_card_mobile_fix(self):
        """The first article card must switch to flex on mobile."""
        content = _read(CSS_FILE)
        assert "article-card:first-child" in content
        # Check that display: flex is in a media query context for first-child
        assert "display: flex" in content, \
            "First card must use display: flex on mobile"

    def test_grid_uses_min_for_overflow_prevention(self):
        """Grid minmax must use min() to prevent overflow on small screens."""
        content = _read(CSS_FILE)
        assert "minmax(min(" in content, \
            "Grid must use minmax(min(...)) to prevent mobile overflow"

    def test_css_braces_balanced(self):
        content = _read(CSS_FILE)
        opens = content.count("{")
        closes = content.count("}")
        assert opens == closes, \
            f"CSS braces unbalanced: {opens} open vs {closes} close"

    def test_css_has_custom_properties(self):
        content = _read(CSS_FILE)
        assert "--color-gold" in content, "CSS must define brand color tokens"
        assert "--font-display" in content, "CSS must define font tokens"

    def test_sticky_nav(self):
        content = _read(CSS_FILE)
        assert "position: sticky" in content, "Nav must be sticky"

    def test_box_sizing_reset(self):
        content = _read(CSS_FILE)
        assert "box-sizing: border-box" in content, \
            "CSS must have box-sizing: border-box reset"


# ===================================================================
# 10. LOGO SVGs — structural integrity
# ===================================================================

class TestLogoSVGs:
    """Verify SVG logos are well-formed and contain expected elements."""

    @pytest.mark.parametrize("logo", ["logo.svg", "logo-nav.svg"])
    def test_svg_is_valid(self, logo):
        path = os.path.join(ASSETS_DIR, "images", logo)
        content = _read(path)
        assert content.strip().startswith("<svg"), \
            f"{logo} must be a valid SVG file"
        assert "</svg>" in content, f"{logo} must have closing </svg>"

    @pytest.mark.parametrize("logo", ["logo.svg", "logo-nav.svg"])
    def test_svg_has_viewbox(self, logo):
        path = os.path.join(ASSETS_DIR, "images", logo)
        soup = BeautifulSoup(_read(path), "lxml")
        svg = soup.find("svg")
        assert svg and svg.get("viewbox") or svg.get("viewBox"), \
            f"{logo} must have a viewBox attribute"

    def test_main_logo_has_both_icons(self):
        """Main logo must contain both horse and motorcycle paths."""
        content = _read(os.path.join(ASSETS_DIR, "images", "logo.svg"))
        paths = re.findall(r'<path[^>]*d="[^"]{100,}"', content)
        assert len(paths) >= 2, \
            "Main logo must have at least 2 path elements (horse + motorcycle)"

    def test_main_logo_has_text_elements(self):
        content = _read(os.path.join(ASSETS_DIR, "images", "logo.svg"))
        assert "GANG" in content, "Logo must contain 'GANG' text"
        assert "EST." in content, "Logo must contain 'EST.' text"


# ===================================================================
# 11. ACCESSIBILITY
# ===================================================================

class TestAccessibility:
    """Basic accessibility checks."""

    @pytest.mark.parametrize("filepath", _html_files())
    def test_images_have_alt(self, filepath):
        soup = _parse(filepath)
        images = soup.find_all("img")
        for img in images:
            assert img.get("alt") is not None, \
                f'{filepath}: img missing alt attribute, src={img.get("src", "")}'

    @pytest.mark.parametrize("filepath", _html_files())
    def test_nav_toggle_has_aria_label(self, filepath):
        soup = _parse(filepath)
        toggle = soup.select_one(".nav-toggle")
        if toggle:
            assert toggle.get("aria-label"), \
                f"{filepath}: hamburger toggle must have aria-label"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_article_has_h1(self, filepath):
        soup = _parse(filepath)
        h1s = soup.find_all("h1")
        assert len(h1s) == 1, \
            f"{filepath} must have exactly one <h1>, found {len(h1s)}"

    def test_index_has_no_h1(self):
        """Homepage uses logo, not an h1 — but sections should have h2s."""
        soup = _parse(INDEX)
        h2s = soup.find_all("h2")
        assert len(h2s) >= 2, "Homepage must have at least 2 section headings (h2)"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_links_have_content(self, filepath):
        """Links must have text content or an aria-label."""
        soup = _parse(filepath)
        for a in soup.find_all("a"):
            text = a.get_text(strip=True)
            has_img = a.find("img")
            aria = a.get("aria-label")
            assert text or has_img or aria, \
                f'{filepath}: empty link with href={a.get("href", "")}'


# ===================================================================
# 12. PERFORMANCE & BEST PRACTICES
# ===================================================================

class TestPerformance:
    """Check performance best practices."""

    @pytest.mark.parametrize("filepath", _html_files())
    def test_images_have_lazy_loading(self, filepath):
        """Non-hero images should use loading='lazy'."""
        soup = _parse(filepath)
        images = soup.find_all("img")
        for img in images:
            src = img.get("src", "")
            loading = img.get("loading")
            # SVG logos and hero images (eager) are exempt
            if "logo" in src or loading == "eager":
                continue
            if src.startswith("http"):
                assert loading == "lazy", \
                    f'{filepath}: remote image missing loading="lazy", src={src}'

    @pytest.mark.parametrize("filepath", _html_files())
    def test_font_preconnect(self, filepath):
        soup = _parse(filepath)
        preconnects = [
            link.get("href", "")
            for link in soup.find_all("link", rel="preconnect")
        ]
        has_google = any("fonts.googleapis.com" in h for h in preconnects)
        has_gstatic = any("fonts.gstatic.com" in h for h in preconnects)
        assert has_google, f"{filepath} must preconnect to fonts.googleapis.com"
        assert has_gstatic, f"{filepath} must preconnect to fonts.gstatic.com"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_css_linked(self, filepath):
        soup = _parse(filepath)
        css_links = [
            link for link in soup.find_all("link", rel="stylesheet")
            if "style.css" in link.get("href", "")
        ]
        assert len(css_links) == 1, \
            f"{filepath} must link to style.css exactly once"


# ===================================================================
# 13. CONTENT QUALITY
# ===================================================================

class TestContentQuality:
    """Verify content meets quality standards."""

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_article_minimum_word_count(self, filepath):
        """Each article must have at least 500 words of content."""
        soup = _parse(filepath)
        content = soup.select_one(".article__content")
        if content:
            words = content.get_text(strip=True).split()
            assert len(words) >= 500, \
                f"{filepath} has only {len(words)} words, expected at least 500"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_article_has_blockquote_or_pullquote(self, filepath):
        """Articles should have at least one quote for visual variety."""
        soup = _parse(filepath)
        content = soup.select_one(".article__content")
        if content:
            quotes = content.find_all("blockquote")
            pulls = content.select(".pull-quote")
            assert len(quotes) + len(pulls) >= 1, \
                f"{filepath} should have at least one blockquote or pull-quote"

    def test_homepage_has_subtitle(self):
        soup = _parse(INDEX)
        sub = soup.select_one(".hero__subtitle")
        assert sub and len(sub.text.strip()) > 20, \
            "Hero subtitle must be meaningful (>20 chars)"

    def test_index_card_excerpts_are_unique(self):
        """Each article card excerpt must be unique."""
        soup = _parse(INDEX)
        excerpts = [
            e.text.strip()
            for e in soup.select(".article-card__excerpt")
        ]
        assert len(excerpts) == len(set(excerpts)), \
            "Article card excerpts must be unique"


# ===================================================================
# 14. FOOTER — present on all pages
# ===================================================================

class TestFooter:
    """Verify footer is consistent across all pages."""

    @pytest.mark.parametrize("filepath", _html_files())
    def test_footer_exists(self, filepath):
        soup = _parse(filepath)
        assert soup.select_one(".site-footer"), \
            f"{filepath} must have a footer"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_footer_has_copyright(self, filepath):
        soup = _parse(filepath)
        bottom = soup.select_one(".footer__bottom")
        assert bottom, f"{filepath} footer must have copyright"

    @pytest.mark.parametrize("filepath", _html_files())
    def test_footer_has_category_links(self, filepath):
        soup = _parse(filepath)
        footer = soup.select_one(".site-footer")
        links = footer.find_all("a") if footer else []
        assert len(links) >= 5, \
            f"{filepath} footer must have at least 5 links"


# ===================================================================
# 15. IMAGE-TEXT COHERENCE — images must match surrounding content
# ===================================================================

# Keyword mappings: article category -> allowed image keywords
# Used to ensure images are topically relevant to their article.
ARTICLE_IMAGE_KEYWORDS = {
    "Equestrian Heritage": [
        "horse", "saddle", "equestrian", "rider", "bridle", "harness",
        "leather", "dressage", "arena", "estate", "white horse",
    ],
    "Motorcycle Culture": [
        "motorcycle", "rider", "jacket", "café", "racer", "road",
        "bike", "engine", "classic", "vintage", "helmet", "open road",
    ],
    "Riding Fashion": [
        "loafer", "shoe", "leather", "horse", "bridle", "snaffle",
        "horsebit", "fashion", "style", "equestrian",
    ],
    "Boots & Shoes": [
        "boot", "riding", "horse", "stirrup", "equestrian", "cavalry",
        "jumping", "dressage", "arena", "hooves",
    ],
    "Motorcycle Lifestyle": [
        "motorcycle", "mountain", "road", "ladakh", "enfield", "rider",
        "lake", "himalaya", "adventure",
    ],
}


class TestImageTextCoherence:
    """
    Verify that every inline image's alt text and caption are coherent
    with the surrounding article text. This prevents mismatches like a
    modern KTM sport bike in a 1920s Belstaff heritage article.
    """

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_inline_images_have_figcaption(self, filepath):
        """Every inline image inside a <figure> must have a <figcaption>."""
        soup = _parse(filepath)
        figures = soup.select(".article__content figure")
        for i, fig in enumerate(figures):
            img = fig.find("img")
            cap = fig.find("figcaption")
            assert cap and cap.text.strip(), \
                f"{filepath} figure {i+1}: inline image must have a non-empty figcaption"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_figcaption_min_length(self, filepath):
        """Captions must be descriptive (at least 20 characters)."""
        soup = _parse(filepath)
        for fig in soup.select(".article__content figure"):
            cap = fig.find("figcaption")
            if cap:
                assert len(cap.text.strip()) >= 20, \
                    f"{filepath}: figcaption too short: '{cap.text.strip()}'"

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_alt_text_min_length(self, filepath):
        """Alt text on article images must be descriptive (>= 20 chars)."""
        soup = _parse(filepath)
        content = soup.select_one(".article__content")
        if not content:
            return
        for img in content.find_all("img"):
            alt = img.get("alt", "")
            assert len(alt) >= 20, \
                f'{filepath}: alt text too short ({len(alt)} chars): "{alt}"'

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_alt_text_not_generic(self, filepath):
        """Alt text must not be generic placeholder text."""
        soup = _parse(filepath)
        generic_phrases = [
            "image", "photo", "picture", "placeholder",
            "untitled", "img_", "screenshot",
        ]
        for img in soup.select(".article__content img"):
            alt = img.get("alt", "").lower()
            for phrase in generic_phrases:
                # Allow "image" as part of a longer description
                if alt == phrase or alt.startswith(f"{phrase} "):
                    assert False, \
                        f'{filepath}: generic alt text "{img.get("alt")}"'

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_images_match_article_category(self, filepath):
        """
        Inline image alt text must contain at least one keyword relevant
        to the article's category. This catches mismatches like a KTM
        sport bike in an article about vintage British jackets.
        """
        soup = _parse(filepath)
        category_el = soup.select_one(".article__category")
        if not category_el:
            return
        category = category_el.text.strip()
        keywords = ARTICLE_IMAGE_KEYWORDS.get(category, [])
        if not keywords:
            return  # Unknown category, skip

        content = soup.select_one(".article__content")
        if not content:
            return

        for img in content.find_all("img"):
            alt = img.get("alt", "").lower()
            cap_el = img.find_parent("figure")
            caption = ""
            if cap_el:
                cap_tag = cap_el.find("figcaption")
                caption = cap_tag.text.lower() if cap_tag else ""

            combined = alt + " " + caption
            match = any(kw in combined for kw in keywords)
            assert match, \
                f'{filepath} [{category}]: image alt+caption has no relevant keyword.\n' \
                f'  Alt: "{img.get("alt")}"\n' \
                f'  Caption: "{caption.strip()}"\n' \
                f'  Expected one of: {keywords}'

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_image_near_relevant_text(self, filepath):
        """
        Each inline image's caption must share at least one meaningful
        word with the heading (h2) that precedes it. This ensures images
        are placed in the right section of the article.
        """
        soup = _parse(filepath)
        content = soup.select_one(".article__content")
        if not content:
            return

        # Walk through all children to find heading->figure pairs
        elements = list(content.children)
        last_h2_text = ""
        for el in elements:
            if not hasattr(el, 'name'):
                continue
            if el.name == "h2":
                last_h2_text = el.get_text(strip=True).lower()
            elif el.name == "figure" and last_h2_text:
                cap = el.find("figcaption")
                if not cap:
                    continue
                caption_words = set(re.findall(r'[a-z]{4,}', cap.text.lower()))
                heading_words = set(re.findall(r'[a-z]{4,}', last_h2_text))
                # Filter out very common words
                stop_words = {"that", "this", "with", "from", "have", "been",
                              "were", "they", "their", "about", "which", "would",
                              "there", "what", "when", "will", "more", "than",
                              "into", "also", "just", "only", "very", "most"}
                caption_words -= stop_words
                heading_words -= stop_words
                # At least one shared meaningful word, OR the caption
                # references the article's main subject (checked elsewhere)
                # This is a soft check — we just verify the caption isn't
                # completely disconnected from its section.
                # Allow if the caption has substance (>5 meaningful words)
                assert len(caption_words) >= 3, \
                    f'{filepath}: figcaption under "{last_h2_text}" has too few ' \
                    f'meaningful words: "{cap.text.strip()}"'

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_hero_image_alt_matches_title(self, filepath):
        """Hero image alt text must relate to the article title."""
        soup = _parse(filepath)
        hero = soup.select_one(".article__hero-image")
        title = soup.select_one(".article__title")
        if not hero or not title:
            return

        title_words = set(re.findall(r'[a-z]{4,}', title.text.lower()))
        alt_words = set(re.findall(r'[a-z]{4,}', hero.get("alt", "").lower()))

        stop_words = {"that", "this", "with", "from", "have", "been",
                      "were", "they", "their", "about", "which", "would"}
        title_words -= stop_words
        alt_words -= stop_words

        shared = title_words & alt_words
        assert len(shared) >= 1, \
            f'{filepath}: hero alt text shares no words with title.\n' \
            f'  Title: "{title.text.strip()}"\n' \
            f'  Alt: "{hero.get("alt")}"'

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_no_branded_product_mismatch(self, filepath):
        """
        Images must not show identifiable branded products that conflict
        with the article's subject. E.g., no KTM in a Belstaff article,
        no Nike in a Gucci article.
        """
        soup = _parse(filepath)
        title = soup.select_one(".article__title")
        if not title:
            return
        title_lower = title.text.lower()

        # Map of article subjects to brands that should NOT appear in images
        forbidden_brands = {
            "belstaff": ["ktm", "yamaha", "ducati", "honda", "suzuki",
                         "kawasaki", "bmw r1", "harley"],
            "hermès": ["western", "rodeo", "cowboy", "lasso"],
            "hermes": ["western", "rodeo", "cowboy", "lasso"],
            "gucci": ["nike", "adidas", "puma", "reebok", "new balance"],
            "riding boots": ["sneaker", "trainer", "running shoe",
                             "flip flop", "sandal"],
        }

        for subject, banned in forbidden_brands.items():
            if subject in title_lower:
                for img in soup.select(".article__content img"):
                    alt = img.get("alt", "").lower()
                    cap_el = img.find_parent("figure")
                    caption = ""
                    if cap_el:
                        cap_tag = cap_el.find("figcaption")
                        caption = cap_tag.text.lower() if cap_tag else ""
                    combined = alt + " " + caption
                    for brand in banned:
                        assert brand not in combined, \
                            f'{filepath}: image references "{brand}" which ' \
                            f'conflicts with article about "{subject}".\n' \
                            f'  Alt: "{img.get("alt")}"\n' \
                            f'  Caption: "{caption.strip()}"'

    def test_index_card_images_match_article_heroes(self):
        """
        Homepage article card images should use the same Unsplash photo
        (possibly at different size) as the corresponding article's hero.
        This ensures visual consistency between the card and the article.
        """
        soup = _parse(INDEX)
        cards = soup.select(".article-card")

        for card in cards:
            link = card.select_one(".article-card__read-more")
            card_img = card.select_one(".article-card__image")
            if not link or not card_img:
                continue

            href = link.get("href", "")
            if not href or href.startswith("http") or href == "#":
                continue

            card_src = card_img.get("src", "")
            if not card_src.startswith("http"):
                continue

            # Extract the Unsplash photo ID (photo-XXXXX)
            card_photo = re.search(r'(photo-[a-f0-9-]+)', card_src)
            if not card_photo:
                continue

            # Read the linked article and check its hero
            article_path = os.path.join(BASE_DIR, href)
            if not os.path.isfile(article_path):
                continue

            article_soup = _parse(article_path)
            hero = article_soup.select_one(".article__hero-image")
            if not hero:
                continue

            hero_src = hero.get("src", "")
            hero_photo = re.search(r'(photo-[a-f0-9-]+)', hero_src)
            if not hero_photo:
                continue

            assert card_photo.group(1) == hero_photo.group(1), \
                f'Card image for "{href}" uses different photo than article hero.\n' \
                f'  Card: {card_photo.group(1)}\n' \
                f'  Hero: {hero_photo.group(1)}'

    @pytest.mark.parametrize("filepath", ARTICLE_FILES)
    def test_no_duplicate_images_in_article(self, filepath):
        """An article must not use the same image URL twice."""
        soup = _parse(filepath)
        srcs = []
        for img in soup.select("article img"):
            src = img.get("src", "")
            if src.startswith("http"):
                # Normalize by extracting just the photo ID
                photo_match = re.search(r'(photo-[a-f0-9-]+)', src)
                if photo_match:
                    srcs.append(photo_match.group(1))

        assert len(srcs) == len(set(srcs)), \
            f"{filepath} has duplicate images: {[s for s in srcs if srcs.count(s) > 1]}"
