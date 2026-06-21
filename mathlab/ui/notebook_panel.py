from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QTextEdit, QTextBrowser, QDockWidget, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal, Qt

from mathlab.ui.code_editor import MonacoCodeEditor
from mathlab.core.notebook import MathLabNotebook, CellType
from mathlab.utils.i18n_manager import t
import numpy as np

class VSCodeStyleCellWidget(QFrame):
    execute_requested = Signal(str)

    def __init__(self, cell_id, cell_type="code", content="", parent=None):
        super().__init__(parent)
        self.cell_id = cell_id
        self.cell_type = cell_type
        
        # UI Styling
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            VSCodeStyleCellWidget {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                margin-bottom: 10px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 4px 10px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)

        self.init_ui(content)

    def init_ui(self, initial_content):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # Toolbar
        self.toolbar_container = QWidget()
        toolbar_layout = QHBoxLayout(self.toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        type_label = QLabel(f"[{self.cell_type.upper()}]")
        type_label.setStyleSheet("color: #cccccc;")
        toolbar_layout.addWidget(type_label)
        
        toolbar_layout.addStretch()
        
        run_btn = QPushButton(t("notebook.run"))
        run_btn.clicked.connect(self.on_run_clicked)
        toolbar_layout.addWidget(run_btn)

        # Editor
        if self.cell_type == "code":
            self.input_editor = MonacoCodeEditor(initial_text=initial_content)
            self.input_editor.setFixedHeight(150)
            self.input_editor.execute_requested.connect(self.on_monaco_run)
        else:
            self.input_editor = QTextEdit(initial_content)
            self.input_editor.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c;")
            self.input_editor.setFixedHeight(100)

        # Output browser
        self.output_browser = QTextBrowser()
        self.output_browser.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; border: none; font-family: Consolas;")
        self.output_browser.hide()

        self.main_layout.addWidget(self.toolbar_container)
        self.main_layout.addWidget(self.input_editor)
        self.main_layout.addWidget(self.output_browser)

    def on_monaco_run(self, code: str):
        self.execute_requested.emit(code)

    def on_run_clicked(self):
        if self.cell_type == "code":
            self.input_editor.get_text(self.execute_requested.emit)
        else:
            self.execute_requested.emit(self.input_editor.toPlainText())

    def set_output(self, text):
        if not text:
            self.output_browser.hide()
        else:
            self.output_browser.setHtml(text)
            self.output_browser.show()

class NotebookPanel(QWidget):
    """
    交互式笔记本的宏观容器
    负责管理多个 Cell 的 UI 排列，并与底层的 MathLabNotebook 保持数据同步
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.backend = MathLabNotebook()
        self.ui_cells = {}
        
        self.init_ui()
        self.add_new_cell(CellType.CODE)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── 1. 顶部全局工具栏 ──
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(40)
        self.toolbar.setStyleSheet("background-color: #252526; border-bottom: 1px solid #333;")
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)

        self.btn_add_code = self._create_toolbar_btn("+ 代码", "#007acc")
        self.btn_add_markdown = self._create_toolbar_btn("+ 文本", "#608b4e")
        self.btn_run_all = self._create_toolbar_btn("▶ 运行全部", "#c586c0")
        self.btn_clear_all = self._create_toolbar_btn("清空输出", "#858585")

        toolbar_layout.addWidget(self.btn_add_code)
        toolbar_layout.addWidget(self.btn_add_markdown)
        toolbar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        toolbar_layout.addWidget(self.btn_run_all)
        toolbar_layout.addWidget(self.btn_clear_all)

        self.btn_add_code.clicked.connect(lambda: self.add_new_cell(CellType.CODE))
        self.btn_add_markdown.clicked.connect(lambda: self.add_new_cell(CellType.MARKDOWN))
        self.btn_run_all.clicked.connect(self.run_all_cells)
        self.btn_clear_all.clicked.connect(self.clear_all_outputs)

        # ── 2. 可滚动的画布区域 ──
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #1e1e1e; }")
        
        self.canvas_widget = QWidget()
        self.canvas_widget.setStyleSheet("background-color: #1e1e1e;")
        self.canvas_layout = QVBoxLayout(self.canvas_widget)
        self.canvas_layout.setContentsMargins(40, 20, 40, 40)
        self.canvas_layout.setSpacing(15)
        self.canvas_layout.addStretch(1)

        self.scroll_area.setWidget(self.canvas_widget)

        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.scroll_area)

    def _create_toolbar_btn(self, text, hover_color):
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: #cccccc; border: none; padding: 6px 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #333333; color: {hover_color}; border-radius: 4px; }}
        """)
        btn.setCursor(Qt.PointingHandCursor)
        return btn

    def add_new_cell(self, cell_type: CellType):
        backend_cell = self.backend.add_cell(cell_type, "")
        ctype_str = "code" if cell_type == CellType.CODE else "markdown"
        ui_cell = VSCodeStyleCellWidget(backend_cell.id, ctype_str, "")
        
        ui_cell.execute_requested.connect(lambda code, cid=backend_cell.id: self.execute_single_cell(cid, code))
        
        self.ui_cells[backend_cell.id] = ui_cell
        self.canvas_layout.insertWidget(self.canvas_layout.count() - 1, ui_cell)

    def delete_cell(self, cell_id: str):
        if cell_id in self.ui_cells:
            ui_cell = self.ui_cells.pop(cell_id)
            self.canvas_layout.removeWidget(ui_cell)
            ui_cell.deleteLater()
        self.backend.remove_cell(cell_id)

    def execute_single_cell(self, cell_id: str, current_code: str):
        for backend_cell in self.backend.cells:
            if backend_cell.id == cell_id:
                backend_cell.content = current_code
                break

        self.backend.execute_cell(cell_id)
        self._render_cell_output(cell_id)

    def run_all_cells(self):
        # Monaco editor async fetch omitted for brevity, just execute backend cells directly
        self.backend.execute_all()
        for backend_cell in self.backend.cells:
            self._render_cell_output(backend_cell.id)

    def clear_all_outputs(self):
        for cell_id, ui_cell in self.ui_cells.items():
            ui_cell.output_browser.clear()
            ui_cell.output_browser.hide()

    def _render_cell_output(self, cell_id: str):
        backend_cell = next((c for c in self.backend.cells if c.id == cell_id), None)
        ui_cell = self.ui_cells.get(cell_id)
        
        if not backend_cell or not ui_cell: return

        if not backend_cell.outputs:
            ui_cell.output_browser.hide()
            return

        html_output = ""
        for out in backend_cell.outputs:
            if out["type"] == "error":
                html_output += f"<div style='color: #f14c4c; padding: 5px;'><b>错误:</b> {out['data']}</div>"
            elif out["type"] == "result":
                html_output += self._format_data_to_html(out["data"])
            elif out["type"] == "markdown":
                html_output += f"<div style='color: #d4d4d4;'>{out['data']}</div>"

        exec_count = backend_cell.execution_count or "*"
        prefix = f"<div style='color: #569cd6; font-size: 10px; margin-bottom: 4px;'>Out [{exec_count}]:</div>"

        ui_cell.set_output(prefix + html_output)
        ui_cell.output_browser.show()

    def _format_data_to_html(self, result) -> str:
        if isinstance(result, np.ndarray):
            return f"<span style='color: #4EC9B0;'>[NumPy Array Shape: {result.shape}]</span><br>"
        elif isinstance(result, dict):
            return "<span style='color: #9cdcfe;'>[Dictionary Result]</span><br>"
        return f"<span style='color: #b5cea8;'>{result}</span><br>"
