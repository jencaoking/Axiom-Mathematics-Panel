from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QTextEdit, QTextBrowser, QDockWidget
)
from PySide6.QtCore import Signal, Qt

from mathlab.ui.code_editor import MonacoCodeEditor
from mathlab.core.notebook import MathLabNotebook, CellType

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
        
        run_btn = QPushButton("▶ Run")
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

class NotebookPanel(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("MathLab Notebook", parent)
        self.notebook = MathLabNotebook()
        
        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setWidget(self.main_widget)
        
        # Toolbar
        self.toolbar = QWidget()
        t_layout = QHBoxLayout(self.toolbar)
        self.add_code_btn = QPushButton("+ Code")
        self.add_md_btn = QPushButton("+ Markdown")
        
        self.add_code_btn.clicked.connect(lambda: self.add_cell("code"))
        self.add_md_btn.clicked.connect(lambda: self.add_cell("markdown"))
        
        t_layout.addWidget(self.add_code_btn)
        t_layout.addWidget(self.add_md_btn)
        t_layout.addStretch()
        self.layout.addWidget(self.toolbar)
        
        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #1e1e1e; border: none; }")
        
        self.cells_container = QWidget()
        self.cells_container.setStyleSheet("background-color: #1e1e1e;")
        self.cells_layout = QVBoxLayout(self.cells_container)
        self.cells_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.cells_container)
        self.layout.addWidget(self.scroll_area)
        
        self.cell_widgets = {} # id -> widget
        
        # Add an initial cell
        self.add_cell("code", "A = [1 2; 3 4; 5 6]\nsvd(A)")

    def add_cell(self, cell_type="code", content=""):
        ctype = CellType.CODE if cell_type == "code" else CellType.MARKDOWN
        cell = self.notebook.add_cell(ctype, content)
        
        widget = VSCodeStyleCellWidget(cell.id, cell_type, content)
        widget.execute_requested.connect(lambda code, cid=cell.id: self.execute_cell(cid, code))
        
        self.cells_layout.addWidget(widget)
        self.cell_widgets[cell.id] = widget

    def execute_cell(self, cell_id, code):
        # Update notebook core with code
        for c in self.notebook.cells:
            if c.id == cell_id:
                c.content = code
                break
                
        self.notebook.execute_cell(cell_id)
        self.update_cell_output(cell_id)

    def update_cell_output(self, cell_id):
        cell = next((c for c in self.notebook.cells if c.id == cell_id), None)
        if not cell: return
        
        widget = self.cell_widgets.get(cell_id)
        if not widget: return
        
        out_text = ""
        for out in cell.outputs:
            if out["type"] == "error":
                out_text += f"<span style='color:red'>{out['data']}</span><br>"
            elif out["type"] == "result":
                # Format the result nicely
                out_text += f"<pre style='color: #dcdcaa;'>{out['data']}</pre><br>"
            elif out["type"] == "markdown":
                out_text += f"<div style='font-family: sans-serif; padding: 10px;'>{out['data']}</div><br>"
                
        widget.set_output(out_text)
