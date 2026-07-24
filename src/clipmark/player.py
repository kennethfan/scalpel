from __future__ import annotations

import math

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def _format_time(seconds: float) -> str:
    """将秒数格式化为 MM:SS 或 HH:MM:SS"""
    if seconds < 0:
        seconds = 0
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class VideoPlayerWidget(QWidget):
    """视频播放器控件"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._player = QMediaPlayer(self)
        self._video_widget = QVideoWidget(self)
        self._player.setVideoOutput(self._video_widget)

        self._is_dragging = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        self.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- 视频显示区域 ---
        self._video_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._video_widget.setStyleSheet("background-color: #000;")
        layout.addWidget(self._video_widget, 1)

        # --- 控制栏 ---
        controls = QWidget()
        controls.setStyleSheet(
            "background-color: #2d2d2d; padding: 4px 8px;"
        )
        ctrl_layout = QHBoxLayout(controls)
        ctrl_layout.setContentsMargins(4, 4, 4, 4)
        ctrl_layout.setSpacing(8)

        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedWidth(32)
        self._play_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #fff; border: none; font-size: 14px; }"
            "QPushButton:hover { color: #4a9eff; }"
        )
        ctrl_layout.addWidget(self._play_btn)

        self._time_label = QLabel("0:00 / 0:00")
        self._time_label.setStyleSheet("color: #ccc; font-size: 12px;")
        ctrl_layout.addWidget(self._time_label)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 0)
        self._slider.setStyleSheet(
            "QSlider::groove:horizontal { height: 4px; background: #555; border-radius: 2px; }"
            "QSlider::handle:horizontal { background: #4a9eff; width: 12px; margin: -4px 0; border-radius: 6px; }"
            "QSlider::sub-page:horizontal { background: #4a9eff; border-radius: 2px; }"
        )
        ctrl_layout.addWidget(self._slider, 1)

        ctrl_layout.addStretch()
        layout.addWidget(controls)

        # --- 空闲提示（无视频时） ---
        self._placeholder = QLabel("拖入视频文件或点击文件 → 导入视频")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet("color: #666; font-size: 16px;")
        layout.addWidget(self._placeholder)

    def _connect_signals(self) -> None:
        self._play_btn.clicked.connect(self._toggle_play)
        self._player.stateChanged.connect(self._on_state_changed)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.error.connect(self._on_error)
        self._slider.sliderPressed.connect(self._on_slider_pressed)
        self._slider.sliderReleased.connect(self._on_slider_released)

    def load_video(self, path: str) -> None:
        """加载视频文件"""
        url = QUrl.fromLocalFile(path)
        self._player.setMedia(QMediaContent(url))
        self._placeholder.hide()

    def play(self) -> None:
        self._player.play()

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self._player.stop()

    def _toggle_play(self) -> None:
        if self._player.state() == QMediaPlayer.State.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _on_state_changed(self, state: QMediaPlayer.State) -> None:
        if state == QMediaPlayer.State.PlayingState:
            self._play_btn.setText("⏸")
        else:
            self._play_btn.setText("▶")

    def _on_position_changed(self, position_ms: int) -> None:
        if not self._is_dragging:
            self._slider.blockSignals(True)
            self._slider.setValue(position_ms)
            self._slider.blockSignals(False)
        self._update_time_label(position_ms)

    def _on_duration_changed(self, duration_ms: int) -> None:
        self._slider.setRange(0, duration_ms)

    def _on_error(self, error: QMediaPlayer.Error) -> None:
        if error != QMediaPlayer.Error.NoError:
            self._placeholder.setText(f"播放错误: {self._player.errorString()}")
            self._placeholder.show()

    def _on_slider_pressed(self) -> None:
        self._is_dragging = True

    def _on_slider_released(self) -> None:
        self._is_dragging = False
        self._player.setPosition(self._slider.value())

    def _update_time_label(self, position_ms: int) -> None:
        current = _format_time(position_ms / 1000.0)
        total = _format_time(self._player.duration() / 1000.0)
        self._time_label.setText(f"{current} / {total}")

    # -- 公开属性 --
    @property
    def player(self) -> QMediaPlayer:
        return self._player
