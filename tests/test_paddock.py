"""
Test suite for The Paddock — the machine repository.

Covers data/machines.json (the canonical record), machines.html (the index),
and every long-form article in articles/machines/.

The Paddock's editorial rule is that its content must never be wrong, so these
tests are deliberately strict about structure, completeness and link integrity.

Run with: pytest tests/test_paddock.py -v
"""

import os
import re
import json
import glob
import pytest
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MACHINES_JSON = os.path.join(BASE_DIR, "data", "machines.json")
MACHINES_INDEX = os.path.join(BASE_DIR, "machines.html")
MACHINE_ARTICLES_DIR = os.path.join(BASE_DIR, "articles", "machines")
MACHINE_ARTICLES = sorted(glob.glob(os.path.join(MACHINE_ARTICLES_DIR, "*.html")))
INDEX = os.path.join(BASE_DIR, "index.html")

BRAND_NAME = "The Rider's Gang"

REQUIRED_SECTIONS = [
    "Why This Machine",
    "The Beauty",
    "The Power",
    "The History Behind It",
    "What It Costs",
    "Where to Find One",
    "What Makes It Unlike Anything Else",
]

REQUIRED_MACHINE_FIELDS = [
    "id", "kind", "name", "manufacturer", "origin", "country", "type",
    "launched", "engine", "power", "cardDescription", "image", "imageSource",
    "imageLicence", "imageVerified", "article", "moreInfoUrl", "moreInfoLabel",
    "pricing", "sourcing", "uniquePoints", "publishedDate",
]


def _data():
    with open(MACHINES_JSON, encoding="utf-8") as f:
        return json.load(f)


def _parse(filepath):
    with open(filepath, encoding="utf-8") as f:
        return BeautifulSoup(f.read(), "lxml")


def _raw(filepath):
    with open(filepath, encoding="utf-8") as f:
        return f.read()


MACHINES = _data()["machines"]
MACHINE_IDS = [m["id"] for m in MACHINES]


# ---------------------------------------------------------------------------
# The data repository
# ---------------------------------------------------------------------------

class TestMachinesData:

    def test_json_is_valid(self):
        assert _data(), "machines.json did not parse"

    def test_has_schema_and_section(self):
        d = _data()
        assert "$schema" in d, "machines.json must document its own schema"
        assert "section" in d
        assert "machines" in d

    def test_schema_documents_pricing_disclaimer(self):
        schema = _data()["$schema"]
        assert "pricingDisclaimer" in schema
        assert "approximate" in schema["pricingDisclaimer"].lower()

    def test_schema_documents_editorial_rule(self):
        schema = _data()["$schema"]
        assert "editorialRule" in schema
        assert "never be wrong" in schema["editorialRule"].lower()

    def test_schema_documents_how_to_add(self):
        schema = _data()["$schema"]
        assert isinstance(schema.get("howToAddAMachine"), list)
        assert len(schema["howToAddAMachine"]) >= 4, \
            "the repository must document how to grow it"

    def test_covers_both_bikes_and_cars(self):
        kinds = {m["kind"] for m in MACHINES}
        assert "motorcycle" in kinds, "The Paddock must cover motorcycles"
        assert "car" in kinds, "The Paddock must cover cars"

    def test_machine_ids_unique(self):
        assert len(MACHINE_IDS) == len(set(MACHINE_IDS)), "duplicate machine ids"

    def test_machine_of_the_moment_is_a_real_machine(self):
        motm = _data()["section"]["machineOfTheMoment"]
        assert motm in MACHINE_IDS, f"machineOfTheMoment '{motm}' is not a known machine"

    def test_index_page_declared(self):
        page = _data()["section"]["indexPage"]
        assert os.path.exists(os.path.join(BASE_DIR, page)), f"missing {page}"

    @pytest.mark.parametrize("machine", MACHINES, ids=MACHINE_IDS)
    def test_required_fields_present(self, machine):
        for field in REQUIRED_MACHINE_FIELDS:
            assert field in machine, f"{machine.get('id')}: missing field '{field}'"
            assert machine[field] not in (None, "", [], {}), \
                f"{machine.get('id')}: field '{field}' is empty"

    @pytest.mark.parametrize("machine", MACHINES, ids=MACHINE_IDS)
    def test_kind_is_valid(self, machine):
        assert machine["kind"] in ("motorcycle", "car")

    @pytest.mark.parametrize("machine", MACHINES, ids=MACHINE_IDS)
    def test_image_exists_and_is_real(self, machine):
        path = os.path.join(BASE_DIR, machine["image"])
        assert os.path.exists(path), f"{machine['id']}: image missing at {machine['image']}"
        assert os.path.getsize(path) > 20_000, \
            f"{machine['id']}: image suspiciously small — is it an error page?"
        with open(path, "rb") as f:
            assert f.read(2) == b"\xff\xd8", f"{machine['id']}: image is not a valid JPEG"

    @pytest.mark.parametrize("machine", MACHINES, ids=MACHINE_IDS)
    def test_image_is_verified(self, machine):
        assert machine["imageVerified"] is True, \
            f"{machine['id']}: image must be visually verified as the actual model"

    @pytest.mark.parametrize("machine", MACHINES, ids=MACHINE_IDS)
    def test_image_source_and_licence_recorded(self, machine):
        assert len(machine["imageSource"]) > 15, f"{machine['id']}: image source too vague"
        assert len(machine["imageLicence"]) > 3, f"{machine['id']}: image licence not recorded"

    @pytest.mark.parametrize("machine", MACHINES, ids=MACHINE_IDS)
    def test_article_exists(self, machine):
        path = os.path.join(BASE_DIR, machine["article"])
        assert os.path.exists(path), f"{machine['id']}: article missing at {machine['article']}"

    @pytest.mark.parametrize("machine", MACHINES, ids=MACHINE_IDS)
    def test_pricing_is_framed_as_indicative(self, machine):
        indicative = machine["pricing"]["indicative"].lower()
        assert any(w in indicative for w in ("approx", "from", "~")), \
            f"{machine['id']}: price must be framed as approximate, not absolute"

    @pytest.mark.parametrize("machine", MACHINES, ids=MACHINE_IDS)
    def test_sourcing_covers_multiple_markets(self, machine):
        sourcing = machine["sourcing"]
        assert len(sourcing) >= 4, \
            f"{machine['id']}: needs at least 4 markets so readers worldwide are served"
        for row in sourcing:
            for key in ("market", "availability", "indicativePrice"):
                assert row.get(key), f"{machine['id']}: sourcing row missing '{key}'"

    @pytest.mark.parametrize("machine", MACHINES, ids=MACHINE_IDS)
    def test_has_unique_points(self, machine):
        assert len(machine["uniquePoints"]) >= 2, \
            f"{machine['id']}: needs at least 2 unique points"

    @pytest.mark.parametrize("machine", MACHINES, ids=MACHINE_IDS)
    def test_production_status_declared(self, machine):
        status = machine.get("productionStatus", "")
        assert status == "current" or re.fullmatch(r"ended-\d{4}", status), \
            f"{machine['id']}: productionStatus must be 'current' or 'ended-<year>', got {status!r}"

    @pytest.mark.parametrize("machine", MACHINES, ids=MACHINE_IDS)
    def test_discontinued_machines_are_not_sold_as_current(self, machine):
        """A machine out of production must never read as a showroom purchase."""
        if machine["productionStatus"] == "current":
            return
        blob = " ".join([
            machine["cardDescription"],
            machine["pricing"]["indicative"],
            machine["pricing"].get("note", ""),
            " ".join(r["availability"] for r in machine["sourcing"]),
        ]).lower()
        assert any(w in blob for w in
                   ("out of production", "used", "remaining stock", "ended", "no longer")), \
            f"{machine['id']}: production has ended but nothing says so"

    @pytest.mark.parametrize("machine", MACHINES, ids=MACHINE_IDS)
    def test_more_info_url_is_absolute(self, machine):
        assert machine["moreInfoUrl"].startswith("https://"), \
            f"{machine['id']}: moreInfoUrl must be an absolute https URL"


# ---------------------------------------------------------------------------
# The machine articles
# ---------------------------------------------------------------------------

class TestMachineArticles:

    def test_every_machine_has_an_article_file(self):
        assert len(MACHINE_ARTICLES) >= len(MACHINES), \
            f"expected at least {len(MACHINES)} machine articles, found {len(MACHINE_ARTICLES)}"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_has_all_required_sections(self, path):
        text = _raw(path)
        for section in REQUIRED_SECTIONS:
            assert section in text, f"{os.path.basename(path)}: missing section '{section}'"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_has_spec_plate(self, path):
        soup = _parse(path)
        plate = soup.select_one(".spec-plate")
        assert plate, f"{os.path.basename(path)}: missing spec plate"
        items = plate.select(".spec-plate__item")
        assert len(items) >= 4, f"{os.path.basename(path)}: spec plate needs 4 entries"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_has_scrollable_sourcing_table(self, path):
        soup = _parse(path)
        table = soup.select_one("table.sourcing-table")
        assert table, f"{os.path.basename(path)}: missing sourcing table"
        # The table must be wrapped so it never scrolls the whole page sideways
        assert table.find_parent(class_="table-scroll"), \
            f"{os.path.basename(path)}: sourcing table must sit inside .table-scroll"
        rows = table.select("tbody tr") or table.select("tr")[1:]
        assert len(rows) >= 4, \
            f"{os.path.basename(path)}: sourcing table needs at least 4 markets"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_asset_paths_are_two_levels_up(self, path):
        soup = _parse(path)
        css = soup.select_one('link[rel="stylesheet"][href$="style.css"]')
        assert css, f"{os.path.basename(path)}: stylesheet not linked"
        assert css["href"] == "../../assets/css/style.css", \
            f"{os.path.basename(path)}: stylesheet path must be ../../ from articles/machines/"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_local_assets_resolve(self, path):
        soup = _parse(path)
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src.startswith("http") or not src:
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), src))
            assert os.path.exists(resolved), \
                f"{os.path.basename(path)}: broken image src '{src}'"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_internal_links_resolve(self, path):
        soup = _parse(path)
        for a in soup.find_all("a", href=True):
            href = a["href"].split("#")[0]
            if not href or href.startswith(("http", "mailto:", "#")):
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), href))
            assert os.path.exists(resolved), \
                f"{os.path.basename(path)}: broken link '{a['href']}'"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_has_hero_image_with_alt(self, path):
        soup = _parse(path)
        hero = soup.select_one("img.article__hero-image")
        assert hero, f"{os.path.basename(path)}: missing hero image"
        assert len(hero.get("alt", "")) > 10, \
            f"{os.path.basename(path)}: hero image needs descriptive alt text"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_has_seo_metadata(self, path):
        soup = _parse(path)
        title = soup.find("title")
        assert title and BRAND_NAME in title.get_text(), \
            f"{os.path.basename(path)}: title must carry the brand"
        desc = soup.find("meta", attrs={"name": "description"})
        assert desc and len(desc.get("content", "")) > 60, \
            f"{os.path.basename(path)}: needs a substantial meta description"
        kw = soup.find("meta", attrs={"name": "keywords"})
        assert kw and len(kw.get("content", "")) > 20, \
            f"{os.path.basename(path)}: needs keywords"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_is_substantial_longform(self, path):
        soup = _parse(path)
        content = soup.select_one(".article__content")
        assert content, f"{os.path.basename(path)}: missing article content block"
        words = len(content.get_text().split())
        assert words >= 1000, \
            f"{os.path.basename(path)}: only {words} words — The Paddock is long-form"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_has_nav_and_footer(self, path):
        soup = _parse(path)
        assert soup.select_one("nav.site-nav"), f"{os.path.basename(path)}: missing nav"
        assert soup.select_one("footer.site-footer"), f"{os.path.basename(path)}: missing footer"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_links_back_to_paddock(self, path):
        soup = _parse(path)
        assert soup.select_one(".article__back-link"), \
            f"{os.path.basename(path)}: needs a way back to The Paddock"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_has_tags(self, path):
        soup = _parse(path)
        tags = soup.select(".article__tags .tag")
        assert len(tags) >= 6, f"{os.path.basename(path)}: needs at least 6 tags"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_prices_are_hedged_not_absolute(self, path):
        """Cost claims must read as indicative, never as a firm quote."""
        text = _parse(path).get_text().lower()
        assert any(w in text for w in ("approx", "indicative", "approximately", "around")), \
            f"{os.path.basename(path)}: pricing must be framed as approximate"

    @pytest.mark.parametrize("path", MACHINE_ARTICLES,
                             ids=[os.path.basename(p) for p in MACHINE_ARTICLES])
    def test_no_unreplaced_template_placeholders(self, path):
        raw = _raw(path)
        leftovers = re.findall(r"\{\{[A-Z_]+\}\}", raw)
        assert not leftovers, \
            f"{os.path.basename(path)}: unreplaced placeholders {set(leftovers)}"


# ---------------------------------------------------------------------------
# The Paddock index page
# ---------------------------------------------------------------------------

class TestPaddockIndex:

    def test_exists(self):
        assert os.path.exists(MACHINES_INDEX)

    def test_has_masthead(self):
        soup = _parse(MACHINES_INDEX)
        assert soup.select_one(".paddock-masthead__title")

    def test_has_both_sections(self):
        soup = _parse(MACHINES_INDEX)
        assert soup.select_one("#motorcycles"), "missing motorcycles section"
        assert soup.select_one("#cars"), "missing cars section"

    def test_lists_every_machine(self):
        soup = _parse(MACHINES_INDEX)
        cards = soup.select(".machine-card")
        assert len(cards) == len(MACHINES), \
            f"index shows {len(cards)} machines but data has {len(MACHINES)}"

    def test_every_machine_article_is_linked(self):
        raw = _raw(MACHINES_INDEX)
        for m in MACHINES:
            assert m["article"] in raw, f"machines.html does not link {m['id']}"

    def test_all_links_resolve(self):
        soup = _parse(MACHINES_INDEX)
        for a in soup.find_all("a", href=True):
            href = a["href"].split("#")[0]
            if not href or href.startswith(("http", "mailto:", "#")):
                continue
            assert os.path.exists(os.path.join(BASE_DIR, href)), \
                f"machines.html: broken link '{a['href']}'"

    def test_all_images_resolve(self):
        soup = _parse(MACHINES_INDEX)
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src.startswith("http") or not src:
                continue
            assert os.path.exists(os.path.join(BASE_DIR, src)), \
                f"machines.html: broken image '{src}'"

    def test_carries_price_disclaimer(self):
        soup = _parse(MACHINES_INDEX)
        note = soup.select_one(".price-disclaimer")
        assert note, "The Paddock index must carry the pricing disclaimer"
        text = note.get_text().lower()
        assert "indicative" in text and "approximate" in text

    def test_every_card_has_specs_and_link(self):
        soup = _parse(MACHINES_INDEX)
        for card in soup.select(".machine-card"):
            name = card.select_one(".machine-card__name")
            assert name, "a machine card has no name"
            assert card.select_one(".machine-card__specs"), f"{name.get_text()}: no specs"
            assert card.select_one(".machine-card__link"), f"{name.get_text()}: no article link"


# ---------------------------------------------------------------------------
# Homepage integration — the Paddock must stay wired into the site
# ---------------------------------------------------------------------------

class TestHomepageIntegration:

    def test_hero_features_machine_of_the_moment(self):
        soup = _parse(INDEX)
        card = soup.select_one(".hero__machine")
        assert card, "homepage hero must feature a machine"
        motm_id = _data()["section"]["machineOfTheMoment"]
        motm = next(m for m in MACHINES if m["id"] == motm_id)
        assert motm["name"] in card.get_text(), \
            f"hero should feature {motm['name']} (the declared machineOfTheMoment)"

    def test_hero_links_to_full_article(self):
        soup = _parse(INDEX)
        link = soup.select_one(".hero__machine-link")
        assert link, "hero machine needs a link to its story"
        assert os.path.exists(os.path.join(BASE_DIR, link["href"])), \
            f"hero machine link is broken: {link['href']}"

    def test_paddock_rail_links_resolve(self):
        soup = _parse(INDEX)
        cards = soup.select(".rail-card")
        assert len(cards) >= 3, "paddock rail should show the rest of the stable"
        for a in cards:
            assert os.path.exists(os.path.join(BASE_DIR, a["href"])), \
                f"rail card link is broken: {a['href']}"

    def test_nav_reaches_the_paddock(self):
        soup = _parse(INDEX)
        hrefs = [a["href"] for a in soup.select(".site-nav__links a[href]")]
        assert "machines.html" in hrefs, "nav must link to The Paddock"

    def test_no_stale_sidebar_markup(self):
        raw = _raw(INDEX)
        assert "bike-sidebar" not in raw, "the retired sidebar markup is still present"

    def test_discontinued_machines_flagged_on_index(self):
        """The Paddock index must not imply a discontinued machine is on sale."""
        raw = _raw(MACHINES_INDEX).lower()
        for m in MACHINES:
            if m["productionStatus"] == "current":
                continue
            assert "out of production" in raw, \
                f"{m['id']} has ended production but machines.html does not say so"
