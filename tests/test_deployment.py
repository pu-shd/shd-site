"""Repository conventions that GitHub Pages depends on."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ElementTree

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def test_index_html_is_at_the_repository_root(root):
    assert (root / "index.html").is_file(), "Pages serves / from index.html at the root"


def test_the_full_page_is_staged_alongside_it(root):
    """preview.html holds the landing page until it is swapped in at /."""
    assert (root / "preview.html").is_file(), (
        "the full page should stay in the repository while the holding page is served"
    )


def test_only_the_holding_page_is_published(root):
    """The staged page must not ship, or it is public in all but name."""
    build = (root / "scripts" / "build-site.sh").read_text(encoding="utf-8")
    copied = re.search(r"for item in ([^\n]+); do", build).group(1).split()
    assert "index.html" in copied
    assert "preview.html" not in copied, (
        "preview.html would be reachable on the published site"
    )


def test_robots_allows_indexing_and_names_the_sitemap(root):
    robots = (root / "robots.txt").read_text(encoding="utf-8")
    assert "Disallow: /" not in robots
    assert "https://shd.princeton.edu/sitemap.xml" in robots


def test_sitemap_is_valid_and_lists_the_canonical_url(root):
    tree = ElementTree.parse(root / "sitemap.xml")
    locations = [el.text for el in tree.iter(f"{SITEMAP_NS}loc")]
    assert locations == ["https://shd.princeton.edu/"]


def test_custom_domain_is_not_claimed_before_dns_exists(root):
    """A CNAME file with no matching DNS record takes the site offline.

    Add it — or set the custom domain in the Pages settings — only once
    shd.princeton.edu actually resolves to GitHub.
    """
    cname = root / "CNAME"
    if cname.exists():
        assert cname.read_text(encoding="utf-8").strip() == "shd.princeton.edu"


def test_workflows_are_present(root):
    workflows = sorted(p.name for p in (root / ".github" / "workflows").glob("*.yml"))
    assert "ci.yml" in workflows
    assert "pages.yml" in workflows


def test_scripts_are_executable(root):
    for script in (root / "scripts").glob("*.sh"):
        assert script.stat().st_mode & 0o111, f"{script.name} is not executable"


def test_readme_documents_the_domain_switch(root):
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "shd.princeton.edu" in readme
    assert "CNAME" in readme


def test_readme_documents_the_holding_page(root):
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "preview.html" in readme, "the swap has to be written down somewhere"
