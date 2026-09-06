"""The document itself: head metadata, landmarks, and heading order."""
from __future__ import annotations

import json
import re

CANONICAL = "https://shd.princeton.edu/"


def test_html_declares_language(soup):
    assert soup.html.get("lang") == "en"


def test_charset_and_viewport_present(soup):
    assert soup.find("meta", charset=True)["charset"].lower() == "utf-8"
    viewport = soup.find("meta", attrs={"name": "viewport"})
    assert viewport and "width=device-width" in viewport["content"]


def test_title_is_present_and_reasonable(soup):
    title = soup.title.string.strip()
    assert "Sherrerd Hall" in title
    assert "SHD" in title
    assert len(title) <= 70, "titles over ~70 chars get truncated in search results"


def test_meta_description_present_and_sized(soup):
    desc = soup.find("meta", attrs={"name": "description"})
    assert desc, "a landing page needs a meta description"
    assert 80 <= len(desc["content"]) <= 200


def test_canonical_points_at_the_custom_domain(soup):
    link = soup.find("link", rel="canonical")
    assert link and link["href"] == CANONICAL


def test_open_graph_card_is_complete(soup):
    required = {
        "og:type", "og:title", "og:description",
        "og:url", "og:image", "og:image:width", "og:image:height", "og:image:alt",
    }
    found = {
        m["property"]: m["content"]
        for m in soup.find_all("meta", attrs={"property": True})
    }
    assert required <= found.keys(), f"missing: {sorted(required - found.keys())}"
    assert found["og:url"] == CANONICAL
    assert found["og:image"].startswith("https://"), "og:image must be absolute"


def test_exactly_one_h1(soup):
    assert len(soup.find_all("h1")) == 1


def test_heading_levels_never_skip(soup):
    levels = [int(h.name[1]) for h in soup.find_all(re.compile(r"^h[1-6]$"))]
    for previous, current in zip(levels, levels[1:]):
        assert current <= previous + 1, f"h{previous} is followed by h{current}"


def test_landmarks_present(soup):
    assert soup.find("header", class_="masthead")
    assert soup.find("main", id="main")
    assert soup.find("footer")


def test_skip_link_targets_main(soup):
    skip = soup.find("a", class_="skip")
    assert skip and skip["href"] == "#main"
    assert soup.find(id="main"), "skip link target must exist"


def test_every_section_is_labelled(soup):
    for section in soup.find_all("section"):
        labelled_by = section.get("aria-labelledby")
        assert labelled_by, "each section needs aria-labelledby for screen readers"
        assert soup.find(id=labelled_by), f"no element with id={labelled_by!r}"


def test_structured_data_parses(soup):
    blocks = soup.find_all("script", type="application/ld+json")
    assert blocks, "expected JSON-LD for the site"
    for block in blocks:
        data = json.loads(block.string)
        assert data["@context"] == "https://schema.org"
        assert data["@type"]


def test_in_page_anchors_resolve(soup):
    for anchor in soup.find_all("a", href=re.compile(r"^#.")):
        target = anchor["href"][1:]
        assert soup.find(id=target), f"dead in-page link: #{target}"
