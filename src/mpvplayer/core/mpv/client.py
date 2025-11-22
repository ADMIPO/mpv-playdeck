"""Thin wrapper around libmpv using the `python-mpv` bindings.

The goal of this module is to provide a minimal, UI-agnostic interface for
embedding libmpv into the application. It handles creating the mpv instance,
binding it to a native window handle, and loading media files. Any Qt-specific
logic should stay outside of this layer.
"""

from __future__ import annotations

import logging
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Optional

from ..logger import get_logger


class MpvClientError(RuntimeError):
    """Raised when mpv cannot be initialized or used."""


class MpvClient:
    """Minimal wrapper around :class:`mpv.MPV`.

    Parameters
    ----------
    log:
        Optional logger to use. If omitted, a default logger for this module
        will be used.
    """

    def __init__(self, log: Optional[logging.Logger] = None) -> None:
        self._logger = log or get_logger(__name__)
        self._mpv_module: Optional[ModuleType] = None
        self._mpv_instance = None
        self._create_instance()

    def _load_binding(self) -> ModuleType:
        try:
            return import_module("mpv")
        except ImportError as exc:  # pragma: no cover - runtime dependency
            raise MpvClientError(
                "python-mpv is not installed or libmpv could not be loaded. "
                "Ensure libmpv-2.dll is present in third_party/mpv and the directory "
                "is on PATH."
            ) from exc

    def _create_instance(self) -> None:
        self._mpv_module = self._load_binding()
        try:
            self._mpv_instance = self._mpv_module.MPV(
                log_handler=self._log_handler, ytdl=False
            )
        except Exception as exc:  # pragma: no cover - defensive path
            raise MpvClientError("Failed to initialize libmpv") from exc

    def _log_handler(self, level: str, prefix: str, text: str) -> None:
        # mpv provides level as string (e.g., 'info', 'error').
        self._logger.log(logging.getLevelName(level.upper()), f"{prefix}: {text}")

    def shutdown(self) -> None:
        """Terminate the underlying mpv instance."""

        if self._mpv_instance:
            self._mpv_instance.terminate()
            self._mpv_instance = None

    def set_wid(self, window_id: int) -> None:
        """Bind mpv's video output to a native window handle."""

        if not self._mpv_instance:
            raise MpvClientError("mpv is not initialized")
        self._mpv_instance.wid = window_id

    def load_file(self, path: Path) -> None:
        """Load and start playing a local media file."""

        if not self._mpv_instance:
            raise MpvClientError("mpv is not initialized")
        if not path.exists():
            raise MpvClientError(f"File does not exist: {path}")
        self._mpv_instance.play(str(path))

    def set_pause(self, paused: bool) -> None:
        """Pause or resume playback."""

        if not self._mpv_instance:
            raise MpvClientError("mpv is not initialized")
        self._mpv_instance.pause = paused

    def toggle_pause(self) -> None:
        """Toggle the pause state."""

        if not self._mpv_instance:
            raise MpvClientError("mpv is not initialized")
        self._mpv_instance.pause = not self._mpv_instance.pause
