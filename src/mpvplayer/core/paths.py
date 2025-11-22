"""Helpers for resolving important filesystem locations.

This module avoids any Qt imports and is intended to be reused by both core
and UI layers. The paths are computed relative to the installed package
location, making it robust to running from source or an installed wheel.
"""

from __future__ import annotations

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
THIRD_PARTY_DIR = PROJECT_ROOT / "third_party"
MPV_DIR = THIRD_PARTY_DIR / "mpv"


def project_root() -> Path:
    """Return the absolute path to the repository root directory."""

    return PROJECT_ROOT


def third_party_dir() -> Path:
    """Return the absolute path to the ``third_party`` directory."""

    return THIRD_PARTY_DIR


def mpv_binary_dir() -> Path:
    """Return the directory expected to contain ``libmpv-2.dll``.

    On Windows, this directory must be added to the DLL search path before
    importing the :mod:`mpv` bindings. The caller is responsible for ensuring
    the DLL actually exists inside this directory.
    """

    return MPV_DIR
