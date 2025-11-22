"""High-level player interface built on top of :mod:`mpvplayer.core.mpv.client`."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .client import MpvClient, MpvClientError


class MpvPlayer:
    """Simple facade used by UI components to control playback."""

    def __init__(self, client: Optional[MpvClient] = None) -> None:
        self._client = client or MpvClient()

    def shutdown(self) -> None:
        """Release mpv resources."""

        self._client.shutdown()

    def set_render_target(self, window_id: int) -> None:
        """Send the native window handle to mpv."""

        self._client.set_wid(window_id)

    def open_file(self, path: Path) -> None:
        """Open and play a local media file."""

        self._client.load_file(path)

    def toggle_pause(self) -> None:
        """Toggle the pause state."""

        self._client.toggle_pause()

    def pause(self) -> None:
        """Pause playback."""

        self._client.set_pause(True)

    def resume(self) -> None:
        """Resume playback."""

        self._client.set_pause(False)

    @property
    def client(self) -> MpvClient:
        """Expose the underlying :class:`MpvClient` for advanced use cases."""

        return self._client


__all__ = ["MpvPlayer", "MpvClientError"]
