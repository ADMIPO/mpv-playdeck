"""基于 `python-mpv` 绑定的 libmpv 轻量封装。

本模块提供一个最小化、与界面无关的接口，用于在应用中嵌入 libmpv。它负责创建 mpv
实例、绑定原生窗口句柄以及加载媒体文件。任何与 Qt 相关的逻辑都应位于本层之外。
"""

from __future__ import annotations

import logging
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Optional

from ..logger import get_logger


class MpvClientError(RuntimeError):
    """在 mpv 无法初始化或使用时抛出的异常。"""


class MpvClient:
    """对 :class:`mpv.MPV` 的最小封装。

    Parameters
    ----------
    log:
        可选的日志记录器。如果未提供，将使用本模块的默认记录器。
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
        # mpv 返回的日志等级是字符串（例如 'info'、'error'）。
        self._logger.log(logging.getLevelName(level.upper()), f"{prefix}: {text}")

    def shutdown(self) -> None:
        """终止底层 mpv 实例。"""

        if self._mpv_instance:
            self._mpv_instance.terminate()
            self._mpv_instance = None

    def set_wid(self, window_id: int) -> None:
        """将 mpv 的视频输出绑定到原生窗口句柄。"""

        if not self._mpv_instance:
            raise MpvClientError("mpv is not initialized")
        self._mpv_instance.wid = window_id

    def load_file(self, path: Path) -> None:
        """加载并开始播放本地媒体文件。"""

        if not self._mpv_instance:
            raise MpvClientError("mpv is not initialized")
        if not path.exists():
            raise MpvClientError(f"File does not exist: {path}")
        self._mpv_instance.play(str(path))

    def set_pause(self, paused: bool) -> None:
        """暂停或恢复播放。"""

        if not self._mpv_instance:
            raise MpvClientError("mpv is not initialized")
        self._mpv_instance.pause = paused

    def toggle_pause(self) -> None:
        """切换当前的暂停状态。"""

        if not self._mpv_instance:
            raise MpvClientError("mpv is not initialized")
        self._mpv_instance.pause = not self._mpv_instance.pause
