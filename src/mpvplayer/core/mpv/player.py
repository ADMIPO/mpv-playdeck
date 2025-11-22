"""基于 :mod:`mpvplayer.core.mpv.client` 的高层播放器接口。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer

from .client import MpvClient, MpvClientError
from ..models.playback_state import PlaybackState


class MpvPlayer:
    """供 UI 组件调用的简单播放控制门面。

    该类负责调用 :class:`MpvClient` 与 mpv 交互，并维护一个
    :class:`mpvplayer.core.models.playback_state.PlaybackState` 实例。UI 层可以通过
    :meth:`get_state` 订阅位置、时长、播放/暂停等信号，避免自行轮询 mpv。
    """

    def __init__(
        self,
        client: MpvClient | None = None,
        state: PlaybackState | None = None,
        poll_interval_ms: int = 500,
    ) -> None:
        self._client = client or MpvClient()
        self._state = state or PlaybackState()
        self._poll_timer = QTimer()
        self._poll_timer.setInterval(poll_interval_ms)
        self._poll_timer.timeout.connect(self._poll_playback)
        # TODO: 后续可替换为 mpv 事件驱动的观察者，减少轮询开销。
        self._poll_timer.start()

    def shutdown(self) -> None:
        """释放 mpv 资源。"""

        self._client.shutdown()
        self._poll_timer.stop()

    def set_render_target(self, window_id: int) -> None:
        """将原生窗口句柄传递给 mpv。"""

        self._client.set_wid(window_id)

    def get_state(self) -> PlaybackState:
        """返回可供 UI 订阅的播放状态模型。"""

        return self._state

    def open_file(self, path: Path) -> None:
        """打开并播放本地媒体文件。"""

        self._client.load_file(path)
        self._state.set_file_path(str(path))
        self._state.set_position(0.0)
        self._state.set_eof(False)
        self._state.set_is_paused(False)
        self._state.set_is_playing(True)
        duration = self._client.get_property("duration")
        self._state.set_duration(float(duration) if duration is not None else None)

    def play(self) -> None:
        """开始或恢复播放。"""

        self._client.set_pause(False)
        self._state.set_is_paused(False)
        self._state.set_is_playing(True)
        self._state.set_eof(False)

    def toggle_pause(self) -> None:
        """切换暂停状态。"""

        self._client.toggle_pause()
        paused = self.is_paused()
        self._state.set_is_paused(paused)
        self._state.set_is_playing(not paused)
        if not paused:
            self._state.set_eof(False)

    def pause(self) -> None:
        """暂停播放。"""

        self._client.set_pause(True)
        self._state.set_is_paused(True)
        self._state.set_is_playing(False)

    def resume(self) -> None:
        """恢复播放。"""

        self._client.set_pause(False)
        self._state.set_is_paused(False)
        self._state.set_is_playing(True)
        self._state.set_eof(False)

    def seek(self, position: float) -> None:
        """跳转到媒体的绝对时间位置（秒）。"""

        self._client.command("seek", position, "absolute")
        self._state.set_position(position)

    def seek_relative(self, delta: float) -> None:
        """在当前位置基础上快进/快退。"""

        self._client.command("seek", delta, "relative")

    def set_volume(self, volume: float) -> None:
        """设置音量（0-100）。"""

        self._client.set_property("volume", volume)
        self._state.set_volume(volume)

    def set_mute(self, muted: bool) -> None:
        """设置静音状态。"""

        self._client.set_property("mute", muted)
        self._state.set_mute(muted)

    def get_position(self) -> float | None:
        """获取当前播放时间（秒）。"""

        return self._client.get_property("time-pos")

    def get_duration(self) -> float | None:
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

    def _poll_playback(self) -> None:
        """定时读取 mpv 属性，保持 :class:`PlaybackState` 同步。

        目前采用 Qt 定时器轮询 mpv 属性，后续可替换为 mpv 的事件观察回调，
        以减少无效查询。
        """

        try:
            position = self._client.get_property("time-pos")
            if position is not None:
                self._state.set_position(float(position))

            duration = self._client.get_property("duration")
            if duration is not None:
                self._state.set_duration(float(duration))

            paused = bool(self._client.get_property("pause"))
            self._state.set_is_paused(paused)

            volume = self._client.get_property("volume")
            if volume is not None:
                self._state.set_volume(float(volume))

            muted = self._client.get_property("mute")
            if muted is not None:
                self._state.set_mute(bool(muted))

            speed = self._client.get_property("speed")
            if speed is not None:
                self._state.set_speed(float(speed))

            eof_reached = bool(self._client.get_property("eof-reached"))
            self._state.set_eof(eof_reached)

            # 播放中意味着未暂停且未到结尾。
            self._state.set_is_playing(not paused and not eof_reached)
        except MpvClientError:
            # mpv 尚未初始化或已关闭时可能出现异常，忽略即可等待下一次轮询。
            return


__all__ = ["MpvPlayer", "MpvClientError"]
