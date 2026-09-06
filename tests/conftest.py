"""Shared fixtures for the shd-site checks.

The site is static, so every test works against the files on disk. Nothing here
needs a network or a browser; the one test module that does reach the network is
marked `network` and deselected by default.
"""
from __future__ import annotations

import pathlib

import pytest
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "network: requires outbound HTTP access")


@pytest.fixture(scope="session")
def root() -> pathlib.Path:
    return ROOT


@pytest.fixture(scope="session")
def index_html() -> str:
    return (ROOT / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def soup(index_html: str) -> BeautifulSoup:
    return BeautifulSoup(index_html, "lxml")


@pytest.fixture(scope="session")
def stylesheet() -> str:
    return (ROOT / "assets" / "css" / "site.css").read_text(encoding="utf-8")
