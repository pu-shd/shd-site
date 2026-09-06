"""Assets: every reference resolves, paths stay relative, weight stays sane."""
from __future__ import annotations

import re
import urllib.parse

import pytest

# GitHub Pages serves a project repo from /<repo>/ until the custom domain is
# attached, and from / afterwards. Root-relative paths break in the first case,
# so every local reference must be relative.
LOCAL_ATTRS = (("img", "src"), ("script", "src"), ("link", "href"), ("source", "srcset"))

# Budget for what a first visit actually pulls down, in kilobytes.
HERO_BUDGET_KB = 320
IMAGE_BUDGET_KB = 400


def _local_refs(soup):
    for tag_name, attr in LOCAL_ATTRS:
        for tag in soup.find_all(tag_name):
            value = tag.get(attr)
            if not value:
                continue
            # srcset is a comma-separated candidate list; src/href are single
            # URLs that may legitimately contain commas.
            candidates = re.split(r",\s*", value) if attr == "srcset" else [value]
            for candidate in candidates:
                url = candidate.strip().split(" ")[0]
                if not url or url.startswith(("http://", "https://", "//", "#", "data:", "mailto:")):
                    continue
                yield tag_name, attr, url


def test_referenced_files_exist(soup, root):
    missing = [
        url for _, _, url in _local_refs(soup)
        if not (root / urllib.parse.unquote(url)).is_file()
    ]
    assert not missing, f"referenced but absent: {missing}"


def test_local_paths_are_relative(soup):
    absolute = [url for _, _, url in _local_refs(soup) if url.startswith("/")]
    assert not absolute, (
        f"root-relative paths break project-page hosting: {absolute}"
    )


def test_css_url_references_exist(stylesheet, root):
    css_dir = root / "assets" / "css"
    for match in re.finditer(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", stylesheet):
        url = match.group(1).strip()
        if url.startswith(("http", "data:", "#")):
            continue
        assert (css_dir / url).resolve().is_file(), f"missing CSS asset: {url}"


def test_stylesheet_is_linked_not_inlined(soup):
    assert soup.find("link", rel="stylesheet", href=re.compile(r"site\.css$"))
    assert not soup.find("style"), "keep styles in assets/css/site.css"


def test_no_inline_style_attributes(soup):
    offenders = [str(t)[:80] for t in soup.find_all(style=True)]
    assert not offenders, f"inline styles belong in the stylesheet: {offenders}"


def test_favicons_present(soup, root):
    hrefs = {
        link["href"]
        for link in soup.find_all("link", rel=True) if link.get("href")
    }
    assert "assets/img/favicon.svg" in hrefs
    assert "assets/img/apple-touch-icon.png" in hrefs
    for href in hrefs:
        if href.startswith("assets/"):
            assert (root / href).is_file()


def test_open_graph_image_exists_locally(soup, root):
    og_image = soup.find("meta", attrs={"property": "og:image"})["content"]
    assert og_image.endswith("assets/img/og-card.jpg")
    assert (root / "assets" / "img" / "og-card.jpg").is_file()


@pytest.mark.parametrize("name", ["hero", "hero-1200w", "screens", "lantern",
                                  "townsquare", "reflection", "terrace"])
def test_every_jpeg_has_a_webp_sibling(root, name):
    jpg = root / "assets" / "img" / f"{name}.jpg"
    webp = root / "assets" / "img" / f"{name}.webp"
    assert jpg.is_file(), f"{name}.jpg missing — run scripts/build-images.sh"
    assert webp.is_file(), f"{name}.webp missing — run scripts/build-images.sh"
    assert webp.stat().st_size < jpg.stat().st_size, "the webp should be the smaller one"


def test_hero_stays_within_budget(root):
    size_kb = (root / "assets" / "img" / "hero.webp").stat().st_size / 1024
    assert size_kb <= HERO_BUDGET_KB, f"hero.webp is {size_kb:.0f} KB"


def test_no_single_image_is_oversized(root):
    heavy = {
        path.name: round(path.stat().st_size / 1024)
        for path in (root / "assets" / "img").glob("*")
        if path.stat().st_size / 1024 > IMAGE_BUDGET_KB
    }
    assert not heavy, f"over {IMAGE_BUDGET_KB} KB: {heavy}"


def test_originals_are_not_committed(root):
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    assert "_source/" in gitignore, "the full-resolution originals must stay untracked"


def test_nojekyll_present(root):
    assert (root / ".nojekyll").exists(), (
        "GitHub Pages skips files and folders beginning with an underscore "
        "unless .nojekyll is present"
    )
