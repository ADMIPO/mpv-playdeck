"""播放状态模型。

该模块提供 :class:`PlaybackState`，用于描述 mpv 当前的播放状态并通过 Qt
信号对外通知。模型本身与界面解耦，可被 :class:`mpvplayer.core.mpv.player.MpvPlayer`
维护，并在 UI 层订阅其信号以更新进度条、按钮状态等。
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class PlaybackState(QObject):
    """封装 mpv 播放状态的可观察模型。"""

    file_path_changed = Signal(object)
    position_changed = Signal(float)
    duration_changed = Signal(object)
    playing_changed = Signal(bool)
    paused_changed = Signal(bool)
    volume_changed = Signal(float)
    mute_changed = Signal(bool)
    speed_changed = Signal(float)
    eof_changed = Signal(bool)

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        file_path: str | None = None,
        is_playing: bool = False,
        is_paused: bool = False,
        position: float = 0.0,
        duration: float | None = 0.0,
        volume: float = 100.0,
        mute: bool = False,
        speed: float = 1.0,
        eof: bool = False,
    ) -> None:
        super().__init__(parent)
        self._file_path: str | None = file_path
        self._is_playing = is_playing
        self._is_paused = is_paused
        self._position = position
        self._duration: float | None = duration
        self._volume = volume
        self._mute = mute
        self._speed = speed
        self._eof = eof

    @property
    def file_path(self) -> str | None:
        """当前播放的文件路径。"""

        return self._file_path

    def set_file_path(self, value: str | None) -> None:
        """更新文件路径并发射变更信号。"""

        if value == self._file_path:
            return
        self._file_path = value
        self.file_path_changed.emit(value)

    @property
    def is_playing(self) -> bool:
        """是否正在播放（非暂停/停止）。"""

        return self._is_playing

    def set_is_playing(self, value: bool) -> None:
        """更新播放状态并发射变更信号。"""

        if value == self._is_playing:
            return
        self._is_playing = value
        self.playing_changed.emit(value)

    @property
    def is_paused(self) -> bool:
        """是否处于暂停状态。"""

        return self._is_paused

    def set_is_paused(self, value: bool) -> None:
        """更新暂停状态并发射变更信号。"""

        if value == self._is_paused:
            return
        self._is_paused = value
        self.paused_changed.emit(value)

    @property
    def position(self) -> float:
        """当前播放位置（秒）。"""

        return self._position

    def set_position(self, value: float) -> None:
        """更新播放位置并发射变更信号。"""

        if value == self._position:
            return
        self._position = value
        self.position_changed.emit(value)

    @property
    def duration(self) -> float | None:
        """媒体总时长（秒），未知时为 ``None`` 或 ``0``。"""

        return self._duration

    def set_duration(self, value: float | None) -> None:
        """更新媒体时长并发射变更信号。"""

        if value == self._duration:
            return
        self._duration = value
        self.duration_changed.emit(value)

    @property
    def volume(self) -> float:
        """当前音量。"""

        return self._volume

    def set_volume(self, value: float) -> None:
        """更新音量并发射变更信号。"""

        if value == self._volume:
            return
        self._volume = value
        self.volume_changed.emit(value)

    @property
    def mute(self) -> bool:
        """是否静音。"""

        return self._mute

    def set_mute(self, value: bool) -> None:
        """更新静音状态并发射变更信号。"""

        if value == self._mute:
            return
        self._mute = value
        self.mute_changed.emit(value)

    @property
    def speed(self) -> float:
        """播放速度。"""

        return self._speed

    def set_speed(self, value: float) -> None:
        """更新播放速度并发射变更信号。"""

        if value == self._speed:
            return
        self._speed = value
        self.speed_changed.emit(value)

    @property
    def eof(self) -> bool:
        """是否已播放到结尾。"""

        return self._eof

    def set_eof(self, value: bool) -> None:
        """更新 EOF 状态并发射变更信号。"""

        if value == self._eof:
            return
        self._eof = value
        self.eof_changed.emit(value)


__all__ = ["PlaybackState"]
