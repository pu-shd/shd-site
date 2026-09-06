"""Accessibility basics that a static check can hold the line on."""
from __future__ import annotations

import re

VAGUE_LINK_TEXT = {"here", "click here", "read more", "more", "link", "this"}


def test_content_images_have_alt_text(soup):
    for img in soup.find_all("img"):
        assert img.has_attr("alt"), f"img without alt: {img.get('src')}"


def test_decorative_images_are_hidden_and_content_images_are_described(soup):
    for img in soup.find_all("img"):
        alt = img["alt"]
        if img.get("class") and "hero__img" in img["class"]:
            assert alt == "", "the hero photograph is decorative; the panel carries the text"
            continue
        assert len(alt) >= 20, f"alt text too thin to be useful: {alt!r}"
        assert not alt.lower().startswith(("image of", "picture of", "photo of"))


def test_images_declare_intrinsic_size(soup):
    for img in soup.find_all("img"):
        assert img.get("width") and img.get("height"), (
            f"{img.get('src')} needs width/height so the layout does not shift"
        )


def test_offscreen_images_are_lazy_and_the_masthead_and_hero_are_not(soup):
    """Everything below the fold defers; the signature and the hero do not."""
    for img in soup.find_all("img"):
        classes = img.get("class") or []
        if "hero__img" in classes:
            assert img.get("loading") != "lazy", "never lazy-load the LCP image"
            assert img.get("fetchpriority") == "high"
        elif img.find_parent("header", class_="masthead"):
            assert img.get("loading") != "lazy", (
                "the University signature renders first; deferring it flashes an empty header"
            )
        else:
            assert img.get("loading") == "lazy"


def test_link_text_is_never_vague(soup):
    for anchor in soup.find_all("a"):
        text = " ".join(anchor.get_text(" ", strip=True).split()).lower()
        assert text.strip(".") not in VAGUE_LINK_TEXT, f"vague link text: {text!r}"


def test_every_link_has_an_accessible_name(soup):
    for anchor in soup.find_all("a"):
        # An image-only link takes its name from the image's alt text.
        alt = " ".join(img.get("alt", "") for img in anchor.find_all("img"))
        name = anchor.get_text(" ", strip=True) or anchor.get("aria-label") or alt
        assert name.strip(), f"link with no accessible name: {anchor}"


def test_svg_icons_are_hidden_from_assistive_tech(soup):
    for svg in soup.find_all("svg"):
        assert svg.get("aria-hidden") == "true" or svg.find("title"), (
            "decorative SVGs need aria-hidden; meaningful ones need a <title>"
        )


def test_focus_is_always_visible(stylesheet):
    assert ":focus-visible" in stylesheet
    assert "outline: none" not in stylesheet.replace(" ", " ")


def test_reduced_motion_is_honoured(stylesheet):
    assert "prefers-reduced-motion" in stylesheet, (
        "smooth scrolling must be switched off for users who ask for less motion"
    )


def test_font_sizes_are_relative(stylesheet):
    px_font_sizes = re.findall(r"font-size:\s*\d+px", stylesheet)
    assert not px_font_sizes, f"use rem so browser zoom works: {px_font_sizes}"


def test_body_background_and_colour_are_explicit(stylesheet):
    body_block = re.search(r"\nbody\s*\{(.*?)\}", stylesheet, re.S)
    assert body_block, "expected a body rule"
    assert "background:" in body_block.group(1)
    assert "color:" in body_block.group(1)
