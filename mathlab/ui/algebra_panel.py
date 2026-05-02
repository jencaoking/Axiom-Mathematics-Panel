"""
Algebra Panel — redesigned with a custom card list:
  • Each entry: coloured dot  +  two-line text (name bold / formula monospace)
  • Selected state: light-blue background (#d3e4fe)
  • Hover state   : lighter background   (#eff4ff)
  • Right-click context menu: Rename / Delete
"""

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QFrame, QMenu, QSizePolicy,
    QApplication
)
from PySide6.QtGui import QAction, QFont, QColor, QPainter, QBrush, QPen, QCursor
from PySide6.QtCore import Signal, Qt, QSize, QPoint

try:
    from ..utils.i18n_manager import t
except ImportError:
    from utils.i18n_manager import t


# ──────────────────────────────────────────────────────────────────────────────
# Colour palette per object type
# ──────────────────────────────────────────────────────────────────────────────

_TYPE_COLORS: dict[str, str] = {
    'Point':   '#004ac6',
    'Segment': '#4b41e1',
    'Circle':  '#4b41e1',
    'Polygon': '#9333ea',
}
_DEFAULT_COLOR = '#737686'


# ──────────────────────────────────────────────────────────────────────────────
# Coloured dot widget (painted)
# ──────────────────────────────────────────────────────────────────────────────

class _ColorDot(QWidget):
    """10×10 filled circle (hollow for Circle type)."""

    def __init__(self, hex_color: str, hollow: bool = False, parent=None):
        super().__init__(parent)
        self.hex_color = hex_color
        self.hollow = hollow
        self.setFixedSize(QSize(12, 12))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(self.hex_color)
        if self.hollow:
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(2, 2, 8, 8)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(1, 1, 10, 10)
        painter.end()


# ──────────────────────────────────────────────────────────────────────────────
# Individual item widget
# ──────────────────────────────────────────────────────────────────────────────

class _AlgebraItem(QFrame):
    """
    A single row in the algebra list.

    Layout:
        [dot]  [name  (bold 14px)    ]
               [formula (mono 12px)  ]
    """

    clicked  = Signal(str)      # obj_id
    rename_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, obj_id: str, obj_data: dict, parent=None):
        super().__init__(parent)
        self.obj_id = obj_id
        self._selected = False

        self.setObjectName("algebra_item")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # ── dot ──────────────────────────────────────────────────────
        obj_type = obj_data.get('type', '')
        hex_col  = _TYPE_COLORS.get(obj_type, _DEFAULT_COLOR)
        hollow   = (obj_type == 'Circle')
        dot = _ColorDot(hex_col, hollow)

        # ── text labels ───────────────────────────────────────────────
        self._name_label = QLabel()
        self._name_label.setObjectName("item_name")

        self._formula_label = QLabel()
        self._formula_label.setObjectName("item_formula")

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)
        text_layout.addWidget(self._name_label)
        text_layout.addWidget(self._formula_label)

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 7, 10, 7)
        row.setSpacing(8)
        row.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        row.addLayout(text_layout, 1)

        self._apply_base_style()
        self.update_data(obj_data)

    # ── data ──────────────────────────────────────────────────────────

    def update_data(self, obj_data: dict):
        self._name_label.setText(obj_data.get('name', ''))
        self._formula_label.setText(AlgebraPanel.format_definition(obj_data))

    # ── selection ─────────────────────────────────────────────────────

    def set_selected(self, selected: bool):
        self._selected = selected
        self._refresh_bg()

    # ── style helpers ─────────────────────────────────────────────────

    def _apply_base_style(self):
        self._name_label.setStyleSheet(
            "QLabel { font-size: 14px; font-weight: 600; color: #1e1e2e; }"
        )
        self._formula_label.setStyleSheet(
            "QLabel {"
            "  font-family: 'Consolas', 'JetBrains Mono', monospace;"
            "  font-size: 12px;"
            "  color: #434655;"
            "}"
        )
        self._refresh_bg()

    def _refresh_bg(self):
        if self._selected:
            bg = "#d3e4fe"
        else:
            bg = "transparent"
        self.setStyleSheet(
            f"QFrame#algebra_item {{ background: {bg}; border-radius: 6px; }}"
            f"QFrame#algebra_item:hover {{ background: {'#d3e4fe' if self._selected else '#eff4ff'}; border-radius: 6px; }}"
        )

    # ── events ────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.obj_id)
        super().mousePressEvent(event)

    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        rename_act = QAction(t('algebra_panel.rename'), self)
        rename_act.triggered.connect(lambda: self.rename_requested.emit(self.obj_id))
        delete_act = QAction(t('algebra_panel.delete'), self)
        delete_act.triggered.connect(lambda: self.delete_requested.emit(self.obj_id))
        menu.addAction(rename_act)
        menu.addAction(delete_act)
        menu.exec(self.mapToGlobal(pos))


# ──────────────────────────────────────────────────────────────────────────────
# Main panel
# ──────────────────────────────────────────────────────────────────────────────

class AlgebraPanel(QDockWidget):
    object_selected = Signal(str)
    object_renamed  = Signal(str, str)
    object_deleted  = Signal(str)

    def __init__(self, parent=None):
        super().__init__(t('algebra_panel.title'), parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setMinimumWidth(200)

        self.object_items: dict[str, _AlgebraItem] = {}
        self._selected_id: str | None = None

        # ── outer container ───────────────────────────────────────────
        outer = QWidget()
        outer.setObjectName("algebra_outer")
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(10, 8, 10, 8)
        outer_layout.setSpacing(0)

        # ── section title ─────────────────────────────────────────────
        self._title_label = QLabel(t('algebra_panel.title').upper())
        self._title_label.setStyleSheet(
            "QLabel {"
            "  font-size: 11px; font-weight: 700;"
            "  color: #737686; letter-spacing: 1px;"
            "  padding: 2px 0 6px 0;"
            "}"
        )
        outer_layout.addWidget(self._title_label)

        # ── divider ───────────────────────────────────────────────────
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setFrameShadow(QFrame.Shadow.Sunken)
        div.setStyleSheet("color: #e0e2ec; margin-bottom: 4px;")
        outer_layout.addWidget(div)

        # ── scroll area ───────────────────────────────────────────────
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._list_widget = QWidget()
        self._list_widget.setObjectName("algebra_list")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(2)
        self._list_layout.addStretch()   # pushes items to top

        self._scroll_area.setWidget(self._list_widget)
        outer_layout.addWidget(self._scroll_area)

        self.setWidget(outer)

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    def add_object(self, obj_data: dict) -> None:
        obj_id = obj_data['id']
        if obj_id in self.object_items:
            self.update_object(obj_data)
            return

        item = _AlgebraItem(obj_id, obj_data)
        item.clicked.connect(self._on_item_clicked)
        item.rename_requested.connect(self._on_rename_requested)
        item.delete_requested.connect(self.object_deleted)

        # insert before the trailing stretch
        count = self._list_layout.count()
        self._list_layout.insertWidget(count - 1, item)
        self.object_items[obj_id] = item

    def update_object(self, obj_data: dict) -> None:
        obj_id = obj_data['id']
        if obj_id in self.object_items:
            self.object_items[obj_id].update_data(obj_data)

    def remove_object(self, obj_id: str) -> None:
        if obj_id in self.object_items:
            item = self.object_items.pop(obj_id)
            self._list_layout.removeWidget(item)
            item.deleteLater()
            if self._selected_id == obj_id:
                self._selected_id = None

    def clear(self) -> None:
        for obj_id in list(self.object_items.keys()):
            self.remove_object(obj_id)
        self._selected_id = None

    def retranslate_ui(self) -> None:
        self.setWindowTitle(t('algebra_panel.title'))
        self._title_label.setText(t('algebra_panel.title').upper())

    # ──────────────────────────────────────────────────────────────────
    # Internal slots
    # ──────────────────────────────────────────────────────────────────

    def _on_item_clicked(self, obj_id: str):
        # deselect previous
        if self._selected_id and self._selected_id in self.object_items:
            self.object_items[self._selected_id].set_selected(False)

        self._selected_id = obj_id
        if obj_id in self.object_items:
            self.object_items[obj_id].set_selected(True)

        self.object_selected.emit(obj_id)

    def _on_rename_requested(self, obj_id: str):
        """
        Inline rename is not straightforward with custom widgets —
        emit object_renamed with an empty new name as a trigger so
        the caller can open a dialog.  The caller is expected to call
        update_object() after the rename completes.
        """
        from PySide6.QtWidgets import QInputDialog
        if obj_id not in self.object_items:
            return
        current_name = self.object_items[obj_id]._name_label.text()
        new_name, ok = QInputDialog.getText(
            self, t('algebra_panel.rename'), "", text=current_name
        )
        if ok and new_name.strip():
            self.object_renamed.emit(obj_id, new_name.strip())

    # ──────────────────────────────────────────────────────────────────
    # Static formula formatter (shared with PropertiesPanel)
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def format_definition(obj_data: dict) -> str:
        obj_type = obj_data.get('type', '')
        coords   = obj_data.get('coordinates', {})
        name     = obj_data.get('name', '?')

        if obj_type == 'Point':
            x = coords.get('x', 0.0)
            y = coords.get('y', 0.0)
            return f"{name} = ({x:.2f}, {y:.2f})"

        elif obj_type == 'Circle':
            cx = coords.get('cx', 0.0)
            cy = coords.get('cy', 0.0)
            r  = coords.get('r', 1.0)
            cx_str  = f"{abs(cx):.2f}"
            cy_str  = f"{abs(cy):.2f}"
            cx_sign = "-" if cx >= 0 else "+"
            cy_sign = "-" if cy >= 0 else "+"
            return (
                f"(x {cx_sign} {cx_str})\u00b2 + "
                f"(y {cy_sign} {cy_str})\u00b2 = r\u00b2"
            )

        elif obj_type == 'Segment':
            x1 = coords.get('x1', 0.0)
            y1 = coords.get('y1', 0.0)
            x2 = coords.get('x2', 0.0)
            y2 = coords.get('y2', 0.0)
            return f"({x1:.2f}, {y1:.2f}) \u2192 ({x2:.2f}, {y2:.2f})"

        elif obj_type == 'Polygon':
            pts = obj_data.get('points', [])
            return f"{len(pts)} vertices"

        else:
            return str(coords)
