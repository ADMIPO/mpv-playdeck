"""将 mpv 输出绑定到 Qt 视频区域的基础主窗口。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ...core.mpv.player import MpvPlayer
from ...core.models.playback_state import PlaybackState


class MainWindow(QMainWindow):
    """拥有 mpv 渲染表面的最简播放窗口。"""

    def __init__(self, player: MpvPlayer, initial_file: Optional[Path] = None) -> None:
        super().__init__()
        self._player = player
        self._state: PlaybackState = self._player.get_state()
        self._initial_file = initial_file
        self._player_attached = False
        self._default_volume = 50
        self._progress_dragging = False

        self._video_surface = QWidget(self)
        self._video_surface.setStyleSheet("background-color: #000;")
        self._video_surface.setMinimumSize(640, 360)

        self._play_pause_button = QPushButton("播放", self)
        self._play_pause_button.clicked.connect(self.on_play_pause_clicked)

        self._volume_label = QLabel("音量", self)
        self._volume_slider = QSlider(Qt.Horizontal, self)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(self._default_volume)
        self._volume_slider.valueChanged.connect(self.on_volume_changed)
        self._player.set_volume(self._default_volume)

        self._progress_slider = QSlider(Qt.Horizontal, self)
        self._progress_slider.setEnabled(False)
        self._progress_slider.sliderPressed.connect(self.on_progress_pressed)
        self._progress_slider.sliderReleased.connect(self.on_progress_released)
        self._progress_slider.sliderMoved.connect(self.on_progress_moved)

        self._time_label = QLabel("00:00:00 / 00:00:00", self)

        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self._progress_slider, stretch=1)
        progress_layout.addWidget(self._time_label)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self._play_pause_button)
        controls_layout.addStretch()
        controls_layout.addWidget(self._volume_label)
        controls_layout.addWidget(self._volume_slider)

        layout = QVBoxLayout()
        layout.addWidget(self._video_surface, stretch=1)
        layout.addLayout(progress_layout)
        layout.addLayout(controls_layout)

        container = QWidget(self)
        container.setLayout(layout)
        self.setCentralWidget(container)

        file_menu = self.menuBar().addMenu("文件(&F)")
        open_action = QAction("打开文件…", self)
        open_action.triggered.connect(self.on_open_clicked)
        file_menu.addAction(open_action)
        exit_action = QAction("退出...", self)
        exit_action.triggered.connect(self.on_exit_triggered)
        file_menu.addAction(exit_action)

        self.setWindowTitle("mpv player")
        self.resize(800, 600)

        self._state.position_changed.connect(self.on_position_changed)
        self._state.duration_changed.connect(self.on_duration_changed)
        self._set_progress_range(self._state.duration)
        self._update_time_label(position=self._state.position, duration=self._state.duration)

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
        media_filter = (
            "音视频文件 (*.mp4 *.mkv *.mov *.avi *.mp3 *.flac *.wav *.ogg *.m4a)"
        )
        file_path, _ = QFileDialog.getOpenFileName(self, "选择媒体文件", "", media_filter)
        if file_path:
            self._open_media(Path(file_path))

    def on_play_pause_clicked(self) -> None:
        self._player.toggle_pause()
        self._update_play_pause_text()

    def on_volume_changed(self, value: int) -> None:
        self._player.set_volume(value)

    def on_exit_triggered(self) -> None:
        self.close()

    def _open_media(self, path: Path) -> None:
        if not path.exists():
            QMessageBox.warning(self, "无法打开文件", f"文件不存在：{path}")
            return
        if not self._player_attached:
            self._attach_player()
        self._reset_progress()
        self._player.open_file(path)
        self._update_play_pause_text()

    def _update_play_pause_text(self) -> None:
        if self._player.is_paused():
            self._play_pause_button.setText("播放")
        else:
            self._play_pause_button.setText("暂停")

    def on_position_changed(self, position: float) -> None:
        if self._progress_dragging:
            return
        self._set_progress_value(position)
        self._update_time_label(position=position)

    def on_duration_changed(self, duration: float | None) -> None:
        self._set_progress_range(duration)
        self._update_time_label(duration=duration)

    def on_progress_pressed(self) -> None:
        self._progress_dragging = True

    def on_progress_moved(self, value: int) -> None:
        self._update_time_label(position=self._slider_to_seconds(value))

    def on_progress_released(self) -> None:
        target_seconds = self._slider_to_seconds(self._progress_slider.value())
        self._player.seek(target_seconds)
        self._progress_dragging = False
        self._update_time_label(position=target_seconds)

    def _reset_progress(self) -> None:
        self._progress_dragging = False
        self._progress_slider.setEnabled(False)
        self._progress_slider.setRange(0, 0)
        self._progress_slider.setValue(0)
        self._update_time_label(position=0.0, duration=None)

    def _set_progress_range(self, duration: float | None) -> None:
        if duration and duration > 0:
            max_value = int(duration)
            self._progress_slider.setRange(0, max_value)
            self._progress_slider.setEnabled(True)
        else:
            self._progress_slider.setRange(0, 0)
            self._progress_slider.setEnabled(False)

    def _set_progress_value(self, position: float) -> None:
        if not self._progress_slider.isEnabled():
            return
        max_value = self._progress_slider.maximum()
        clamped_value = max(0, min(int(position), max_value)) if max_value > 0 else 0
        self._progress_slider.setValue(clamped_value)

    def _slider_to_seconds(self, value: int) -> float:
        return float(value)

    def _format_time(self, seconds: float | None) -> str:
        if seconds is None or seconds < 0:
            return "--:--:--"
        total_seconds = int(seconds)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _update_time_label(
        self, *, position: float | None = None, duration: float | None = None
    ) -> None:
        position_seconds = position if position is not None else self._state.position
        duration_seconds = duration if duration is not None else self._state.duration
        position_text = self._format_time(position_seconds)
        duration_text = self._format_time(duration_seconds)
        self._time_label.setText(f"{position_text} / {duration_text}")
