"""基于 `python-mpv` 绑定的 libmpv 轻量封装。

本模块提供一个最小化、与界面无关的接口，用于在应用中嵌入 libmpv。它负责创建 mpv
实例、绑定原生窗口句柄以及加载媒体文件。任何与 Qt 相关的逻辑都应位于本层之外。
"""

from __future__ import annotations

import logging
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Callable, Optional

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
        self._mpv_instance: object | None = None
        self._event_callbacks: list[Callable[[object], None]] = []
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

    def command(self, name: str, *args: object) -> object:
        """执行 mpv 的任意指令。

        Parameters
        ----------
        name:
            指令名称，例如 ``"loadfile"``、``"seek"``。
        *args:
            可变参数列表，对应 mpv 指令的参数顺序。
        """

        instance = self._require_instance()
        return instance.command(name, *args)

    def set_property(self, name: str, value: object) -> None:
        """设置 mpv 属性。

        参数 ``name`` 接受 mpv 原生属性名，例如 ``"volume"``、``"time-pos"``。
        """

        instance = self._require_instance()
        attr_name = name.replace("-", "_")
        self._logger.debug("set_property %s=%r (attr=%s)", name, value, attr_name)
        try:
            setattr(instance, attr_name, value)
        except Exception as exc:  # pragma: no cover - 依赖运行时 mpv
            self._logger.error("Failed to set property %s: %s", name, exc)
            raise MpvClientError(f"Failed to set property {name!r}") from exc

    def get_property(self, name: str) -> object | None:
        """读取 mpv 属性。

        参数 ``name`` 使用 mpv 原生属性名。如果属性不可用或不存在，返回 ``None``。
        """

        instance = self._require_instance()
        attr_name = name.replace("-", "_")
        try:
            return getattr(instance, attr_name)
        except Exception as exc:  # pragma: no cover - 依赖运行时 mpv
            self._logger.debug(
                "Failed to get property %s (attr=%s): %s", name, attr_name, exc
            )
            return None

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

        self.set_property("pause", paused)

    def toggle_pause(self) -> None:
        """切换当前的暂停状态。"""

        current = bool(self.get_property("pause"))
        self.set_property("pause", not current)

    def observe_property(self, name: str, callback: Callable[[str, object], None]) -> None:
        """注册 mpv 属性观察回调。"""

        instance = self._require_instance()
        instance.observe_property(name, callback)

    def unobserve_property(self, name: str, callback: Callable[[str, object], None]) -> None:
        """取消 mpv 属性观察回调。"""

        instance = self._require_instance()
        instance.unobserve_property(name, callback)

    def add_event_callback(self, callback: Callable[[object], None]) -> None:
        """添加事件回调，在 :meth:`poll_event` 收到事件时触发。"""

        self._event_callbacks.append(callback)

    def remove_event_callback(self, callback: Callable[[object], None]) -> None:
        """移除事件回调。"""

        try:
            self._event_callbacks.remove(callback)
        except ValueError:
            self._logger.debug("callback not registered, ignore removal")

    def poll_event(self, timeout: float = 0.1) -> Optional[object]:
        """轮询 mpv 事件并触发已注册的回调。"""

        instance = self._require_instance()
        event = instance.wait_for_event(timeout)
        if event:
            for callback in list(self._event_callbacks):
                try:
                    callback(event)
                except Exception:  # pragma: no cover - 调试辅助
                    self._logger.exception("Unhandled exception in mpv event callback")
        return event

    def _require_instance(self) -> object:
        if not self._mpv_instance:
            raise MpvClientError("mpv is not initialized")
        return self._mpv_instance
