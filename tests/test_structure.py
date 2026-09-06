"""Document structure: head metadata, landmarks, and heading order."""
from __future__ import annotations

import json
import re

CANONICAL = "https://shd.princeton.edu/"


# ---- true of anything we publish -----------------------------------------

def test_html_declares_language(page):
    assert page.soup.html.get("lang") == "en"


def test_charset_and_viewport_present(page):
    assert page.soup.find("meta", charset=True)["charset"].lower() == "utf-8"
    viewport = page.soup.find("meta", attrs={"name": "viewport"})
    assert viewport and "width=device-width" in viewport["content"]


def test_title_is_present_and_reasonable(page):
    title = page.soup.title.string.strip()
    assert "SHD" in title
    assert len(title) <= 70, "titles over ~70 chars get truncated in search results"


def test_exactly_one_h1(page):
    assert len(page.soup.find_all("h1")) == 1


def test_heading_levels_never_skip(page):
    levels = [int(h.name[1]) for h in page.soup.find_all(re.compile(r"^h[1-6]$"))]
    for previous, current in zip(levels, levels[1:]):
        assert current <= previous + 1, f"h{previous} is followed by h{current}"


def test_main_and_footer_landmarks_present(page):
    assert page.soup.find("main"), "every page needs a main landmark"
    assert page.soup.find("footer"), "every page needs a footer"


def test_skip_link_if_present_resolves(page):
    skip = page.soup.find("a", class_="skip")
    if skip is None:
        return  # the holding page is short enough not to need one
    assert page.soup.find(id=skip["href"][1:]), "skip link target must exist"


def test_in_page_anchors_resolve(page):
    for anchor in page.soup.find_all("a", href=re.compile(r"^#.")):
        target = anchor["href"][1:]
        assert page.soup.find(id=target), f"dead in-page link: #{target}"


def test_structured_data_parses(page):
    for block in page.soup.find_all("script", type="application/ld+json"):
        data = json.loads(block.string)
        assert data["@context"] == "https://schema.org"
        assert data["@type"]


def test_open_graph_has_at_least_the_basics(page):
    found = {
        m["property"]: m["content"]
        for m in page.soup.find_all("meta", attrs={"property": True})
    }
    assert {"og:type", "og:title", "og:url"} <= found.keys()
    assert found["og:url"] == CANONICAL


# ---- the holding page ------------------------------------------------------

def test_holding_page_is_not_indexable(placeholder):
    """A 'Coming soon' snippet should not become the site's search result."""
    robots = placeholder.soup.find("meta", attrs={"name": "robots"})
    assert robots and "noindex" in robots["content"]


def test_holding_page_mentions_nothing_but_shd(placeholder):
    """It carries the mark, the message, and the required University footer."""
    main_text = placeholder.soup.find("main").get_text(" ", strip=True)
    assert "SHD" in main_text
    assert "Coming soon" in main_text
    for absent in ("Sherrerd Hall", "ORFE", "GitHub", "pu-shd", "Princeton University"):
        assert absent not in main_text, f"holding page should not mention {absent!r}"


def test_holding_page_links_out_only_where_required(placeholder):
    """No navigation, no destinations — only the policy links in the subfooter."""
    outside_subfooter = [
        a for a in placeholder.soup.find_all("a", href=True)
        if not a.find_parent(class_="subfoot")
    ]
    assert not outside_subfooter, (
        f"unexpected links: {[a['href'] for a in outside_subfooter]}"
    )
    assert not placeholder.soup.find("nav"), "the holding page has nothing to navigate"


# ---- the full page --------------------------------------------------------

def test_preview_meta_description_present_and_sized(preview):
    desc = preview.soup.find("meta", attrs={"name": "description"})
    assert desc, "the landing page needs a meta description"
    assert 80 <= len(desc["content"]) <= 200


def test_preview_canonical_points_at_the_custom_domain(preview):
    link = preview.soup.find("link", rel="canonical")
    assert link and link["href"] == CANONICAL


def test_preview_open_graph_card_is_complete(preview):
    required = {
        "og:type", "og:site_name", "og:title", "og:description",
        "og:url", "og:image", "og:image:width", "og:image:height", "og:image:alt",
    }
    found = {
        m["property"]: m["content"]
        for m in preview.soup.find_all("meta", attrs={"property": True})
    }
    assert required <= found.keys(), f"missing: {sorted(required - found.keys())}"
    assert found["og:image"].startswith("https://"), "og:image must be absolute"


def test_preview_has_a_masthead_and_labelled_sections(preview):
    assert preview.soup.find("header", class_="masthead")
    for section in preview.soup.find_all("section"):
        labelled_by = section.get("aria-labelledby")
        assert labelled_by, "each section needs aria-labelledby for screen readers"
        assert preview.soup.find(id=labelled_by), f"no element with id={labelled_by!r}"


def test_preview_is_indexable(preview):
    """Whatever the holding page says, the real page must be crawlable."""
    robots = preview.soup.find("meta", attrs={"name": "robots"})
    assert robots is None or "noindex" not in robots["content"]
