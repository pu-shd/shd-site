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


def test_no_cname_file(root):
    """shd.princeton.edu is served by the Azure Static Web App, not Pages.

    A CNAME file would make GitHub Pages claim the same hostname, which at best
    is dead configuration and at worst fights the Azure custom domain. Pages is
    only the preview environment now, on its pu-shd.github.io URL.
    """
    assert not (root / "CNAME").exists(), (
        "the custom domain belongs to the Static Web App; see infra/set-custom-domain.sh"
    )


def test_workflows_are_present(root):
    workflows = sorted(p.name for p in (root / ".github" / "workflows").glob("*.yml"))
    for expected in ("ci.yml", "pages.yml", "azure-swa.yml"):
        assert expected in workflows, f"missing workflow: {expected}"


def test_infra_is_scripted_with_a_teardown(root):
    """Deploy, teardown and domain attachment are all scripted, not manual."""
    for script in ("config.sh", "deploy.sh", "teardown.sh", "set-custom-domain.sh"):
        path = root / "infra" / script
        assert path.is_file(), f"missing infra/{script}"
    for script in ("deploy.sh", "teardown.sh", "set-custom-domain.sh"):
        assert (root / "infra" / script).stat().st_mode & 0o111, f"infra/{script} not executable"


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
