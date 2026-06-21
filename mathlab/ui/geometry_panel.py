from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup
from PySide6.QtCore import Qt

from mathlab.ui.geogebra_canvas import GeoGebraCanvas, ToolMode

class GeometryPanel(QWidget):
    """几何引擎的完整 UI 容器：顶部工具栏 + 底部画布"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # ── 1. 创建顶部工具栏 ──
        self.toolbar = QWidget()
        self.toolbar.setFixedHeight(45)
        self.toolbar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #1e1e1e;")
        tb_layout = QHBoxLayout(self.toolbar)
        tb_layout.setContentsMargins(10, 0, 10, 0)
        tb_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 使用 QButtonGroup 保证同一时间只能选中一个工具
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        # 工具定义
        tools = [
            ("👆 移动", ToolMode.SELECT),
            ("⏺ 自由点", ToolMode.POINT),
            ("📏 直线/线段", ToolMode.LINE),
            ("❌ 找交点", ToolMode.INTERSECT)
        ]

        for text, mode in tools:
            btn = QPushButton(text)
            btn.setCheckable(True) # 按钮变成可按下的拨动开关状态
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background: transparent; color: #d4d4d4; border: none; padding: 6px 12px; border-radius: 4px; }
                QPushButton:checked { background: #007acc; color: white; font-weight: bold; }
                QPushButton:hover:!checked { background: #3c3c3c; }
            """)
            
            # 将按钮的点击信号映射到画布的状态切换
            btn.clicked.connect(lambda checked, m=mode: self.canvas.set_tool_mode(m))
            
            self.btn_group.addButton(btn)
            tb_layout.addWidget(btn)

        # 默认选中“移动”工具
        self.btn_group.buttons()[0].setChecked(True)

        # ── 2. 挂载画板 ──
        self.canvas = GeoGebraCanvas(self)

        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)
