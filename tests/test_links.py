"""Outbound links: shape by default, and reachability when asked for it.

princeton.edu sits behind Cloudflare bot detection. The `x-wdsoit-bot-bypass`
header gets an automated client through; the value is not checked, only the
presence of the header.
"""
from __future__ import annotations

import concurrent.futures
import urllib.error
import urllib.request

import pytest

BOT_BYPASS = {"x-wdsoit-bot-bypass": "true"}
USER_AGENT = "shd-site-linkcheck/1.0 (+https://shd.princeton.edu/)"
TIMEOUT = 25

# The two destinations this page exists to point at.
REQUIRED_DESTINATIONS = {
    "https://github.com/pu-shd",
    "https://facilities.princeton.edu/projects/sherrerd-hall-2008",
}

ALLOWED_HOSTS = {
    "github.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "orfe.princeton.edu",
    "citp.princeton.edu",
    "facilities.princeton.edu",
    "alumni.princeton.edu",
    "fisherpartners.net",
    "www.princeton.edu",
    "accessibility.princeton.edu",
    "inclusive.princeton.edu",
    "shd.princeton.edu",
}


def external_links(soup):
    seen = {}
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if href.startswith(("http://", "https://")):
            seen.setdefault(href, anchor)
    return seen


def test_no_plain_http_links(soup):
    insecure = [href for href in external_links(soup) if href.startswith("http://")]
    assert not insecure, f"link over plain HTTP: {insecure}"


def test_external_hosts_are_expected(soup):
    from urllib.parse import urlsplit

    unexpected = {
        urlsplit(href).hostname
        for href in external_links(soup)
        if urlsplit(href).hostname not in ALLOWED_HOSTS
    }
    assert not unexpected, f"unreviewed outbound host: {sorted(unexpected)}"


def test_both_destinations_are_linked(soup):
    hrefs = set(external_links(soup))
    assert REQUIRED_DESTINATIONS <= hrefs, (
        f"missing: {sorted(REQUIRED_DESTINATIONS - hrefs)}"
    )


def test_highlighted_repositories_are_distinct(soup):
    """Each highlighted repo appears once, and the organization is linked out."""
    repo_links = [
        a["href"] for a in soup.select(".highlights li a")
        if a["href"].startswith("https://github.com/pu-shd/")
    ]
    assert repo_links, "expected the highlights to link repositories"
    assert len(repo_links) == len(set(repo_links)), "a repository is highlighted twice"
    more = soup.select_one(".more a")
    assert more and more["href"] == "https://github.com/pu-shd", (
        "the highlights are a sample; the organization must be linked for the rest"
    )


def _fetch_status(url: str) -> int:
    request = urllib.request.Request(
        url, method="GET", headers={"User-Agent": USER_AGENT, **BOT_BYPASS}
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


@pytest.mark.network
def test_every_external_link_resolves(soup):
    urls = sorted(external_links(soup))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = dict(zip(urls, pool.map(_fetch_status, urls)))
    broken = {url: status for url, status in results.items() if status >= 400}
    assert not broken, f"broken links: {broken}"


def test_private_repositories_are_never_linked(soup):
    """A link to a private repo shows a stranger a 404, so we only ever name them."""
    for item in soup.select(".is-private"):
        assert not item.find("a"), f"private entry must not link out: {item.get_text(strip=True)}"
        assert item.find("code"), "a private entry still names the repository"


# Princeton requires these on University sites; losing one is a compliance
# problem, not a cosmetic one.
REQUIRED_POLICY_LINKS = {
    "https://www.princeton.edu/content/copyright-infringement",
    "https://www.princeton.edu/privacy-notice",
    "https://accessibility.princeton.edu/help",
    "https://inclusive.princeton.edu/about/"
    "our-commitment-equal-opportunity-and-non-discrimination",
}


def test_university_policy_links_are_present(soup):
    subfooter = soup.select_one(".subfoot")
    assert subfooter, "the University subfooter is missing"
    hrefs = {a["href"] for a in subfooter.select("a[href]")}
    assert REQUIRED_POLICY_LINKS <= hrefs, (
        f"missing required policy links: {sorted(REQUIRED_POLICY_LINKS - hrefs)}"
    )


def test_university_attribution_is_present(soup):
    subfooter = soup.select_one(".subfoot")
    assert "The Trustees of Princeton University" in subfooter.get_text()
    shield = subfooter.select_one(".subfoot__shield img")
    assert shield and shield["alt"] == "Princeton University"
    assert shield["src"].endswith("pu-logo-stacked-white.svg")
    assert subfooter.select_one(".subfoot__shield")["href"] == "https://www.princeton.edu"
