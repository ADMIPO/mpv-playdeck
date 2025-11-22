"""Basic main window that wires mpv into a Qt video surface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core.mpv.player import MpvPlayer


class MainWindow(QMainWindow):
    """Minimal playable window with an mpv-backed video surface."""

    def __init__(self, player: MpvPlayer, initial_file: Optional[Path] = None) -> None:
        super().__init__()
        self._player = player
        self._initial_file = initial_file
        self._player_attached = False

        self._video_surface = QWidget(self)
        self._video_surface.setStyleSheet("background-color: #000;")
        self._video_surface.setMinimumSize(640, 360)

        self._status_label = QLabel("Drop a file or use Open to start playing.", self)
        self._open_button = QPushButton("Open File…", self)
        self._open_button.clicked.connect(self.on_open_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self._video_surface, stretch=1)
        layout.addWidget(self._status_label)
        layout.addWidget(self._open_button, alignment=Qt.AlignRight)

        container = QWidget(self)
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setWindowTitle("mpv-playdeck (minimal)")
        self.resize(800, 600)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if not self._player_attached:
            self._attach_player()
        if self._initial_file:
            self._open_media(self._initial_file)
            self._initial_file = None

    def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        self._player.shutdown()
        event.accept()

    def _attach_player(self) -> None:
        wid = int(self._video_surface.winId())
        self._player.set_render_target(wid)
        self._player_attached = True

    def on_open_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open media file", "", "Media files (*.mp4 *.mkv *.mp3 *.flac *.*)"
        )
        if file_path:
            self._open_media(Path(file_path))

    def _open_media(self, path: Path) -> None:
        if not path.exists():
            QMessageBox.warning(self, "File not found", f"{path} does not exist.")
            return
        if not self._player_attached:
            self._attach_player()
        self._player.open_file(path)
        self._status_label.setText(f"Playing: {path.name}")
