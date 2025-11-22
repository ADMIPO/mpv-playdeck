"""Application bootstrap utilities.

This module owns QApplication creation and early process setup, such as ensuring
libmpv's DLL directory is discoverable on Windows before the mpv bindings are
imported. UI components should be created here and passed any required
dependencies.
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
    """Add the mpv DLL directory to the search path on Windows.

    This function must run before importing any module that loads ``libmpv-2.dll``.
    Users need to place the DLL in ``third_party/mpv`` (relative to project root)
    or adjust the path accordingly. If the DLL cannot be found at runtime, mpv
    initialization will fail with a clear error message.
    """

    if os.name != "nt":
        return

    if not mpv_dir.exists():
        _LOGGER.warning("Expected mpv directory does not exist: %s", mpv_dir)

    # os.add_dll_directory is available on Python 3.8+ and is the recommended
    # way to influence DLL search order for the current process.
    os.add_dll_directory(str(mpv_dir))

    # Also prepend to PATH so child processes (if any) inherit the location.
    current_path = os.environ.get("PATH", "")
    path_parts = current_path.split(os.pathsep) if current_path else []
    if str(mpv_dir) not in path_parts:
        os.environ["PATH"] = str(mpv_dir) + os.pathsep + current_path


def run(argv: Optional[Iterable[str]] = None) -> int:
    """Create and run the Qt application.

    Parameters
    ----------
    argv:
        Command-line arguments excluding the executable name. When provided, the
        first value is treated as an optional initial media file path.
    """

    setup_logging()

    # Ensure DLL search path is ready before any MpvPlayer instantiation.
    _ensure_mpv_on_path(mpv_binary_dir())

    # Perform mpv-related imports only after the DLL directory has been
    # registered so that ``libmpv-2.dll`` can be found reliably on Windows.
    from .core.mpv.player import MpvPlayer

    # Qt expects a list; allow caller to pass any iterable for convenience.
    args = list(argv) if argv is not None else sys.argv[1:]
    initial_file = Path(args[0]) if args else None

    app = QApplication(sys.argv[:1])

    player = MpvPlayer()
    window = MainWindow(player=player, initial_file=initial_file)
    window.show()
    return app.exec()
