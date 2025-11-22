"""基于 :mod:`mpvplayer.core.mpv.client` 的高层播放器接口。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .client import MpvClient, MpvClientError


class MpvPlayer:
    """供 UI 组件调用的简单播放控制门面。"""

    def __init__(self, client: Optional[MpvClient] = None) -> None:
        self._client = client or MpvClient()

    def shutdown(self) -> None:
        """释放 mpv 资源。"""

        self._client.shutdown()

    def set_render_target(self, window_id: int) -> None:
        """将原生窗口句柄传递给 mpv。"""

        self._client.set_wid(window_id)

    def open_file(self, path: Path) -> None:
        """打开并播放本地媒体文件。"""

        self._client.load_file(path)

    def play(self) -> None:
        """开始或恢复播放。"""

        self._client.set_pause(False)

    def toggle_pause(self) -> None:
        """切换暂停状态。"""

        self._client.toggle_pause()

    def pause(self) -> None:
        """暂停播放。"""

        self._client.set_pause(True)

    def resume(self) -> None:
        """恢复播放。"""

        self._client.set_pause(False)

    def seek(self, position: float) -> None:
        """跳转到媒体的绝对时间位置（秒）。"""

        self._client.command("seek", position, "absolute")

    def seek_relative(self, delta: float) -> None:
        """在当前位置基础上快进/快退。"""

        self._client.command("seek", delta, "relative")

    def set_volume(self, volume: float) -> None:
        """设置音量（0-100）。"""

        self._client.set_property("volume", volume)

    def set_mute(self, muted: bool) -> None:
        """设置静音状态。"""

        self._client.set_property("mute", muted)

    def get_position(self) -> Optional[float]:
        """获取当前播放时间（秒）。"""

        return self._client.get_property("time-pos")

    def get_duration(self) -> Optional[float]:
        """获取媒体总时长（秒）。"""

        return self._client.get_property("duration")

    def is_paused(self) -> bool:
        """返回当前是否处于暂停状态。"""

        pause = self._client.get_property("pause")
        return bool(pause)

    @property
    def client(self) -> MpvClient:
        """暴露底层 :class:`MpvClient`，供高级用例使用。"""

        return self._client


__all__ = ["MpvPlayer", "MpvClientError"]
