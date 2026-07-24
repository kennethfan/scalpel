from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .ai_client import AIClient
from .export_dialog import ExportDialog
from .marker_panel import MarkerPanel
from .models import Marker, Project
from .player import VideoPlayerWidget
from .settings import AISettingsDialog, load_config


class CommentaryWorker(QThread):
    """后台 AI 解说词生成线程，避免阻塞 GUI"""

    finished = pyqtSignal(str, str)  # marker_id, commentary_text
    error = pyqtSignal(str, str)  # marker_id, error_message

    def __init__(
        self, client: AIClient, marker_id: str, notes: str
    ) -> None:
        super().__init__()
        self._client = client
        self._marker_id = marker_id
        self._notes = notes

    def run(self) -> None:
        try:
            text = self._client.generate_commentary(self._notes)
            self.finished.emit(self._marker_id, text)
        except Exception as e:
            self.error.emit(self._marker_id, str(e))


class MainWindow(QMainWindow):
    """ClipMark 主窗口"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ClipMark")
        self.resize(1200, 800)

        self._project: Project | None = None
        self._ai_client: AIClient | None = None
        self._current_commentary_worker: CommentaryWorker | None = None
        self._commentary_marker_name: str = ""
        self._init_ai_client()

        self._setup_menus()
        self._setup_ui()
        self._connect_signals()

    def _init_ai_client(self) -> None:
        config = load_config()
        ai_cfg = config.get("ai", {})
        if ai_cfg.get("endpoint") and ai_cfg.get("api_key"):
            self._ai_client = AIClient(**ai_cfg)

    def _setup_menus(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件(&F)")

        import_action = QAction("导入视频(&I)...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self._import_video)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        save_action = QAction("保存项目(&S)", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)

        open_action = QAction("打开项目(&O)...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        export_action = QAction("批量导出(&E)...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._show_export_dialog)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu("设置(&S)")
        ai_settings_action = QAction("AI 设置(&A)...", self)
        ai_settings_action.triggered.connect(self._show_ai_settings)
        settings_menu.addAction(ai_settings_action)

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 主内容区：播放器 + 标记面板
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        root_layout.addLayout(main_layout, 1)

        # 左侧：视频播放器
        self._player = VideoPlayerWidget()
        main_layout.addWidget(self._player, 1)

        # 右侧：标记面板
        self._marker_panel = MarkerPanel()
        main_layout.addWidget(self._marker_panel)

        # 底部导出栏
        self._setup_export_bar()
        root_layout.addWidget(self._export_bar)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 — 使用文件 → 导入视频开始")

    def _setup_export_bar(self) -> None:
        self._export_bar = QWidget()
        self._export_bar.setFixedHeight(36)
        self._export_bar.setStyleSheet(
            "background-color: #f0f0f0; border-top: 1px solid #ddd;"
        )
        bar_layout = QHBoxLayout(self._export_bar)
        bar_layout.setContentsMargins(12, 2, 12, 2)

        self._export_status_label = QLabel("标记 0 个 | 上次导出: —")
        self._export_status_label.setStyleSheet("color: #555; font-size: 12px;")
        bar_layout.addWidget(self._export_status_label, 1)

        self._export_bar_progress = QProgressBar()
        self._export_bar_progress.setFixedWidth(160)
        self._export_bar_progress.setFixedHeight(16)
        self._export_bar_progress.setRange(0, 100)
        self._export_bar_progress.setValue(0)
        self._export_bar_progress.hide()
        bar_layout.addWidget(self._export_bar_progress)

        self._export_bar_btn = QPushButton("批量导出")
        self._export_bar_btn.setStyleSheet(
            "QPushButton { background-color: #4a9eff; color: #fff; border: none; "
            "padding: 4px 14px; border-radius: 4px; font-size: 12px; }"
            "QPushButton:hover { background-color: #3a8eef; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )
        self._export_bar_btn.clicked.connect(self._show_export_dialog)
        bar_layout.addWidget(self._export_bar_btn)

    def _connect_signals(self) -> None:
        self._player.player.positionChanged.connect(self._on_position_changed)
        self._marker_panel.seek_requested.connect(self._on_seek_requested)
        self._marker_panel.generate_commentary_requested.connect(
            self._on_generate_commentary
        )
        self._marker_panel.markers_changed.connect(self._update_export_bar_status)

    def _on_position_changed(self, position_ms: int) -> None:
        self._marker_panel.set_player_time(position_ms)

    def _on_seek_requested(self, position_ms: int) -> None:
        self._player.player.setPosition(position_ms)
        self._player.play()

    # -- AI 设置 & 解说词 --

    def _show_ai_settings(self) -> None:
        dialog = AISettingsDialog(self)
        if dialog.exec_() and dialog.result:
            self._ai_client = dialog.result
            self.status_bar.showMessage("AI 设置已保存")

    def _on_generate_commentary(self, marker: Marker) -> None:
        if self._ai_client is None or not self._ai_client.is_configured():
            QMessageBox.warning(
                self,
                "AI 未配置",
                "请先在 设置 → AI 设置 中配置 API endpoint 和 key",
            )
            return

        self._marker_panel.set_generating(True)
        self.status_bar.showMessage(f"正在生成解说词: {marker.name}…")

        worker = CommentaryWorker(self._ai_client, marker.id, marker.notes)
        worker.finished.connect(self._on_commentary_finished)
        worker.error.connect(self._on_commentary_error)
        self._current_commentary_worker = worker
        self._commentary_marker_name = marker.name
        worker.start()

    def _on_commentary_finished(self, marker_id: str, text: str) -> None:
        self._marker_panel.update_commentary(marker_id, text)
        self._marker_panel.set_generating(False)
        self._update_export_bar_status()
        self.status_bar.showMessage(f"解说词已生成: {self._commentary_marker_name}")
        self._current_commentary_worker = None

    def _on_commentary_error(self, marker_id: str, msg: str) -> None:
        self._marker_panel.set_generating(False)
        QMessageBox.critical(self, "生成失败", f"解说词生成失败:\n{msg}")
        self.status_bar.showMessage("解说词生成失败")
        self._current_commentary_worker = None

    # -- 底部导出栏 --

    def _update_export_bar_status(self) -> None:
        markers = self._marker_panel.get_markers()
        count = len(markers)
        has_commentary = sum(1 for m in markers if m.commentary)
        self._export_status_label.setText(
            f"标记 {count} 个 | 已生成解说词 {has_commentary} 个"
        )

    # -- 导出 --

    def _show_export_dialog(self) -> None:
        if self._project is None or not self._project.video_paths:
            QMessageBox.information(self, "提示", "请先导入视频")
            return

        markers = self._marker_panel.get_markers()
        if not markers:
            QMessageBox.information(self, "提示", "还没有标记，请先添加标记")
            return

        has_commentary = any(m.commentary for m in markers)
        if not has_commentary:
            QMessageBox.information(
                self, "提示", "请先为标记生成解说词（选中标记 → 生成解说词）"
            )
            return

        dialog = ExportDialog(markers, self._project.video_paths[0], self)
        dialog.exec_()
        self._export_status_label.setText("上次导出: 完成")
        self._update_export_bar_status()

    # -- 视频导入 --
    def _import_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm);;所有文件 (*)",
        )
        if not path:
            return

        # 初始化项目（首次导入时）
        if self._project is None:
            video_name = Path(path).stem
            self._project = Project(name=video_name)

        if path not in self._project.video_paths:
            self._project.video_paths.append(path)

        self._player.load_video(path)
        self.status_bar.showMessage(f"已加载: {path}")

    # -- 项目保存/加载 --
    def _save_project(self) -> None:
        if self._project is None:
            QMessageBox.information(self, "提示", "没有可保存的项目。请先导入视频。")
            return

        # 同步标记数据
        self._project.markers = self._marker_panel.get_markers()

        path, _ = QFileDialog.getSaveFileName(
            self, "保存项目", f"{self._project.name}.json", "JSON (*.json)"
        )
        if not path:
            return

        from .storage import save_project

        save_project(self._project, path)
        self.status_bar.showMessage(f"项目已保存: {path}")

    def _open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "打开项目", "", "JSON (*.json)"
        )
        if not path:
            return

        from .storage import load_project

        self._project = load_project(path)
        title = f"ClipMark — {self._project.name}"
        self.setWindowTitle(title)
        self._marker_panel.set_markers(self._project.markers)

        # 自动加载第一个视频
        if self._project.video_paths:
            first = self._project.video_paths[0]
            if Path(first).exists():
                self._player.load_video(first)
                self.status_bar.showMessage(f"已加载项目: {path}")
            else:
                self.status_bar.showMessage(
                    f"项目已加载，但视频文件不存在: {first}"
                )
        else:
            self.status_bar.showMessage(f"项目已加载: {path}")


def run() -> None:
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
