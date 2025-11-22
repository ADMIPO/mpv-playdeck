"""用于解析关键文件系统路径的辅助方法。

本模块不依赖任何 Qt 导入，旨在在 core 与 UI 层之间复用。所有路径都以已安装的包位置为
基准进行计算，因此无论从源码运行还是安装后的 wheel，都能保持稳健。
"""

from __future__ import annotations

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
THIRD_PARTY_DIR = PROJECT_ROOT / "third_party"
MPV_DIR = THIRD_PARTY_DIR / "mpv"


def project_root() -> Path:
    """返回仓库根目录的绝对路径。"""

    return PROJECT_ROOT


def third_party_dir() -> Path:
    """返回 ``third_party`` 目录的绝对路径。"""

    return THIRD_PARTY_DIR


def mpv_binary_dir() -> Path:
    """返回预期存放 ``libmpv-2.dll`` 的目录。

    在 Windows 上需要在导入 :mod:`mpv` 绑定前，将该目录加入 DLL 搜索路径。调用方需要
    确保 DLL 确实存在于此目录中。
    """

    return MPV_DIR
