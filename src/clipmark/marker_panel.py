from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .models import Marker


class MarkerPanel(QWidget):
    """标记管理面板（右侧栏）"""

    seek_requested = pyqtSignal(int)
    generate_commentary_requested = pyqtSignal(Marker)
    markers_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_marker: Marker | None = None
        self._markers: list[Marker] = []

        self.setFixedWidth(380)
        self.setStyleSheet("background-color: #f8f9fa;")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("标记管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        self._build_editor(layout)
        self._build_list(layout)
        self._build_commentary(layout)

        self._apply_styles()

    def _build_editor(self, layout: QVBoxLayout) -> None:
        group = QGroupBox("新建/编辑标记")
        group.setStyleSheet(
            "QGroupBox { font-weight: bold; border: 1px solid #ddd; border-radius: 4px; "
            "margin-top: 8px; padding-top: 16px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }"
        )
        el = QVBoxLayout(group)
        el.setSpacing(6)

        time_row = QHBoxLayout()
        self._start_label = QLabel("起始: 0:00")
        self._start_label.setStyleSheet("color: #555; font-size: 12px;")
        time_row.addWidget(self._start_label)
        self._mark_start_btn = QPushButton("←标记")
        self._mark_start_btn.setFixedWidth(60)
        self._mark_start_btn.clicked.connect(self._mark_start)
        time_row.addWidget(self._mark_start_btn)
        self._end_label = QLabel("结束: 0:00")
        self._end_label.setStyleSheet("color: #555; font-size: 12px;")
        time_row.addWidget(self._end_label)
        self._mark_end_btn = QPushButton("标记→")
        self._mark_end_btn.setFixedWidth(60)
        self._mark_end_btn.clicked.connect(self._mark_end)
        time_row.addWidget(self._mark_end_btn)
        el.addLayout(time_row)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("标记名称（可选）")
        el.addWidget(self._name_input)

        self._notes_input = QPlainTextEdit()
        self._notes_input.setPlaceholderText("备注（用于 AI 生成解说词）")
        self._notes_input.setMaximumHeight(70)
        el.addWidget(self._notes_input)

        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("添加标记")
        self._add_btn.clicked.connect(self._add_marker)
        btn_row.addWidget(self._add_btn)
        self._update_btn = QPushButton("更新")
        self._update_btn.clicked.connect(self._update_marker)
        self._update_btn.setEnabled(False)
        btn_row.addWidget(self._update_btn)
        self._delete_btn = QPushButton("删除")
        self._delete_btn.clicked.connect(self._delete_marker)
        self._delete_btn.setEnabled(False)
        btn_row.addWidget(self._delete_btn)
        el.addLayout(btn_row)

        layout.addWidget(group)

    def _build_list(self, layout: QVBoxLayout) -> None:
        lbl = QLabel("标记列表")
        lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        layout.addWidget(lbl)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["名称", "开始", "结束", "备注"])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().hide()
        self._table.setStyleSheet(
            "QTableWidget { border: 1px solid #ddd; gridline-color: #eee; }"
            "QTableWidget::item { padding: 4px; }"
            "QTableWidget::item:selected { background-color: #cce5ff; }"
        )
        self._table.itemDoubleClicked.connect(self._on_table_double_click)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table, 1)

    def _build_commentary(self, layout: QVBoxLayout) -> None:
        group = QGroupBox("AI 解说词")
        group.setStyleSheet(
            "QGroupBox { font-weight: bold; border: 1px solid #ddd; border-radius: 4px; "
            "margin-top: 8px; padding-top: 16px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }"
        )
        cl = QVBoxLayout(group)
        cl.setSpacing(4)

        self._commentary_view = QPlainTextEdit()
        self._commentary_view.setReadOnly(True)
        self._commentary_view.setPlaceholderText("选择标记后点击「生成解说词」")
        self._commentary_view.setMaximumHeight(100)
        cl.addWidget(self._commentary_view)

        self._gen_btn = QPushButton("生成解说词")
        self._gen_btn.setEnabled(False)
        self._gen_btn.clicked.connect(self._request_commentary)
        cl.addWidget(self._gen_btn)

        layout.addWidget(group)

    def _apply_styles(self) -> None:
        btn_style = (
            "QPushButton { background-color: #4a9eff; color: #fff; border: none; "
            "padding: 6px 12px; border-radius: 4px; font-size: 12px; }"
            "QPushButton:hover { background-color: #3a8eef; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )
        self._add_btn.setStyleSheet(btn_style)
        self._update_btn.setStyleSheet(btn_style)
        del_style = btn_style.replace("#4a9eff", "#e74c3c").replace("#3a8eef", "#c0392b")
        self._delete_btn.setStyleSheet(del_style)
        self._gen_btn.setStyleSheet(btn_style)

        mark_style = (
            "QPushButton { background-color: #555; color: #fff; border: none; "
            "padding: 4px 8px; border-radius: 3px; font-size: 11px; }"
            "QPushButton:hover { background-color: #777; }"
        )
        self._mark_start_btn.setStyleSheet(mark_style)
        self._mark_end_btn.setStyleSheet(mark_style)

    # -- 公开接口 --

    def set_markers(self, markers: list[Marker]) -> None:
        self._markers = markers
        self._refresh_table()

    def get_markers(self) -> list[Marker]:
        return self._markers

    def set_player_time(self, position_ms: int) -> None:
        self._last_position_ms = position_ms

    def update_commentary(self, marker_id: str, text: str) -> None:
        for m in self._markers:
            if m.id == marker_id:
                m.commentary = text
                if self._current_marker and self._current_marker.id == marker_id:
                    self._commentary_view.setPlainText(text)
                break

    def set_generating(self, busy: bool) -> None:
        self._gen_btn.setEnabled(not busy)
        self._gen_btn.setText("生成中…" if busy else "生成解说词")

    # -- 内部 --

    def _mark_start(self) -> None:
        pos = getattr(self, "_last_position_ms", 0)
        seconds = pos / 1000.0
        m = int(seconds // 60)
        s = seconds % 60
        self._start_label.setText(f"起始: {m}:{s:05.2f}")
        self._pending_start = seconds
        self._start_label.setStyleSheet("color: #4a9eff; font-size: 12px;")

    def _mark_end(self) -> None:
        pos = getattr(self, "_last_position_ms", 0)
        seconds = pos / 1000.0
        m = int(seconds // 60)
        s = seconds % 60
        self._end_label.setText(f"结束: {m}:{s:05.2f}")
        self._pending_end = seconds
        self._end_label.setStyleSheet("color: #e74c3c; font-size: 12px;")

    def _clear_pending(self) -> None:
        self._pending_start = 0.0
        self._pending_end = 0.0
        self._start_label.setText("起始: 0:00")
        self._end_label.setText("结束: 0:00")
        self._start_label.setStyleSheet("color: #555; font-size: 12px;")
        self._end_label.setStyleSheet("color: #555; font-size: 12px;")
        self._name_input.clear()
        self._notes_input.clear()

    def _add_marker(self) -> None:
        start = getattr(self, "_pending_start", 0.0)
        end = getattr(self, "_pending_end", 0.0)
        if end <= start:
            end = getattr(self, "_last_position_ms", 0) / 1000.0
            if end <= start:
                end = start + 1.0
        name = self._name_input.text().strip() or f"片段 {len(self._markers) + 1}"
        notes = self._notes_input.toPlainText().strip()
        marker = Marker(name=name, start_time=start, end_time=end, notes=notes)
        self._markers.append(marker)
        self._refresh_table()
        self._clear_pending()
        self.markers_changed.emit()

    def _update_marker(self) -> None:
        if self._current_marker is None:
            return
        m = self._current_marker
        m.name = self._name_input.text().strip() or m.name
        m.notes = self._notes_input.toPlainText().strip()
        m.start_time = getattr(self, "_pending_start", m.start_time)
        m.end_time = getattr(self, "_pending_end", m.end_time)
        self._refresh_table()
        self._clear_edit_state()
        self.markers_changed.emit()

    def _delete_marker(self) -> None:
        if self._current_marker is None:
            return
        self._markers.remove(self._current_marker)
        self._refresh_table()
        self._clear_edit_state()
        self.markers_changed.emit()

    def _clear_edit_state(self) -> None:
        self._current_marker = None
        self._clear_pending()
        self._add_btn.setEnabled(True)
        self._update_btn.setEnabled(False)
        self._delete_btn.setEnabled(False)
        self._gen_btn.setEnabled(False)
        self._commentary_view.clear()

    def _request_commentary(self) -> None:
        if self._current_marker:
            self.generate_commentary_requested.emit(self._current_marker)

    def _refresh_table(self) -> None:
        self._table.setRowCount(len(self._markers))
        for i, m in enumerate(self._markers):
            self._table.setItem(i, 0, QTableWidgetItem(m.name))
            self._table.setItem(i, 1, QTableWidgetItem(self._format_ts(m.start_time)))
            self._table.setItem(i, 2, QTableWidgetItem(self._format_ts(m.end_time)))
            self._table.setItem(i, 3, QTableWidgetItem(m.notes))

    @staticmethod
    def _format_ts(seconds: float) -> str:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}:{s:05.2f}"

    def _on_table_double_click(self, row: int, _col: int) -> None:
        if 0 <= row < len(self._markers):
            pos = int(self._markers[row].start_time * 1000)
            self.seek_requested.emit(pos)

    def _on_selection_changed(self) -> None:
        rows = self._table.selectedIndexes()
        if not rows:
            return
        row = rows[0].row()
        if 0 <= row < len(self._markers):
            m = self._markers[row]
            self._current_marker = m
            self._name_input.setText(m.name)
            self._notes_input.setPlainText(m.notes)
            self._pending_start = m.start_time
            self._pending_end = m.end_time
            self._start_label.setText(f"起始: {int(m.start_time//60)}:{m.start_time%60:05.2f}")
            self._start_label.setStyleSheet("color: #4a9eff; font-size: 12px;")
            self._end_label.setText(f"结束: {int(m.end_time//60)}:{m.end_time%60:05.2f}")
            self._end_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
            self._commentary_view.setPlainText(m.commentary)
            self._add_btn.setEnabled(False)
            self._update_btn.setEnabled(True)
            self._delete_btn.setEnabled(True)
            self._gen_btn.setEnabled(True)
            # 单击选中即跳转到起始时间
            pos = int(m.start_time * 1000)
            self.seek_requested.emit(pos)
