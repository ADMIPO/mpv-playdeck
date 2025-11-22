"""应用程序启动辅助工具。

本模块负责创建 QApplication 并完成早期的进程初始化，例如在导入 mpv 绑定前确保
libmpv 的 DLL 目录在 Windows 上可被发现。UI 组件应在此处创建，并传入所需依赖。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, Optional

from PySide6.QtWidgets import QApplication

from .core.logger import get_logger, setup_logging
from .core.paths import mpv_binary_dir
from .ui.windows.main_window import MainWindow

_LOGGER = get_logger(__name__)


def _ensure_mpv_on_path(mpv_dir: Path) -> None:
    """在 Windows 上将 mpv DLL 目录加入搜索路径。

    该函数必须在导入任何会加载 ``libmpv-2.dll`` 的模块前执行。用户需要将 DLL 放到
    项目根目录下的 ``third_party/mpv``，或根据需要调整路径。如果运行时找不到 DLL，
    mpv 初始化将失败并给出清晰的错误信息。
    """

    if os.name != "nt":
        return

    if not mpv_dir.exists():
        _LOGGER.warning("Expected mpv directory does not exist: %s", mpv_dir)

    # os.add_dll_directory 在 Python 3.8+ 可用，是修改当前进程 DLL 搜索顺序的推荐方式。
    os.add_dll_directory(str(mpv_dir))

    # 同时写入 PATH，确保子进程（如果有）也能继承该目录。
    current_path = os.environ.get("PATH", "")
    path_parts = current_path.split(os.pathsep) if current_path else []
    if str(mpv_dir) not in path_parts:
        os.environ["PATH"] = str(mpv_dir) + os.pathsep + current_path


def run(argv: Optional[Iterable[str]] = None) -> int:
    """创建并运行 Qt 应用程序。

    Parameters
    ----------
    argv:
        除可执行文件名外的命令行参数。若提供，首个值会被视为可选的初始媒体文件路径。
    """

    setup_logging()

    # 在任何 MpvPlayer 实例化之前确保 DLL 搜索路径已就绪。
    _ensure_mpv_on_path(mpv_binary_dir())

    # 只有在 DLL 目录注册完成后再执行 mpv 相关的导入，确保 Windows 上能稳定找到
    # ``libmpv-2.dll``。
    from .core.mpv.player import MpvPlayer

    # Qt 期望获得列表；这里允许调用方传入任意可迭代对象以提高便利性。
    args = list(argv) if argv is not None else sys.argv[1:]
    initial_file = Path(args[0]) if args else None

    app = QApplication(sys.argv[:1])

    player = MpvPlayer()
    window = MainWindow(player=player, initial_file=initial_file)
    window.show()
    return app.exec()
