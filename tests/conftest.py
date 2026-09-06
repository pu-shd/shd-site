"""Shared fixtures for the shd-site checks.

Two documents live in this repository:

  index.html    the holding page currently served at /
  preview.html  the full landing page, staged for the swap

Checks that should hold for anything we publish are parametrized over both via
the `page` fixture. Checks specific to one document take `placeholder` or
`preview` directly.

The site is static, so every test works against the files on disk. Nothing here
needs a network or a browser; the one module that reaches the network is marked
`network` and deselected by default.
"""
from __future__ import annotations

import dataclasses
import pathlib

import pytest
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent

PLACEHOLDER = "index.html"
PREVIEW = "preview.html"
PAGES = (PLACEHOLDER, PREVIEW)


@dataclasses.dataclass(frozen=True)
class Page:
    name: str
    html: str
    soup: BeautifulSoup

    def __str__(self) -> str:  # keeps pytest ids readable
        return self.name


def _load(name: str) -> Page:
    html = (ROOT / name).read_text(encoding="utf-8")
    return Page(name=name, html=html, soup=BeautifulSoup(html, "lxml"))


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "network: requires outbound HTTP access")


@pytest.fixture(scope="session")
def root() -> pathlib.Path:
    return ROOT


@pytest.fixture(scope="session", params=PAGES, ids=PAGES)
def page(request: pytest.FixtureRequest) -> Page:
    """Every document this repository publishes, one at a time."""
    return _load(request.param)


@pytest.fixture(scope="session")
def placeholder() -> Page:
    return _load(PLACEHOLDER)


@pytest.fixture(scope="session")
def preview() -> Page:
    return _load(PREVIEW)


@pytest.fixture(scope="session")
def stylesheet() -> str:
    return (ROOT / "assets" / "css" / "site.css").read_text(encoding="utf-8")
