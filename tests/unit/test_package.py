"""Smoke tests for the package metadata and public module."""

import re

import flet_toastify as fts

SEMVER_PATTERN = r"^\d+\.\d+\.\d+"


def test_package_exposes_version():
    assert re.match(SEMVER_PATTERN, fts.__version__)


def test_package_defines_public_api_listing():
    assert isinstance(fts.__all__, list)
