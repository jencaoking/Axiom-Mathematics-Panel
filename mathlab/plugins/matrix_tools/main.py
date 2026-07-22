# mathlab/plugins/matrix_tools/main.py
from mathlab.core.plugin_base import MathLabPlugin
from mathlab.core.extension_api import MathLabAPI
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from mathlab.utils.i18n_manager import t


class MatrixPanelWidget(QWidget):
    def __init__(self, api: MathLabAPI, parent=None):
        super().__init__(parent)
        self.api = api
        layout = QVBoxLayout(self)

        self.label = QLabel("矩阵工具插件面板")
        self.label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px; color: #ffffff;")
        layout.addWidget(self.label)

        self.btn_inject = QPushButton("注入 3x3 单位矩阵 (I3)")
        self.btn_inject.setStyleSheet("""
            QPushButton {
                background-color: #2b579a;
                color: white;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #1e3f7a;
            }
        """)
        self.btn_inject.clicked.connect(self.inject_matrix)
        layout.addWidget(self.btn_inject)

        layout.addStretch()

    def inject_matrix(self):
        self.api.execute_script("import numpy as np; I3 = np.eye(3)")
        self.api.print_to_console("已在 REPL 环境中注入变量: I3 (3x3 单位矩阵)")


class MatrixToolsPlugin(MathLabPlugin):
    name = "Matrix Extension"
    version = "1.0.0"
    author = "Antigravity Team"
    description = "Provides advanced matrix manipulation commands."

    def __init__(self):
        self.api = None
        self.widget = None

    def on_activate(self, api: MathLabAPI):
        self.api = api

        # 1. 注册一个向控制台注入单位矩阵的命令
        api.register_command(
            id="matrix.inject_identity",
            title="生成 3x3 单位矩阵 (Identity Matrix)",
            action=self._inject_identity_matrix,
            category="线性代数",
        )

        # 2. 注册并添加侧边栏面板
        self.widget = MatrixPanelWidget(api)
        api.add_sidebar_panel(t("plugins.matrix"), self.widget)

        api.print_to_console(
            "[Matrix Extension] Plugin successfully loaded and activated!",
            color_or_level="info",
        )

    def _inject_identity_matrix(self):
        """执行命令注入逻辑"""
        self.api.execute_script("import numpy as np; I3 = np.eye(3)")
        self.api.print_to_console("已在 REPL 环境中注入变量: I3 (3x3 单位矩阵)")

    def on_deactivate(self):
        print("Matrix Extension 正在卸载...")
