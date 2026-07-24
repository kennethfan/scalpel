from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .exporter import composite_audio_video, cut_video
from .models import Marker
from .tts import synthesize


class ExportWorker(QThread):
    progress = pyqtSignal(int, int, str)  # current, total, status
    finished_one = pyqtSignal(int, str)  # index, output_path
    error = pyqtSignal(str)
    done = pyqtSignal()

    def __init__(
        self,
        markers: list[Marker],
        video_path: str,
        output_dir: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
    ) -> None:
        super().__init__()
        self._markers = markers
        self._video_path = video_path
        self._output_dir = Path(output_dir)
        self._voice = voice
        self._cancelled = False

    def run(self) -> None:
        total = len(self._markers)
        for i, marker in enumerate(self._markers):
            if self._cancelled:
                break
            try:
                self._export_one(i, total, marker)
            except Exception as e:
                self.error.emit(f"[{marker.name}] {e}")
                continue
        self.done.emit()

    def cancel(self) -> None:
        self._cancelled = True

    def _export_one(self, index: int, total: int, marker: Marker) -> None:
        name_safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in marker.name)
        idx = f"{index + 1:02d}"

        self.progress.emit(index, total, f"[{idx}/{total}] {marker.name}: TTS 合成…")
        # 1. TTS
        if not marker.commentary:
            raise RuntimeError("标记没有解说词，请先生成")
        audio_path = str(
            Path(tempfile.gettempdir()) / "clipmark" / f"tts_{marker.id}.mp3"
        )
        synthesize(marker.commentary, audio_path, voice=self._voice)

        self.progress.emit(index, total, f"[{idx}/{total}] {marker.name}: 裁剪视频…")
        # 2. 裁剪视频
        clip_path = str(
            Path(tempfile.gettempdir()) / "clipmark" / f"clip_{marker.id}.mp4"
        )
        cut_video(self._video_path, marker.start_time, marker.end_time, clip_path)

        self.progress.emit(index, total, f"[{idx}/{total}] {marker.name}: 合成输出…")
        # 3. 合成
        output_path = str(self._output_dir / f"{idx}_{name_safe}.mp4")
        composite_audio_video(clip_path, audio_path, output_path)

        self.finished_one.emit(index, output_path)


class ExportDialog(QDialog):
    def __init__(
        self,
        markers: list[Marker],
        video_path: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("批量导出")
        self.setMinimumWidth(500)

        self._markers = markers
        self._video_path = video_path
        self._worker: ExportWorker | None = None

        layout = QVBoxLayout(self)

        # 输出目录
        dir_group = QGroupBox("输出目录")
        dl = QHBoxLayout(dir_group)
        self._dir_input = QLineEdit(str(Path.home() / "Desktop" / "ClipMark 导出"))
        dl.addWidget(self._dir_input, 1)
        browse_btn = QPushButton("浏览…")
        browse_btn.clicked.connect(self._browse_dir)
        dl.addWidget(browse_btn)
        layout.addWidget(dir_group)

        # 进度
        self._status_label = QLabel("就绪")
        layout.addWidget(self._status_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, len(markers))
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(150)
        layout.addWidget(self._log)

        # 按钮
        btn_row = QHBoxLayout()
        self._export_btn = QPushButton("开始导出")
        self._export_btn.clicked.connect(self._start_export)
        btn_row.addWidget(self._export_btn)

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self._cancel_export)
        self._cancel_btn.setEnabled(False)
        btn_row.addWidget(self._cancel_btn)

        self._open_btn = QPushButton("打开输出目录")
        self._open_btn.clicked.connect(self._open_output)
        self._open_btn.setEnabled(False)
        btn_row.addWidget(self._open_btn)

        layout.addLayout(btn_row)

    def _browse_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self._dir_input.setText(path)

    def _start_export(self) -> None:
        output_dir = self._dir_input.text().strip()
        if not output_dir:
            return

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        self._worker = ExportWorker(
            self._markers, self._video_path, output_dir
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_one.connect(self._on_finished_one)
        self._worker.error.connect(self._on_error)
        self._worker.done.connect(self._on_done)

        self._export_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._log.clear()

        self._worker.start()

    def _cancel_export(self) -> None:
        if self._worker:
            self._worker.cancel()
            self._cancel_btn.setEnabled(False)
            self._log.append("⏹ 用户取消导出")

    def _on_progress(self, current: int, total: int, status: str) -> None:
        self._status_label.setText(status)
        self._progress_bar.setValue(current)
        self._log.append(status)

    def _on_finished_one(self, index: int, output_path: str) -> None:
        self._log.append(f"✅ 已完成: {Path(output_path).name}")
        self._progress_bar.setValue(index + 1)

    def _on_error(self, msg: str) -> None:
        self._log.append(f"❌ {msg}")

    def _on_done(self) -> None:
        self._export_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._open_btn.setEnabled(True)
        self._status_label.setText("导出完成")
        self._log.append("🎉 全部导出完成")

    def _open_output(self) -> None:
        path = self._dir_input.text().strip()
        if Path(path).exists():
            import subprocess
            subprocess.run(["open", path])
