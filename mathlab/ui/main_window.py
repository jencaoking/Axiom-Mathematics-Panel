from mathlab.core.prompt_manager import prompt_manager
import os
import uuid
import platform
import subprocess

from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QToolButton,
    QMenuBar, QMenu, QDockWidget, QStatusBar,
    QFileDialog, QMessageBox, QDialog, QVBoxLayout,
    QLabel, QComboBox, QPushButton, QHBoxLayout,
    QSpacerItem, QSizePolicy, QTabWidget
)
from PySide6.QtGui import QAction, QPainter as QtPainter, QShortcut, QKeySequence, QIcon
from PySide6.QtCore import Qt, QSize
from PySide6.QtSvg import QSvgGenerator

from .canvas import GeometryCanvas
from .algebra_panel import AlgebraPanel
from .console import PythonConsole
from .properties_panel import PropertiesPanel
from .command_bar import CommandBar, CommandPalette
from .algo_vis_panel import AlgoVisPanel
from .ai_tools_panel import AIToolsPanel
from .function_explorer_panel import FunctionExplorerPanel
from .signal_lab_panel import SignalLabPanel
from .fractal_gpu_panel import FractalGPUExplorer
from .animations import fade_in, fade_out
from .math_console import MathConsole
from .notebook_panel import NotebookPanel
from .omni_bar import OmniBar

# ── JupyterLab 嵌入组件（软依赖：WebEngine 不存在时降级为占位面板） ──────────
try:
    from .jupyter_panel import JupyterPanel
    from core.jupyter_manager import JupyterManager
except ImportError:
    try:
        from .jupyter_panel import JupyterPanel
        from ..core.jupyter_manager import JupyterManager
    except ImportError:
        JupyterPanel = None
        JupyterManager = None

try:
    from core.geometry_engine import GeometryEngine
    from core.python_repl import PythonREPL
    from core.ai_manager import AIManager
    from core.cas_provider import CASProvider
    from core.async_workers import TaskManager, AIFitWorker, AIClusterWorker, AIRecognizeWorker, AIGeneratePointsWorker
    from core.command_manager import CommandManager, Command
    from core.ipc_server import JupyterIPCServer
    from core.ipc_client import JupyterIPCClient
    from core.error_manager import AutoSaver
except ImportError:
    from ..core.geometry_engine import GeometryEngine
    from ..core.python_repl import PythonREPL
    from ..core.ai_manager import AIManager
    from ..core.cas_provider import CASProvider
    from ..core.async_workers import TaskManager, AIFitWorker, AIClusterWorker, AIRecognizeWorker, AIGeneratePointsWorker
    from ..core.command_manager import CommandManager, Command
    from ..core.ipc_server import JupyterIPCServer
    from ..core.ipc_client import JupyterIPCClient
    from ..core.error_manager import AutoSaver

try:
    from .preferences_dialog import PreferencesDialog
except ImportError:
    PreferencesDialog = None

try:
    from ..utils.latex_renderer import export_canvas_to_latex
except ImportError:
    from utils.latex_renderer import export_canvas_to_latex

try:
    from ..utils.theme_manager import THEMES, set_theme, get_current_theme
except ImportError:
    from utils.theme_manager import THEMES, set_theme, get_current_theme

try:
    from ..utils.i18n_manager import t, get_i18n, SUPPORTED_LANGUAGES
except ImportError:
    from utils.i18n_manager import t, get_i18n, SUPPORTED_LANGUAGES

try:
    from ..utils.logger import get_logger, LOG_DIR
except ImportError:
    from utils.logger import get_logger, LOG_DIR

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t('main_window.title'))
        self.setGeometry(100, 100, 1200, 800)

        self._objects_data: dict = {}
        self.current_function_id = None  # 跟踪当前正在编辑的函数ID

        self.geometry_engine = GeometryEngine()
        self.cas_provider = CASProvider()
        self.geometry_engine.set_cas_provider(self.cas_provider)
        self.python_repl = PythonREPL()
        self.ai_manager = AIManager()

        # 将 ai_manager 注入给代码编辑器
        from mathlab.ui.code_editor import AutocompleteTextEdit
        self.code_editor = AutocompleteTextEdit(ai_manager=self.ai_manager)

        # 命令管理器（必须在 setup_ui 前创建，供各面板注册命令）
        self.cmd_manager = CommandManager()

        # 🌟 1. 启动跨进程监听服务 🌟
        self.ipc_server = JupyterIPCServer(port=45678, parent=self)
        self.ipc_server.command_received.connect(self.handle_kernel_command)
        self.ipc_server.start()

        # 🌟 2. 实例化发送器 (发给 Jupyter) 🌟
        self.ipc_client = JupyterIPCClient(port=45679)

        self.setup_ui()
        
        # 将客户端挂载到画板上，供画板使用
        self.central_widget.ipc_client = self.ipc_client
        self.setup_menus()
        self.setup_toolbar()
        self.setup_docks()

        self.load_stylesheet()

        self.current_project = None

        self.active_workers = set()
        self.fit_worker = None
        self.cluster_worker = None
        self.recognize_worker = None
        self.generate_points_worker = None

        self.connect_signals()
        self._register_commands()  # 注册命令面板命令

        get_i18n().add_language_change_listener(self._on_language_changed)
        self.apply_theme(get_current_theme())
        
        # 初始化自动存档与恢复神机
        self.autosaver = AutoSaver(self)
        self.autosaver.check_and_recover()
        
        # 1. 挂载画板追踪器
        from mathlab.core.canvas_tracker import CanvasShadowTracker
        self.canvas_tracker = CanvasShadowTracker(self.geometry_engine)
        
        # 实例化 Omni-Bar，保证生命周期绑定
        self.omni_bar = OmniBar(self)
        
        # 注册全局快捷键 (Ctrl+K 或 Cmd+K)
        self.shortcut_summon = QShortcut(QKeySequence("Ctrl+K"), self)
        self.shortcut_summon.activated.connect(self.toggle_omni_bar)
        
        # 启动 AI 全局交互集成
        self._setup_ai_integration()
        
        # 启动 ECharts 集成
        self._setup_echarts_integration()

    def toggle_omni_bar(self):
        if self.omni_bar.isVisible() and self.omni_bar.windowOpacity() > 0:
            self.omni_bar.dismiss()
        else:
            # 传入当前主窗口的几何数据，用于 Omni-Bar 计算居中位置
            self.omni_bar.summon(self.geometry())
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'omni_bar') and self.omni_bar.isVisible():
            self.omni_bar.dismiss()

    def setup_ui(self):
        self.central_tabs = QTabWidget()
        self.central_tabs.setStyleSheet("QTabWidget::pane { border: none; }")

        self.central_widget = GeometryCanvas(self)
        self.notebook = NotebookPanel(self)
        self.notebook.ai_explain_requested.connect(self.handle_ai_explain)
        
        try:
            from .geometry_panel import GeometryPanel
            self.geogebra_panel = GeometryPanel(self)
            if hasattr(self.geogebra_panel, 'canvas'):
                self.geogebra_panel.canvas.ipc_client = self.ipc_client
        except ImportError:
            self.geogebra_panel = None

        self.central_tabs.addTab(self.notebook, t('notebook.title') or "Interactive Notebook")
        self.central_tabs.addTab(self.central_widget, t('main_window.geometry_tools') or "Geometry Canvas")
        if self.geogebra_panel:
            self.central_tabs.addTab(self.geogebra_panel, "Mini GeoGebra")

        # ── 🌌 JupyterLab 嵌入工作区 ────────────────────────────────────────────
        self._init_jupyter_tab()

        self.setCentralWidget(self.central_tabs)

    def _init_jupyter_tab(self):
        """在后台线程启动 JupyterLab，避免阻塞 UI 初始化"""
        self.jupyter_mgr = None
        self.jupyter_workspace = None

        if JupyterManager is None or JupyterPanel is None:
            logger.warning("JupyterManager / JupyterPanel 未能导入，Jupyter 标签页已跳过。")
            return

        try:
            self.jupyter_mgr = JupyterManager()
            # 创建面板（此时服务还未就绪，面板显示加载动画）
            self.jupyter_workspace = JupyterPanel(
                self.jupyter_mgr.url, self
            )
            self.central_tabs.addTab(
                self.jupyter_workspace, "🌌 Jupyter 工作区"
            )

            # 在后台线程启动服务，就绪后触发页面加载
            import threading
            def _start_and_load():
                self.jupyter_mgr.start(timeout=30)
                # 切回主线程加载页面（Qt 要求 UI 操作在主线程）
                from PySide6.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(
                    self.jupyter_workspace,
                    "load_workspace",
                    Qt.ConnectionType.QueuedConnection,
                )

            t_jupyter = threading.Thread(
                target=_start_and_load, daemon=True, name="JupyterStartup"
            )
            t_jupyter.start()
            logger.info("JupyterLab 后台启动线程已派发，端口：%s", self.jupyter_mgr.port)

        except Exception as exc:
            logger.warning("Jupyter 初始化失败（不影响其他功能）：%s", exc)

    def setup_menus(self):
        menu_bar = QMenuBar(self)

        self.file_menu = QMenu(t('menu.file'), self)

        self.new_action         = QAction(t('main_window.new_project'), self)
        self.open_action        = QAction(t('main_window.open_project'), self)
        self.save_action        = QAction(t('main_window.save_project'), self)
        self.save_as_action     = QAction(t('main_window.save_as'), self)
        self.export_png_action  = QAction(t('main_window.export_png'), self)
        self.export_svg_action  = QAction(t('main_window.export_svg'), self)
        self.export_latex_action = QAction(t('main_window.export_latex'), self)
        self.exit_action        = QAction(t('main_window.exit'), self)

        self.new_action.setShortcut('Ctrl+N')
        self.open_action.setShortcut('Ctrl+O')
        self.save_action.setShortcut('Ctrl+S')
        self.save_as_action.setShortcut('Ctrl+Shift+S')

        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.export_png_action)
        self.file_menu.addAction(self.export_svg_action)
        self.file_menu.addAction(self.export_latex_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        self.edit_menu = QMenu(t('menu.edit'), self)

        self.undo_action   = QAction(t('main_window.undo'), self)
        self.redo_action   = QAction(t('main_window.redo'), self)
        self.delete_action = QAction(t('main_window.delete'), self)

        self.undo_action.setShortcut('Ctrl+Z')
        self.redo_action.setShortcut('Ctrl+Y')
        self.delete_action.setShortcut('Delete')

        self.edit_menu.addAction(self.undo_action)
        self.edit_menu.addAction(self.redo_action)
        self.edit_menu.addSeparator()
        self.edit_menu.addAction(self.delete_action)

        self.view_menu = QMenu(t('menu.view'), self)

        self.algebra_panel_action = QAction(t('main_window.algebra_panel'), self)
        self.algebra_panel_action.setCheckable(True)
        self.algebra_panel_action.setChecked(True)

        self.properties_panel_action = QAction(t('main_window.properties_panel'), self)
        self.properties_panel_action.setCheckable(True)
        self.properties_panel_action.setChecked(True)

        self.console_action = QAction(t('main_window.console'), self)
        self.console_action.setCheckable(True)
        self.console_action.setChecked(True)

        self.algo_vis_action = QAction(t('main_window.algorithm_visualization'), self)
        self.algo_vis_action.setCheckable(True)

        self.ai_tools_action = QAction(t('main_window.ai_tools'), self)
        self.ai_tools_action.setCheckable(True)

        self.notebook_action = QAction(t('main_window.notebook'), self)
        self.notebook_action.setCheckable(True)

        self.function_explorer_action = QAction(t('function_explorer.title'), self)
        self.function_explorer_action.setCheckable(True)

        self.math_console_action = QAction('数学控制台 (Octave)', self)
        self.math_console_action.setCheckable(True)
        self.math_console_action.setChecked(True)
        self.math_console_action.setShortcut('Ctrl+Shift+M')

        self.theme_action    = QAction(t('main_window.theme'), self)
        self.language_action = QAction(t('main_window.language'), self)

        self.view_menu.addAction(self.algebra_panel_action)
        self.view_menu.addAction(self.properties_panel_action)
        self.view_menu.addAction(self.console_action)
        self.view_menu.addAction(self.math_console_action)
        self.view_menu.addAction(self.algo_vis_action)
        self.view_menu.addAction(self.ai_tools_action)
        self.view_menu.addAction(self.notebook_action)
        self.view_menu.addAction(self.function_explorer_action)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.theme_action)
        self.view_menu.addAction(self.language_action)
        self.preferences_action = QAction(t('main_window.preferences'), self)
        self.preferences_action.setShortcut('Ctrl+,')
        self.view_menu.addAction(self.preferences_action)

        self.ai_menu = QMenu(t('menu.ai'), self)
        self.ai_scatter_action  = QAction(t('ai_tools.scatter_fitting'), self)
        self.ai_cluster_action  = QAction(t('ai_tools.clustering'), self)
        self.ai_digit_action    = QAction(t('ai_tools.digit_recognition'), self)
        self.ai_train_action    = QAction(t('ai_tools.training_notebook'), self)
        self.ai_menu.addAction(self.ai_scatter_action)
        self.ai_menu.addAction(self.ai_cluster_action)
        self.ai_menu.addAction(self.ai_digit_action)
        self.ai_menu.addSeparator()
        self.ai_menu.addAction(self.ai_train_action)

        self.tools_menu = QMenu(t('menu.tools'), self)

        self.geometry_tool_action = QAction(t('main_window.geometry_tools'), self)
        self.algebra_tool_action  = QAction(t('main_window.algebra_tools'), self)
        self.ai_tool_action       = QAction(t('main_window.ai_tools'), self)
        self.signal_lab_action    = QAction("⚡ 信号处理实验室 (FFT)", self)
        self.fractal_gpu_action   = QAction("🚀 极致深渊：GPU 分形探索器", self)

        self.tools_menu.addAction(self.geometry_tool_action)
        self.tools_menu.addAction(self.algebra_tool_action)
        self.tools_menu.addAction(self.ai_tool_action)
        self.tools_menu.addAction(self.signal_lab_action)
        self.tools_menu.addAction(self.fractal_gpu_action)

        self.help_menu = QMenu(t('menu.help'), self)

        self.about_action   = QAction(t('main_window.about'), self)
        self.tutorial_action = QAction(t('main_window.tutorial'), self)

        self.help_menu.addAction(self.tutorial_action)
        self.help_menu.addAction(self.about_action)

        menu_bar.addMenu(self.file_menu)
        menu_bar.addMenu(self.edit_menu)
        menu_bar.addMenu(self.view_menu)
        menu_bar.addMenu(self.tools_menu)
        menu_bar.addMenu(self.ai_menu)
        menu_bar.addMenu(self.help_menu)

        self.setMenuBar(menu_bar)

        self.new_action.triggered.connect(self.on_new_project)
        self.open_action.triggered.connect(self.on_open_project)
        self.save_action.triggered.connect(self.on_save_project)
        self.save_as_action.triggered.connect(self.on_save_project_as)
        self.export_png_action.triggered.connect(self.on_export_png)
        self.export_svg_action.triggered.connect(self.on_export_svg)
        self.export_latex_action.triggered.connect(self.on_export_latex)
        self.exit_action.triggered.connect(self.close)

        self.algebra_panel_action.triggered.connect(self.toggle_algebra_panel)
        self.properties_panel_action.triggered.connect(self.toggle_properties_panel)
        self.console_action.triggered.connect(self.toggle_console)
        self.algo_vis_action.triggered.connect(self.toggle_algo_vis_panel)
        self.notebook_action.triggered.connect(self.toggle_notebook_panel)
        self.ai_tools_action.triggered.connect(self.toggle_ai_tools_panel)
        self.function_explorer_action.triggered.connect(self.toggle_function_explorer)
        self.math_console_action.triggered.connect(self.toggle_math_console)

        self.geometry_tool_action.triggered.connect(self._show_command_palette)
        self.algebra_tool_action.triggered.connect(lambda: self.toggle_algebra_panel(True))
        self.ai_tool_action.triggered.connect(lambda: self.toggle_ai_tools_panel(True))
        self.signal_lab_action.triggered.connect(self.open_signal_lab)
        self.fractal_gpu_action.triggered.connect(self.open_gpu_fractal_explorer)

        self.theme_action.triggered.connect(self.show_theme_dialog)
        self.language_action.triggered.connect(self.show_language_dialog)
        self.preferences_action.triggered.connect(self.show_preferences_dialog)

        self.ai_scatter_action.triggered.connect(lambda: self.toggle_ai_tools_panel(True))
        self.ai_cluster_action.triggered.connect(lambda: self.toggle_ai_tools_panel(True))
        self.ai_digit_action.triggered.connect(lambda: self.toggle_ai_tools_panel(True))
        self.ai_train_action.triggered.connect(lambda: self.toggle_ai_tools_panel(True))

        self.about_action.triggered.connect(self.show_about)

    def open_signal_lab(self):
        self.signal_lab = SignalLabPanel(self)
        self.signal_lab.show()

    def open_gpu_fractal_explorer(self):
        self.gpu_fractal_explorer = FractalGPUExplorer(self)
        self.gpu_fractal_explorer.show()

    def setup_toolbar(self):
        self.toolbar = QToolBar('Main Toolbar')
        self.toolbar.setIconSize(QSize(20, 20))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)

        self.select_action = QAction(t('main_window.select'), self)
        self.select_action.setCheckable(True)
        self.select_action.setChecked(True)

        self.point_action = QAction(t('main_window.point'), self)
        self.point_action.setCheckable(True)

        self.segment_action = QAction(t('main_window.segment'), self)
        self.segment_action.setCheckable(True)

        self.circle_action = QAction(t('main_window.circle'), self)
        self.circle_action.setCheckable(True)

        self.polygon_action = QAction(t('main_window.polygon'), self)
        self.polygon_action.setCheckable(True)

        self.pan_action = QAction(t('main_window.pan'), self)
        self.pan_action.setCheckable(True)

        self.tool_actions = [
            self.select_action, self.point_action, self.segment_action,
            self.circle_action, self.polygon_action, self.pan_action
        ]

        self.toolbar.addAction(self.select_action)
        self.toolbar.addAction(self.point_action)
        self.toolbar.addAction(self.segment_action)
        self.toolbar.addAction(self.circle_action)
        self.toolbar.addAction(self.polygon_action)
        self.toolbar.addAction(self.pan_action)
        self.toolbar.addSeparator()

        self.command_bar = CommandBar()
        self.toolbar.addWidget(self.command_bar)

        self.toolbar.addSeparator()

        self._zoom_in_action = QAction(t('main_window.zoom_in'), self)
        self.toolbar.addAction(self._zoom_in_action)
        self._zoom_in_action.triggered.connect(self.on_zoom_in)

        self._zoom_out_action = QAction(t('main_window.zoom_out'), self)
        self.toolbar.addAction(self._zoom_out_action)
        self._zoom_out_action.triggered.connect(self.on_zoom_out)

        self.toolbar.addSeparator()

        self.lang_btn = QPushButton('EN/ZH')
        self.lang_btn.setToolTip(t('main_window.language'))
        self.lang_btn.setObjectName('lang_btn')
        self.lang_btn.setFixedSize(64, 28)
        self.lang_btn.setStyleSheet(
            'QPushButton{'
            '  background:#f8f9ff;'
            '  border:1px solid #c3c6d7;'
            '  border-radius:4px;'
            '  padding:2px 8px;'
            '  font-size:11px;'
            '  font-weight:700;'
            '  color:#434655;'
            '}'
            'QPushButton:hover{'
            '  background:#e5eeff;'
            '  border-color:#004ac6;'
            '  color:#004ac6;'
            '}'
        )
        self.lang_btn.clicked.connect(self._toggle_language)
        self.toolbar.addWidget(self.lang_btn)

        self.settings_btn = QPushButton()
        self.settings_btn.setToolTip(t('main_window.preferences'))
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setStyleSheet(
            'QPushButton{'
            '  background:transparent;'
            '  border:none;'
            '}'
            'QPushButton:hover{'
            '  background:#e5eeff;'
            '  border-radius:4px;'
            '}'
        )
        self.settings_btn.setIconSize(QSize(18, 18))
        self.settings_btn.clicked.connect(self.show_preferences_dialog)
        self.toolbar.addWidget(self.settings_btn)

        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self._connect_tool_actions()
        self.update_toolbar_icons()

    def _connect_tool_actions(self):
        tool_map = [
            ('select',  self.select_action),
            ('point',   self.point_action),
            ('segment', self.segment_action),
            ('circle',  self.circle_action),
            ('polygon', self.polygon_action),
            ('pan',     self.pan_action),
        ]
        for tool_name, action in tool_map:
            action.triggered.connect(
                lambda checked, tn=tool_name: self.on_action_selected(tn)
            )

    def setup_docks(self):
        self.algebra_panel = AlgebraPanel(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.algebra_panel)
        self.algebra_panel.setWindowTitle(t('algebra_panel.title').upper())

        self.properties_panel = PropertiesPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_panel)
        self.properties_panel.setWindowTitle(t('properties_panel.title').upper())

        self.console = PythonConsole(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console)
        self.console.setWindowTitle(t('console.title').upper())
        self.console.set_python_repl(self.python_repl)

        # ── 数学控制台（Octave / NumEngine 交互终端）────────────────────────────
        self.math_console = MathConsole(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.math_console)
        # 与 Python Console 合并为 Tab（底部共享一个停靠区）
        self.tabifyDockWidget(self.console, self.math_console)
        # 默认显示 Python Console（让 math_console 在背景 Tab）
        self.console.raise_()

        # 函数探索器面板
        self.function_explorer = FunctionExplorerPanel(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.function_explorer)
        self.function_explorer.setWindowTitle(t('function_explorer.title').upper())
        self.function_explorer.hide()  # 默认隐藏

        self.algo_vis_panel = AlgoVisPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.algo_vis_panel)
        self.algo_vis_panel.setWindowTitle(t('algo_vis.title').upper())
        self.algo_vis_panel.hide()

        self.ai_tools_panel = AIToolsPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.ai_tools_panel)
        self.ai_tools_panel.setWindowTitle(t('ai_tools.title').upper())
        self.ai_tools_panel.hide()

        self.tabifyDockWidget(self.algo_vis_panel, self.ai_tools_panel)

        # ── 命令面板（悬浮层，必须在 setup_docks 结尾创建） ───────────────────────
        self.cmd_palette = CommandPalette(self.cmd_manager, self)

        # Ctrl+Shift+P 唤醒命令面板
        palette_shortcut = QShortcut(QKeySequence('Ctrl+Shift+P'), self)
        palette_shortcut.activated.connect(self._show_command_palette)

        # Ctrl+P 备用快捷键
        palette_shortcut2 = QShortcut(QKeySequence('Ctrl+P'), self)
        palette_shortcut2.activated.connect(self._show_command_palette)

        # ── ✨ 信号接线：数学控制台 plot() 命令 → ECharts 渲染 ────────────────
        # math_console.bridge.signals 是 BridgeSignals(QObject)，
        # plot_requested 发射一个包含 x/y/type/title 的 dict。
        self.math_console.bridge.signals.plot_requested.connect(
            self.handle_console_plot
        )

    def load_stylesheet(self):
        try:
            try:
                from ..utils.theme_manager import get_theme_colors
            except ImportError:
                from utils.theme_manager import get_theme_colors
            theme = get_theme_colors()
            
            stylesheet_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 'ui', 'styles.qss'
            )
            with open(stylesheet_path, 'r', encoding='utf-8') as f:
                qss = f.read()

            if theme['name'] != 'Dark':
                qss = qss.replace('#13131A', theme['background'])
                qss = qss.replace('#E0E0E6', theme['foreground'])
                qss = qss.replace('#1E1E28', theme['panel_bg'])
                qss = qss.replace('#2A2A35', theme['panel_border'])
                qss = qss.replace('#181822', theme['console_bg'])
                qss = qss.replace('#323242', theme['panel_border'])
                qss = qss.replace('#FFFFFF', theme['console_fg'])
                qss = qss.replace('#00A67E', theme['accent'])
                qss = qss.replace('#2A2A38', theme['panel_bg'])
                qss = qss.replace('#3A3A4A', theme['panel_border'])
                qss = qss.replace('#353545', theme['panel_border'])

            self.setStyleSheet(qss)
        except Exception as e:
            logger.warning('样式表加载失败: %s', e)

    def connect_signals(self):
        self.central_widget.point_added.connect(self.on_point_added)
        self.central_widget.segment_added_coords.connect(self.on_segment_added)
        self.central_widget.circle_added_coords.connect(self.on_circle_added)
        self.central_widget.polygon_added_coords.connect(self.on_polygon_added)

        # 连接 geometry_engine 的监听器
        if hasattr(self, 'geometry_engine'):
            self.geometry_engine.add_listener(self.on_geometry_event)

        self.algebra_panel.object_selected.connect(self.on_algebra_item_selected)
        self.algebra_panel.object_deleted.connect(self.on_object_deleted)
        self.algebra_panel.object_renamed.connect(self.on_object_renamed)
        self.algebra_panel.equation_changed.connect(self.on_equation_changed)
        
        # 连接属性面板信号
        if hasattr(self, 'properties_panel'):
            self.properties_panel.object_renamed.connect(self.on_object_renamed)
            self.properties_panel.color_changed.connect(self.on_object_color_changed)
            self.properties_panel.opacity_changed.connect(self.on_object_opacity_changed)
            self.properties_panel.stroke_changed.connect(self.on_object_stroke_changed)
            self.properties_panel.label_toggled.connect(self.on_object_label_toggled)

        self.central_widget.object_selected.connect(self.on_algebra_item_selected)
        self.console.execute_command.connect(self.on_console_command)
        self.command_bar.command_entered.connect(self.on_command_entered)

        self.ai_tools_panel.action_requested.connect(self.execute_ai_action)
        self.ai_tools_panel.fit_requested.connect(self.on_ai_fit_requested)
        self.ai_tools_panel.cluster_requested.connect(self.on_ai_cluster_requested)
        self.ai_tools_panel.recognize_requested.connect(self.on_ai_recognize_requested)
        self.ai_tools_panel.generate_points.connect(self.on_ai_generate_points)


        # 连接函数探索器信号
        self.function_explorer.function_added.connect(self.on_function_added)
        self.function_explorer.function_updated.connect(self.on_function_updated)
        self.function_explorer.render_integral_area.connect(self.on_render_integral_area)
        self.function_explorer.render_tangent_line.connect(self.on_render_tangent_line)

    def on_code_completion_requested(self, code_text: str, line: int, column: int):
        if hasattr(self, 'python_repl'):
            completions = self.python_repl.get_completions(code_text, line, column)
            self.ai_tools_panel.code_editor.set_completions(completions)

    # 🌟 2. 处理来自 Jupyter 的指令 🌟
    def handle_kernel_command(self, msg: dict):
        cmd = msg.get("cmd")
        
        # 获取底层几何引擎
        engine = self.geometry_engine
        
        try:
            if cmd == "draw_point":
                # 调用核心几何引擎
                engine.add_point(msg["x"], msg["y"], name=msg.get("name"))
                
            elif cmd == "draw_line":
                p1_id = None
                p2_id = None
                for obj_id, entity in engine.objects.items():
                    if entity.name == msg.get("p1"): p1_id = obj_id
                    if entity.name == msg.get("p2"): p2_id = obj_id
                    
                if p1_id and p2_id:
                    engine.add_segment(p1_id, p2_id, name=msg.get("name"))
                    
            elif cmd == "clear":
                engine.clear()
            
        except Exception as e:
            logger.error(f"执行几何指令失败: {e}")

    def _add_object(self, obj_data: dict) -> None:
        obj_id = obj_data['id']
        self._objects_data[obj_id] = obj_data
        self.algebra_panel.add_object(obj_data)
        self.central_widget.draw_object(obj_id, obj_data)

    def on_geometry_event(self, event_type: str, data):
        """处理来自 geometry_engine 的事件"""
        if event_type == 'object_added':
            self._add_object(data)
        elif event_type == 'object_updated':
            obj_id = data.get('id')
            if obj_id:
                self._objects_data[obj_id] = data
                self.algebra_panel.update_object(data)
                self.central_widget.update_object(obj_id, data)
        elif event_type == 'object_removed':
            obj_id = data
            if obj_id in self._objects_data:
                del self._objects_data[obj_id]
                self.algebra_panel.remove_object(obj_id)
                self.central_widget.remove_object(obj_id)
        elif event_type == 'canvas_cleared':
            self._objects_data.clear()
            self.algebra_panel.clear()
            self.central_widget.clear_canvas()

    def on_function_added(self, func_data: dict):
        """处理函数探索器添加的函数"""
        try:
            plot_type = func_data.get('plot_type', 'FunctionPlot')
            expression = func_data.get('expression', '')
            
            if not expression:
                return
            
            # 根据类型调用不同的绘图方法
            if plot_type == 'FunctionPlot':
                obj_id = self.geometry_engine.add_function_plot(
                    expression=expression,
                    x_range=func_data.get('x_range', (-10, 10)),
                    num_points=500
                )
            elif plot_type == 'ImplicitPlot':
                obj_id = self.geometry_engine.add_implicit_plot(
                    expression=expression,
                    x_range=func_data.get('x_range', (-10, 10)),
                    y_range=func_data.get('y_range', (-10, 10))
                )
            elif plot_type == 'PolarPlot':
                import math
                obj_id = self.geometry_engine.add_polar_plot(
                    expression=expression,
                    theta_range=(0, 2*math.pi),
                    num_points=500
                )
            else:
                return
            
            # 保存当前函数ID，用于后续更新
            self.current_function_id = obj_id
            # [P0修复 Bug4] 同步给 function_explorer 面板具体的 obj_id
            self.function_explorer.current_function_id = obj_id
            
            # 保存原始表达式和参数信息到对象中
            obj = self.geometry_engine.get_object(obj_id)
            if obj:
                obj.original_expression = expression
                obj.parameters = func_data.get('parameters', {})
        except Exception as e:
            QMessageBox.warning(self, t('dialogs.error'), 
                              f"{t('errors.invalid_expression')}: {str(e)}")
    
    # [P0修复 Bug4] 接收 obj_id 并精确更新，而非依赖共享的 current_function_id
    def on_function_updated(self, obj_id: str, func_data: dict):
        """处理函数探索器更新的函数（参数变化）"""
        try:
            plot_type = func_data.get('plot_type', 'FunctionPlot')
            expression = func_data.get('expression', '')
            original_expr = func_data.get('original_expression', expression)
            
            if not expression or not obj_id:
                return
            
            # 使用传入的 obj_id 定位对象
            last_func = self.geometry_engine.get_object(obj_id)
            if not last_func:
                logger.warning("函数已被删除")
                return
                
            if hasattr(last_func, '_generate_points'):
                last_func.expression = expression
                last_func._generate_points()
                
                # 通知更新
                self.on_geometry_event('object_updated', last_func.serialize())
        except Exception as e:
            logger.warning("更新函数时出错: %s", e)

    def on_render_integral_area(self, expr: str, a: float, b: float, result: float):
        if hasattr(self, 'central_widget') and hasattr(self.central_widget, 'render_integral_area'):
            self.central_widget.render_integral_area(expr, a, b, result)

    def on_render_tangent_line(self, expr: str, x0: float, k: float):
        if hasattr(self, 'central_widget') and hasattr(self.central_widget, 'render_tangent_line'):
            self.central_widget.render_tangent_line(expr, x0, k)

    # ── AI 全局交互集成 ──────────────────────────────────────────────
    def _setup_ai_integration(self):
        from PySide6.QtCore import QPointF
        from mathlab.core.agent_registry import AgentRegistry
        from mathlab.core.ai_manager import GeometryAgent, DataVizAgent
        from mathlab.core.agent_bridge import AgentUIBridge
        import json
        
        # 1. 初始化联邦路由大脑
        self.agent_registry = AgentRegistry(self.ai_manager)
        
        # 2. 注册所有领域专家
        self.agent_registry.register_agent(
            name="GeometryAgent",
            description="擅长解决平面几何、微积分、代数方程求解，以及二维坐标系中的点线圆绘制任务。",
            agent_instance=GeometryAgent(self.ai_manager)
        )
        
        self.agent_registry.register_agent(
            name="DataVizAgent",
            description="擅长处理统计数据可视化、柱状图、折线图、南丁格尔玫瑰图、3D曲面图等 ECharts 图表渲染任务。",
            agent_instance=DataVizAgent(self.ai_manager)
        )
        
        # 3. UI 桥梁现在不再绑定单一 Agent，而是绑定整个 Registry 路由器
        self.agent_bridge = AgentUIBridge(self.agent_registry, self)
        
        # 4. 信号与槽的严密绑定 (跨线程安全)
        # 思考 -> 打印到终端
        self.agent_bridge.thought_emitted.connect(self.console.append_agent_thought)
        
        # 代码 -> 注入 Monaco 编辑器
        self.agent_bridge.code_generated.connect(self._stream_code_to_editor)
        
        # 结束 -> 善后处理
        self.agent_bridge.task_finished.connect(self._on_agent_task_finished)
        
        # 5. 绑定全局输入框 (OmniBar) 的回车事件
        self.omni_bar.search_submitted.connect(self._trigger_global_ai_task)

    def _setup_echarts_integration(self):
        # 绑定刚刚解析出的信号
        self.code_editor.backend.echarts_data_ready.connect(self._show_echarts_panel)

    def _show_echarts_panel(self, chart_options_dict):
        """唤醒 ECharts 插件面板并渲染"""
        import json
        
        if not hasattr(self, 'plugin_manager'):
            self.console.append_agent_observation("⚠️ 未找到插件管理器！", is_error=True)
            return
        echarts_plugin = self.plugin_manager.active_plugins.get("ECharts Data Viewer")
        if not echarts_plugin:
            self.console.append_agent_observation("⚠️ 未找到 ECharts 插件实例！", is_error=True)
            return
            
        web_view = getattr(echarts_plugin, 'web_view', None)
        if not web_view:
            return
            
        json_payload = json.dumps(chart_options_dict, ensure_ascii=False)
        js_command = f"if(window.updateChartOptions) {{ window.updateChartOptions({json_payload}); }} else if(window.renderChart) {{ window.renderChart('{json_payload}'); }}"
        web_view.page().runJavaScript(js_command)
        
        self.console.append_agent_observation("✨ 3D/2D 交互图表已在 ECharts 面板渲染就绪！", is_error=False)

    def _trigger_global_ai_task(self, user_prompt):
        """当用户在顶部搜索框按下回车时触发"""
        if hasattr(self.omni_bar, 'input_field'):
            self.omni_bar.input_field.clear()
        
        if hasattr(self.console, 'output_area'):
            self.console.output_area.append(f"<hr><b style='color:#64B5F6'>👤 用户:</b> {user_prompt}<br>")
        
        # 唤醒 AI 专属光标，飞入视野
        from PySide6.QtCore import QPointF
        if hasattr(self, 'ai_cursor'):
            self.ai_cursor.move_to(QPointF(self.width() / 2, self.height() / 2), 600)
            
        # 启动后台推演
        self.agent_bridge.run_task_in_background(user_prompt)

    def _stream_code_to_editor(self, code):
        """接收到 AI 代码，安全写入前端 Monaco"""
        import json
        escaped_code = json.dumps(code)
        self.code_editor.web_view.page().runJavaScript(f"window.editor.setValue({escaped_code});")
        
        # 光标小幅抖动，模拟正在打字
        if hasattr(self, 'ai_cursor'):
            import random
            from PySide6.QtCore import QPointF
            curr_pos = self.ai_cursor.cursorPos
            shake_pos = QPointF(curr_pos.x() + random.randint(-5, 5), curr_pos.y() + random.randint(-5, 5))
            self.ai_cursor.move_to(shake_pos, 100)

    def _on_agent_task_finished(self, success, final_content):
        """Agent 彻底跑完任务 (包含自愈和 RAG 沉淀) 后的 UI 善后"""
        if success:
            self.console.append_agent_observation("🎉 任务完美执行并渲染！", is_error=False)
            # 触发底层执行，刷新所有的画布和 C# 引擎联动
            self.code_editor.backend.execute_code(final_content)
        else:
            self.console.append_agent_observation("⚠️ 尝试多次失败，请手动干预。", is_error=True)
            
        # AI 光标隐退
        if hasattr(self, 'ai_cursor'):
            self.ai_cursor.setVisible(False)

    def on_action_selected(self, tool_name: str) -> None:
        for action in self.tool_actions:
            action.setChecked(False)

        action_map = {
            'select':  self.select_action,
            'point':   self.point_action,
            'segment': self.segment_action,
            'circle':  self.circle_action,
            'polygon': self.polygon_action,
            'pan':     self.pan_action,
        }
        if tool_name in action_map:
            action_map[tool_name].setChecked(True)

        self.central_widget.set_tool(tool_name)

    def on_zoom_in(self) -> None:
        self.central_widget.zoom_in()

    def on_zoom_out(self) -> None:
        self.central_widget.zoom_out()

    def on_point_added(self, x: float, y: float) -> None:
        if hasattr(self, 'geometry_engine'):
            self.geometry_engine.add_point(x, y)
        else:
            obj_id = str(uuid.uuid4())
            obj_data = {
                'id': obj_id,
                'name': t('geometry.new_point'),
                'type': 'Point',
                'coordinates': {'x': x, 'y': y},
            }
            self._add_object(obj_data)

    def on_segment_added(self, x1: float, y1: float, x2: float, y2: float) -> None:
        if hasattr(self, 'geometry_engine'):
            p1_id = self.geometry_engine.add_point(x1, y1)
            p2_id = self.geometry_engine.add_point(x2, y2)
            self.geometry_engine.add_segment(p1_id, p2_id)
        else:
            obj_id = str(uuid.uuid4())
            obj_data = {
                'id': obj_id,
                'name': t('geometry.segment'),
                'type': 'Segment',
                'coordinates': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2},
            }
            self._add_object(obj_data)

    def on_circle_added(self, cx: float, cy: float, radius: float) -> None:
        if hasattr(self, 'geometry_engine'):
            c_id = self.geometry_engine.add_point(cx, cy)
            self.geometry_engine.add_circle(c_id, radius)
        else:
            obj_id = str(uuid.uuid4())
            obj_data = {
                'id': obj_id,
                'name': t('geometry.circle'),
                'type': 'Circle',
                'coordinates': {'cx': cx, 'cy': cy, 'r': radius},
            }
            self._add_object(obj_data)

    def on_polygon_added(self, points: list) -> None:
        if hasattr(self, 'geometry_engine'):
            p_ids = [self.geometry_engine.add_point(pt[0], pt[1]) for pt in points]
            self.geometry_engine.add_polygon(p_ids)
        else:
            obj_id = str(uuid.uuid4())
            obj_data = {
                'id': obj_id,
                'name': t('geometry.polygon'),
                'type': 'Polygon',
                'coordinates': {'points': list(points)},
                'points': list(points),
            }
            self._add_object(obj_data)

    def on_algebra_item_selected(self, obj_id: str) -> None:
        self.central_widget.select_object(obj_id)
        if hasattr(self, 'geometry_engine'):
            obj = self.geometry_engine.get_object(obj_id)
            if obj:
                self.properties_panel.set_object(obj.serialize())
        elif obj_id in self._objects_data:
            self.properties_panel.set_object(self._objects_data[obj_id])

    def on_object_color_changed(self, obj_id, color):
        if hasattr(self, 'geometry_engine'):
            obj = self.geometry_engine.get_object(obj_id)
            if obj:
                obj.color = color
                self._update_object_display(obj_id, obj)

    def on_object_opacity_changed(self, obj_id, opacity):
        if hasattr(self, 'geometry_engine'):
            obj = self.geometry_engine.get_object(obj_id)
            if obj:
                obj.opacity = opacity
                self._update_object_display(obj_id, obj)

    def on_object_stroke_changed(self, obj_id, stroke):
        if hasattr(self, 'geometry_engine'):
            obj = self.geometry_engine.get_object(obj_id)
            if obj:
                obj.stroke = stroke
                self._update_object_display(obj_id, obj)

    def on_object_label_toggled(self, obj_id, show_label):
        if hasattr(self, 'geometry_engine'):
            obj = self.geometry_engine.get_object(obj_id)
            if obj:
                obj.show_label = show_label
                self._update_object_display(obj_id, obj)

    def _update_object_display(self, obj_id, obj):
        obj_data = obj.serialize()
        self._objects_data[obj_id] = obj_data
        self.algebra_panel.update_object(obj_data)
        self.central_widget.update_object(obj_id, obj_data)

    def on_object_deleted(self, obj_id: str) -> None:
        if hasattr(self, 'geometry_engine'):
            self.geometry_engine.remove_object(obj_id)
        else:
            self.central_widget.remove_object(obj_id)
            self.algebra_panel.remove_object(obj_id)
        self._objects_data.pop(obj_id, None)

    def on_object_renamed(self, obj_id: str, new_name: str) -> None:
        if hasattr(self, 'geometry_engine'):
            obj = self.geometry_engine.get_object(obj_id)
            if obj:
                obj.name = new_name
                obj_data = obj.serialize()
                self._objects_data[obj_id] = obj_data
                self.algebra_panel.update_object(obj_data)
                self.central_widget.update_object(obj_id, obj_data)
        else:
            if obj_id in self._objects_data:
                self._objects_data[obj_id]['name'] = new_name
                self.algebra_panel.update_object(self._objects_data[obj_id])
                self.central_widget.update_object(obj_id, self._objects_data[obj_id])

    def on_equation_changed(self, obj_id: str, new_equation: str) -> None:
        if not hasattr(self, 'geometry_engine') or not hasattr(self, 'cas_provider'):
            return
        
        obj = self.geometry_engine.get_object(obj_id)
        if not obj:
            return
        
        if obj.type in ['Line', 'Segment']:
            # 1. 定义计算成功后的更新回调（由 TaskManager 自动在主线程中触发，极其安全）
            def on_success(new_coords):
                if len(new_coords) >= 2:
                    self.geometry_engine.block_signals(True)
                    
                    p1_id = obj.point1_id
                    p2_id = obj.point2_id
                    
                    # 更新控制点
                    self.geometry_engine.update_point(p1_id, x=new_coords[0][0], y=new_coords[0][1])
                    self.geometry_engine.update_point(p2_id, x=new_coords[1][0], y=new_coords[1][1])
                    
                    self.geometry_engine.block_signals(False)
                    obj.update_coordinates(self.geometry_engine)
                    # 触发全局画布重绘
                    self.on_geometry_event('object_updated', obj.serialize())

            # 2. 定义失败回调
            def on_error(err_msg):
                self.console.display_system_message(f"公式解析失败: {err_msg}", level='error')

            # 3. 将阻塞的方程反解任务丢入线程池！
            TaskManager().submit(
                fn=self.cas_provider.extract_line_control_points,
                on_success=on_success,
                on_error=on_error,
                group_id=f"eq_{obj_id}",
                equation_str=new_equation
            )

    def execute_ai_action(self, action_data: dict) -> None:
        action = action_data.get('action')
        engine = self.geometry_engine if hasattr(self, 'geometry_engine') else None
        
        if action == 'add_point':
            x = action_data.get('x', 0.0)
            y = action_data.get('y', 0.0)
            z = action_data.get('z', 0.0)
            name = action_data.get('name', '')
            if engine:
                engine.add_point(x=x, y=y, z=z, name=name)
            else:
                self.on_point_added(x, y)
        
        elif action == 'add_segment':
            point1_id = action_data.get('point1_id')
            point2_id = action_data.get('point2_id')
            if point1_id and point2_id and engine:
                engine.add_segment(point1_id, point2_id)
        
        elif action == 'add_circle':
            center_id = action_data.get('center_id')
            radius = action_data.get('radius', 1.0)
            if center_id and engine:
                engine.add_circle(center_id, radius)
                
        elif action == 'add_sphere':
            center_id = action_data.get('center_id')
            radius = action_data.get('radius', 1.0)
            if center_id and engine:
                engine.add_sphere(center_id=center_id, radius=radius)
        
        elif action == 'add_polygon':
            point_ids = action_data.get('point_ids', [])
            if len(point_ids) >= 3 and engine:
                engine.add_polygon(point_ids)
        
        elif action == 'update_point':
            point_id = action_data.get('point_id')
            x = action_data.get('x')
            y = action_data.get('y')
            z = action_data.get('z')
            if point_id and (x is not None or y is not None or z is not None) and engine:
                kwargs = {}
                if x is not None:
                    kwargs['x'] = x
                if y is not None:
                    kwargs['y'] = y
                if z is not None:
                    kwargs['z'] = z
                engine.update_point(point_id, **kwargs)
        
        elif action == 'remove_object':
            obj_id = action_data.get('obj_id')
            if obj_id:
                self.on_object_deleted(obj_id)
        
        elif action == 'clear':
            self.on_console_command('%clear')
        
        elif action == 'solve':
            expression = action_data.get('expression', '')
            if expression and hasattr(self, 'cas_provider'):
                def on_success(result):
                    if result.get('success'):
                        self.console.display_result({
                            'success': True,
                            'output': str(result.get('result', '')),
                            'error': '',
                            'more': False
                        })
                
                def on_error(err_msg):
                    self.console.display_system_message(f"求解失败: {err_msg}", level='error')

                TaskManager().submit(
                    fn=self.cas_provider.solve_equation,
                    on_success=on_success,
                    on_error=on_error,
                    equation_str=expression,
                    variable='x'
                )

    def on_ai_fit_requested(self, points: list, model_type: str, params: dict = None) -> None:
        if not points:
            return

        if self.fit_worker is not None and self.fit_worker.isRunning():
            return

        if params is None:
            params = {}

        self.ai_tools_panel.set_loading_state(True)
        self.statusBar().showMessage(f"正在训练 {model_type} 模型，请稍候...")

        self.fit_worker = AIFitWorker(self.ai_manager, points, model_type, **params)
        self.active_workers.add(self.fit_worker)
        self.fit_worker.finished.connect(lambda res, w=self.fit_worker: self.on_ai_worker_finished(res, w))
        self.fit_worker.error.connect(lambda msg, w=self.fit_worker: self.on_ai_worker_error(msg, w))
        self.fit_worker.start()

    def on_ai_worker_finished(self, result: dict, worker):
        # 在 deleteLater 之前完成所有 worker 类型判断，避免竞态
        if isinstance(worker, AIFitWorker):
            self.statusBar().showMessage("模型训练完成", 3000)
            self.ai_tools_panel.set_fit_result(result)
        elif isinstance(worker, AIClusterWorker):
            self.statusBar().showMessage("聚类分析完成", 3000)
            self.ai_tools_panel.set_cluster_result(result)
        elif isinstance(worker, AIRecognizeWorker):
            self.statusBar().showMessage("识别完成", 3000)
            self.ai_tools_panel.set_recognition_result(result)
        
        # 清理 worker
        if worker in self.active_workers:
            self.active_workers.remove(worker)
            worker.deleteLater()

    def on_ai_cluster_requested(self, points: list, method: str, params: dict) -> None:
        if not points:
            return

        if self.cluster_worker is not None and self.cluster_worker.isRunning():
            return

        self.ai_tools_panel.set_loading_state(True)
        self.statusBar().showMessage(f"正在进行 {method} 聚类分析...")

        self.cluster_worker = AIClusterWorker(self.ai_manager, points, method, params)
        self.active_workers.add(self.cluster_worker)
        self.cluster_worker.finished.connect(lambda res, w=self.cluster_worker: self.on_ai_worker_finished(res, w))
        self.cluster_worker.error.connect(lambda msg, w=self.cluster_worker: self.on_ai_worker_error(msg, w))
        self.cluster_worker.start()

    def on_ai_recognize_requested(self, image_data: list) -> None:
        if self.recognize_worker is not None and self.recognize_worker.isRunning():
            return
            
        self.ai_tools_panel.set_loading_state(True)
        self.statusBar().showMessage("正在识别数字...")

        self.recognize_worker = AIRecognizeWorker(self.ai_manager, image_data)
        self.active_workers.add(self.recognize_worker)
        self.recognize_worker.finished.connect(lambda res, w=self.recognize_worker: self.on_ai_worker_finished(res, w))
        self.recognize_worker.error.connect(lambda msg, w=self.recognize_worker: self.on_ai_worker_error(msg, w))
        self.recognize_worker.start()

    def on_ai_worker_error(self, error_msg: str, worker=None):
        if worker and worker in self.active_workers:
            self.active_workers.remove(worker)
            worker.deleteLater()
        
        self.ai_tools_panel.set_loading_state(False)
        self.statusBar().showMessage(f"后台运算出错: {error_msg}", 5000)

    def on_ai_generate_points(self, n: int) -> None:
        if self.generate_points_worker is not None and self.generate_points_worker.isRunning():
            return
            
        self.ai_tools_panel.set_loading_state(True)
        self.statusBar().showMessage("正在生成随机点...")

        self.generate_points_worker = AIGeneratePointsWorker(self.ai_manager, n, x_range=(-200, 200), y_range=(-200, 200))
        self.active_workers.add(self.generate_points_worker)
        self.generate_points_worker.finished.connect(lambda res, w=self.generate_points_worker: self.on_generate_points_worker_finished(res, w))
        self.generate_points_worker.error.connect(lambda msg, w=self.generate_points_worker: self.on_ai_worker_error(msg, w))
        self.generate_points_worker.start()

    def on_generate_points_worker_finished(self, result: dict, worker):
        if worker in self.active_workers:
            self.active_workers.remove(worker)
            worker.deleteLater()
        
        self.ai_tools_panel.set_loading_state(False)
        self.statusBar().showMessage("随机点生成完成", 3000)
        
        if result['success']:
            self.ai_tools_panel.set_scatter_points(result['points'])
            for x, y in result['points']:
                self.on_point_added(x, y)

    def on_console_command(self, command: str) -> None:
        if command == '%clear':
            self.central_widget.clear_canvas()
            self.algebra_panel.clear()
            self._objects_data.clear()
            if hasattr(self, 'geometry_engine'):
                self.geometry_engine.clear()
            result = {
                'success': True,
                'output': t('errors.canvas_cleared') + '\n',
                'error': '',
                'more': False,
            }
        elif hasattr(self, 'python_repl'):
            result = self.python_repl.execute(command)
        else:
            result = {
                'success': False,
                'output': '',
                'error': t('errors.python_repl_not_initialized'),
                'more': False,
            }
        self.console.display_result(result)

    def on_command_entered(self, command: str) -> None:
        try:
            parts = command.split('=')
            if len(parts) == 2:
                name  = parts[0].strip()
                value = parts[1].strip()

                if value.startswith('(') and value.endswith(')'):
                    coords = value[1:-1].split(',')
                    if len(coords) == 2:
                        x = float(coords[0].strip())
                        y = float(coords[1].strip())

                        if hasattr(self, 'geometry_engine'):
                            self.geometry_engine.add_point(x, y, name=name)
                        else:
                            obj_id = str(uuid.uuid4())
                            obj_data = {
                                'id': obj_id,
                                'name': name,
                                'type': 'Point',
                                'coordinates': {'x': x, 'y': y},
                            }
                            self._add_object(obj_data)
        except Exception as e:
            QMessageBox.warning(
                self,
                t('dialogs.error'),
                t('dialogs.invalid_command', str(e)),
            )

    # ─────────────────────────────────────────────────────────────
    #  命令面板相关方法
    # ─────────────────────────────────────────────────────────────

    def _show_command_palette(self) -> None:
        """居中显示命令面板层。"""
        self.cmd_palette.show_centered_on(self)

    def _register_commands(self) -> None:
        """向 CommandManager 注册所有默认命令。

        分类设计：
          视图   — 面板切换、dock 显隐
          文件   — 新建、打开、保存、导出
          画布   — 清空、缩放、工具切换
          变量   — 常用数学常量注入
          模板   — 向控制台插入常用公式模板
          系统   — 主题、语言、首选项
        """
        reg = self.cmd_manager.register
        C   = Command

        # ── 视图 ────────────────────────────────────────────────────────
        reg(C('view.algebra',    '显示 代数面板',         lambda: self.algebra_panel.show(),            '视图', 'Ctrl+1'))
        reg(C('view.properties', '显示 属性面板',         lambda: self.properties_panel.show(),        '视图', 'Ctrl+2'))
        reg(C('view.console',    '显示 Python 控制台',      lambda: self.console.show(),                 '视图', 'Ctrl+3'))
        reg(C('view.algo',       '显示 算法可视化面板',   lambda: (self.algo_vis_panel.show(), self.algo_vis_panel.raise_()),  '视图'))
        reg(C('view.ai',         '显示 AI 工具面板',      lambda: (self.ai_tools_panel.show(), self.ai_tools_panel.raise_()),   '视图'))
        reg(C('view.function',   '显示 函数探索器',       lambda: (self.function_explorer.show(), self.function_explorer.raise_()), '视图'))

        reg(C('view.hide.algebra',    '隐藏 代数面板',         lambda: self.algebra_panel.hide(),    '视图'))
        reg(C('view.hide.properties', '隐藏 属性面板',         lambda: self.properties_panel.hide(), '视图'))
        reg(C('view.hide.console',    '隐藏 Python 控制台',      lambda: self.console.hide(),          '视图'))
        reg(C('view.hide.algo',       '隐藏 算法可视化面板',   lambda: self.algo_vis_panel.hide(),   '视图'))
        reg(C('view.hide.ai',         '隐藏 AI 工具面板',      lambda: self.ai_tools_panel.hide(),   '视图'))

        # ── 文件 ────────────────────────────────────────────────────────
        reg(C('file.new',        '新建项目',             self.on_new_project,     '文件', 'Ctrl+N'))
        reg(C('file.open',       '打开项目…',          self.on_open_project,    '文件', 'Ctrl+O'))
        reg(C('file.save',       '保存项目',             self.on_save_project,    '文件', 'Ctrl+S'))
        reg(C('file.save_as',    '另存项目…',          self.on_save_project_as, '文件', 'Ctrl+Shift+S'))
        reg(C('file.export.png', '导出 PNG 图片',         self.on_export_png,      '文件'))
        reg(C('file.export.svg', '导出 SVG 矢量图',       self.on_export_svg,      '文件'))
        reg(C('file.export.tex', '导出 LaTeX 文档',        self.on_export_latex,    '文件'))

        # ── 画布 ────────────────────────────────────────────────────────
        reg(C('canvas.clear',    '清空画布与变量',       self.on_new_project,                          '画布'))
        reg(C('canvas.zoom_in',  '放大画布',             lambda: self.central_widget.zoom_in(),        '画布', 'Ctrl+='))
        reg(C('canvas.zoom_out', '缩小画布',             lambda: self.central_widget.zoom_out(),       '画布', 'Ctrl+-'))
        reg(C('tool.select',     '切换工具: 选择',       lambda: self.on_action_selected('select'),     '画布', 'S'))
        reg(C('tool.point',      '切换工具: 点',         lambda: self.on_action_selected('point'),      '画布', 'P'))
        reg(C('tool.segment',    '切换工具: 线段',       lambda: self.on_action_selected('segment'),    '画布', 'L'))
        reg(C('tool.circle',     '切换工具: 圆',         lambda: self.on_action_selected('circle'),     '画布', 'C'))
        reg(C('tool.polygon',    '切换工具: 多边形',       lambda: self.on_action_selected('polygon'),    '画布', 'G'))
        reg(C('tool.pan',        '切换工具: 平移画布',     lambda: self.on_action_selected('pan'),        '画布', 'H'))

        # ── 笔记本与工作区 ────────────────────────────────────────────────────────
        reg(C('notebook.new',    '新建笔记本 (> new notebook)', lambda: (self.central_tabs.setCurrentWidget(self.notebook), self.notebook.backend.cells.clear(), self._refresh_notebook_ui()), '工作区'))
        reg(C('notebook.run_all','运行全部代码块 (> run all)',   lambda: (self.central_tabs.setCurrentWidget(self.notebook), self.notebook.run_all_cells()), '工作区'))
        reg(C('notebook.clear',  '清空所有输出 (> clear output)', lambda: (self.central_tabs.setCurrentWidget(self.notebook), self.notebook.clear_all_outputs()), '工作区'))
        
        if self.geogebra_panel:
            reg(C('geometry.open', '打开几何画板 (> open geometry)', lambda: self.central_tabs.setCurrentWidget(self.geogebra_panel), '工作区'))

        # ── 变量注入 ────────────────────────────────────────────────────
        def _inject(name, expr):
            self.console.inject_variable(name, expr)

        reg(C('var.pi',     '注入常量: 圆周率 PI',          lambda: _inject('PI',  '3.141592653589793'),  '变量', '', '≈ 3.14159'))
        reg(C('var.e',      '注入常量: 自然常数 E',         lambda: _inject('E',   '2.718281828459045'),  '变量', '', '≈ 2.71828'))
        reg(C('var.phi',    '注入常量: 黄金分割比 PHI',       lambda: _inject('PHI', '1.618033988749895'),  '变量', '', '≈ 1.61803'))
        reg(C('var.sqrt2',  '注入常量: 根号 2 SQRT2',         lambda: _inject('SQRT2', '1.4142135623730951'), '变量', '', '≈ 1.41421'))
        reg(C('var.inf',    '注入常量: 正无穷 INF',          lambda: _inject('INF', 'float("inf")'),       '变量'))
        reg(C('var.deg',    '注入常量: 度转弧系数 DEG2RAD',    lambda: _inject('DEG2RAD', '0.017453292519943295'), '变量', '', '° → rad'))

        # ── 模板插入 ────────────────────────────────────────────────────
        def _insert(text):
            self.console.insert_text_at_cursor(text)

        reg(C('tpl.integrate',   '插入模板: 不定积分',     lambda: _insert('integrate(f, x)'),            '模板'))
        reg(C('tpl.diff',        '插入模板: 导数',         lambda: _insert('diff(f, x)'),                 '模板'))
        reg(C('tpl.limit',       '插入模板: 极限',         lambda: _insert('limit(f, x, 0)'),             '模板'))
        reg(C('tpl.solve',       '插入模板: 方程求解',     lambda: _insert('solve(f, x)'),                '模板'))
        reg(C('tpl.matrix',      '插入模板: 2x2 矩阵',     lambda: _insert('Matrix([[1,0],[0,1]])'),       '模板'))
        reg(C('tpl.plot_sin',    '插入模板: 正弦函数绘图',   lambda: _insert('sin(x)'),                     '模板'))
        reg(C('tpl.plot_cos',    '插入模板: 余弦函数绘图',   lambda: _insert('cos(x)'),                     '模板'))
        reg(C('tpl.plot_normal', '插入模板: 正态分布函数',   lambda: _insert('exp(-x**2/2)'),               '模板'))
        reg(C('tpl.taylor',      '插入模板: Taylor 展开',  lambda: _insert('series(f, x, 0, 6)'),         '模板'))

        # ── 系统 ────────────────────────────────────────────────────────
        reg(C('sys.preferences', '打开首选项',          self.show_preferences_dialog, '系统', 'Ctrl+,'))
        reg(C('sys.theme',       '切换主题 / 深色模式 (> toggle dark mode)', self._toggle_theme, '系统'))
        reg(C('sys.language',    '切换语言',             self.show_language_dialog,    '系统'))
        reg(C('sys.about',       '关于 Axiom Mathematics', self.show_about,              '系统'))
        reg(C('sys.console.clear', '清空控制台',         self.console.clear,           '系统'))
        reg(C('sys.exit',        '退出 MathLab (> exit)',  self.close, '系统', 'Alt+F4'))

        # ── 日志 ────────────────────────────────────────────────────────
        def _open_log_dir():
            """跨平台打开运行日志目录，方便用户拖取日志文件提交 Bug 报告。"""
            try:
                if platform.system() == 'Windows':
                    os.startfile(LOG_DIR)
                elif platform.system() == 'Darwin':
                    subprocess.Popen(['open', LOG_DIR])
                else:
                    subprocess.Popen(['xdg-open', LOG_DIR])
                logger.info("用户打开了日志目录: %s", LOG_DIR)
            except Exception as e:
                logger.error("无法打开日志目录: %s", e)
                if hasattr(self, 'console'):
                    self.console.display_system_message(f"无法打开日志目录: {e}")

        reg(C(
            'sys.open_logs',
            '系统：打开运行日志目录 (Open Logs)',
            _open_log_dir,
            '系统',
            description=f'日志路径: {LOG_DIR}',
        ))

    def on_new_project(self) -> None:
        self.central_widget.clear_canvas()
        self.algebra_panel.clear()
        self.properties_panel.clear()
        self.console.clear()
        self._objects_data.clear()
        if hasattr(self, 'geometry_engine'):
            self.geometry_engine.clear()
        self.current_project = None

    def on_open_project(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t('dialogs.open_project'),
            '',
            'MathLab Files (*.mathlab)',
        )
        if not file_path:
            return
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.on_new_project()

            if hasattr(self, 'geometry_engine'):
                if 'name_counter' in data:
                    self.geometry_engine.deserialize_all(data)
                else:
                    legacy_data = {'name_counter': 1, 'objects': data.get('objects', {})}
                    self.geometry_engine.deserialize_all(legacy_data)
                    
                self._objects_data = {obj.id: obj.serialize() for obj in self.geometry_engine.get_all_objects()}
                for obj in self.geometry_engine.get_all_objects():
                    self.algebra_panel.add_object(obj.serialize())
                    self.central_widget.draw_object(obj.id, obj.serialize())
            else:
                for obj_id, obj_data in data.get('objects', {}).items():
                    self._add_object(obj_data)

            self.current_project = file_path
            self.statusBar().showMessage(t('status_bar.opened', file_path))
        except Exception as e:
            QMessageBox.warning(
                self,
                t('dialogs.error'),
                t('dialogs.failed_to_open', str(e)),
            )

    def on_save_project(self) -> None:
        if self.current_project:
            self._save_project(self.current_project)
        else:
            self.on_save_project_as()

    def on_save_project_as(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t('dialogs.save_project_as'),
            '',
            'MathLab Files (*.mathlab)',
        )
        if file_path:
            if not file_path.endswith('.mathlab'):
                file_path += '.mathlab'
            self._save_project(file_path)

    def _save_project(self, file_path: str) -> None:
        try:
            import json
            if hasattr(self, 'geometry_engine'):
                data = self.geometry_engine.serialize_all()
            else:
                data = {'objects': self._objects_data}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.current_project = file_path
            self.statusBar().showMessage(t('status_bar.saved', file_path))
        except Exception as e:
            QMessageBox.warning(
                self,
                t('dialogs.error'),
                t('dialogs.failed_to_save', str(e)),
            )

    def on_export_png(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, t('dialogs.export_png'), '', 'PNG Files (*.png)'
        )
        if not file_path:
            return
        if not file_path.endswith('.png'):
            file_path += '.png'
        try:
            pixmap = self.central_widget.grab()
            pixmap.save(file_path)
            self.statusBar().showMessage(t('status_bar.exported', file_path))
        except Exception as e:
            QMessageBox.warning(self, t('dialogs.error'), t('dialogs.failed_to_export', str(e)))

    def on_export_svg(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, t('dialogs.export_svg'), '', 'SVG Files (*.svg)'
        )
        if not file_path:
            return
        if not file_path.endswith('.svg'):
            file_path += '.svg'
        try:
            svg_generator = QSvgGenerator()
            svg_generator.setFileName(file_path)

            bounding_rect = self.central_widget.scene().itemsBoundingRect()
            svg_generator.setViewBox(bounding_rect)

            painter = QtPainter(svg_generator)
            painter.setRenderHint(QtPainter.Antialiasing)
            self.central_widget.scene().render(painter)
            painter.end()

            self.statusBar().showMessage(t('status_bar.exported_svg', file_path))
        except Exception as e:
            QMessageBox.warning(self, t('dialogs.error'), t('dialogs.failed_to_export', str(e)))

    def get_themed_icon(self, name: str, theme_name: str = None) -> QIcon:
        """获取带有当前主题前景色渲染的 SVG 图标。"""
        if theme_name is None:
            theme_name = get_current_theme()
        
        icon_path = os.path.join(
            os.path.dirname(__file__), 'icons', f"{name}.svg"
        )
        if not os.path.exists(icon_path):
            return QIcon()
        
        try:
            with open(icon_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            foreground = THEMES.get(theme_name, {}).get('foreground', '#434655')
            svg_content = svg_content.replace('currentColor', foreground)
            
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap()
            pixmap.loadFromData(svg_content.encode('utf-8'), 'SVG')
            return QIcon(pixmap)
        except Exception as e:
            print(f"Warning: Could not load themed icon {name}: {e}")
            return QIcon(icon_path)

    def update_toolbar_icons(self, theme_name: str = None) -> None:
        """刷新工具栏上所有按钮的图标颜色。"""
        if theme_name is None:
            theme_name = get_current_theme()
        
        self.select_action.setIcon(self.get_themed_icon('mouse-pointer', theme_name))
        self.point_action.setIcon(self.get_themed_icon('target', theme_name))
        self.segment_action.setIcon(self.get_themed_icon('segment', theme_name))
        self.circle_action.setIcon(self.get_themed_icon('circle', theme_name))
        self.polygon_action.setIcon(self.get_themed_icon('polygon', theme_name))
        self.pan_action.setIcon(self.get_themed_icon('move', theme_name))
        
        self._zoom_in_action.setIcon(self.get_themed_icon('zoom-in', theme_name))
        self._zoom_out_action.setIcon(self.get_themed_icon('zoom-out', theme_name))
        
        self.settings_btn.setIcon(self.get_themed_icon('settings', theme_name))

    def apply_theme(self, theme_key: str) -> None:
        """全局应用指定主题，并更新主题敏感组件。"""
        if theme_key not in THEMES:
            return
        set_theme(theme_key)
        self.update_toolbar_icons(theme_key)

    def _toggle_theme(self) -> None:
        current = get_current_theme()
        new_theme = 'light' if current == 'dark' else 'dark'
        self.apply_theme(new_theme)

    def _refresh_notebook_ui(self) -> None:
        # 暴力清空 UI 然后让其重新为空
        while self.notebook.scroll_layout.count() > 1: # 结尾有弹簧
            item = self.notebook.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.notebook.ui_cells.clear()
        self.notebook.add_new_cell(self.notebook.backend.add_cell("code", ""))

    def on_export_latex(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, t('dialogs.export_latex'), '', 'LaTeX Files (*.tex)'
        )
        if not file_path:
            return
        if not file_path.endswith('.tex'):
            file_path += '.tex'
        try:
            latex_content = export_canvas_to_latex(list(self._objects_data.values()))
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            self.statusBar().showMessage(t('status_bar.exported_latex', file_path))
        except Exception as e:
            QMessageBox.warning(self, t('dialogs.error'), t('dialogs.failed_to_export', str(e)))

    def toggle_algebra_panel(self, visible: bool) -> None:
        if visible:
            self.algebra_panel.show()
            fade_in(self.algebra_panel)
        else:
            fade_out(self.algebra_panel, callback=self.algebra_panel.hide)

    def toggle_properties_panel(self, visible: bool) -> None:
        if visible:
            self.properties_panel.show()
            fade_in(self.properties_panel)
        else:
            fade_out(self.properties_panel, callback=self.properties_panel.hide)

    def toggle_console(self, visible: bool) -> None:
        if visible:
            self.console.show()
            fade_in(self.console)
        else:
            fade_out(self.console, callback=self.console.hide)

    def toggle_algo_vis_panel(self, visible: bool) -> None:
        if visible:
            self.algo_vis_panel.show()
            self.algo_vis_panel.raise_()
            fade_in(self.algo_vis_panel)
        else:
            fade_out(self.algo_vis_panel, callback=self.algo_vis_panel.hide)

    def toggle_ai_tools_panel(self, visible: bool) -> None:
        if visible:
            self.ai_tools_panel.show()
            self.ai_tools_panel.raise_()
            fade_in(self.ai_tools_panel)
        else:
            fade_out(self.ai_tools_panel, callback=self.ai_tools_panel.hide)

    def toggle_function_explorer(self, visible: bool) -> None:
        if visible:
            self.function_explorer.show()
            self.function_explorer.raise_()
            fade_in(self.function_explorer)
        else:
            fade_out(self.function_explorer, callback=self.function_explorer.hide)

    def toggle_math_console(self, visible: bool) -> None:
        if visible:
            self.math_console.show()
            self.math_console.raise_()
            fade_in(self.math_console)
        else:
            fade_out(self.math_console, callback=self.math_console.hide)

    def toggle_notebook_panel(self, visible: bool) -> None:
        if visible:
            self.notebook.show()
            self.notebook.raise_()
            fade_in(self.notebook)
        else:
            fade_out(self.notebook, callback=self.notebook.hide)

    # ─────────────────────────────────────────────────────────────────────
    # ECharts 图表串联棕函数
    # ─────────────────────────────────────────────────────────────────────

    def handle_console_plot(self, plot_data: dict) -> None:
        """
        槽函数：接收来自 OctaveBridge.signals.plot_requested 的绘图请求。

        将 plot_data 序列化为 JSON 并通过 QWebEngineView.runJavaScript
        推送到 ECharts 前端渲染。

        同时调出 ECharts 插件的 QWebEngineView（通过 plugin_manager API 层展示）。
        """
        import json
        json_str = json.dumps(plot_data, ensure_ascii=False)
        # 调用前端统一入口函数 window.renderPlotData(payload)
        js_code = f"window.renderPlotData({json_str});"

        # 尝试通过 plugin_manager 获取 EChartsViewerPlugin 实例
        web_view = self._get_echarts_webview()
        if web_view is not None:
            web_view.page().runJavaScript(js_code)
        else:
            # 如果 ECharts 插件尚未加载，向控制台显示提示
            self.math_console.display_message(
                '⚠ ECharts 插件未激活，请先加载并打开《高级数据调参》面板。',
                'warn'
            )

    def _get_echarts_webview(self):
        """
        尝试通过 plugin_manager 获取 EChartsViewerPlugin 的 web_view。
        返回 QWebEngineView 实例，若未找到则返回 None。
        """
        if not hasattr(self, 'plugin_manager'):
            return None
        try:
            # plugin_manager 注册的插件通常以类名或 id 为键
            pm = self.plugin_manager
            # 尝试常见的字典路径
            plugins = getattr(pm, 'plugins', None) or getattr(pm, '_plugins', {})
            for key, plugin in (plugins.items() if hasattr(plugins, 'items') else []):
                if hasattr(plugin, 'web_view'):
                    return plugin.web_view
        except Exception:
            pass
        return None

    def show_about(self) -> None:
        QMessageBox.about(self, t('dialogs.about_title'), t('dialogs.about_text'))

    def show_preferences_dialog(self) -> None:
        if PreferencesDialog is None:
            self.show_theme_dialog()
            return
        dlg = PreferencesDialog(self)
        
        def on_theme_changed(name_or_key):
            if name_or_key in THEMES:
                theme_key = name_or_key
            else:
                theme_key = next((k for k, v in THEMES.items() if v['name'] == name_or_key), 'light')
            self.apply_theme(theme_key)
            self.load_stylesheet()

        dlg.theme_changed.connect(on_theme_changed)
        dlg.accent_color_changed.connect(lambda c: None) # reserved for future use
        dlg.font_changed.connect(lambda f, s: None) # reserved for future use
        dlg.graphics_settings_changed.connect(lambda gfx: None) # reserved for future use
        dlg.console_settings_changed.connect(lambda con: None) # reserved for future use
        dlg.advanced_settings_changed.connect(lambda adv: None) # reserved for future use
        dlg.exec()

    def show_theme_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(t('dialogs.select_theme'))
        dialog.setModal(True)
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(t('dialogs.choose_theme')))

        combo = QComboBox()
        current_theme = get_current_theme()
        for theme_id, theme_data in THEMES.items():
            combo.addItem(theme_data['name'], theme_id)
            if theme_id == current_theme:
                combo.setCurrentIndex(combo.count() - 1)
        layout.addWidget(combo)

        btn_layout = QHBoxLayout()
        ok_btn     = QPushButton(t('dialogs.apply'))
        cancel_btn = QPushButton(t('dialogs.cancel'))
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def on_apply():
            self.apply_theme(combo.currentData())
            dialog.accept()

        ok_btn.clicked.connect(on_apply)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def show_language_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(t('dialogs.language'))
        dialog.setModal(True)
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(t('dialogs.choose_language')))

        combo = QComboBox()
        current_lang = get_i18n().get_language()
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            combo.addItem(lang_name, lang_code)
            if lang_code == current_lang:
                combo.setCurrentIndex(combo.count() - 1)
        layout.addWidget(combo)

        btn_layout = QHBoxLayout()
        ok_btn     = QPushButton(t('dialogs.apply'))
        cancel_btn = QPushButton(t('dialogs.cancel'))
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def on_apply():
            get_i18n().set_language(combo.currentData())
            dialog.accept()

        ok_btn.clicked.connect(on_apply)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def _toggle_language(self) -> None:
        current = get_i18n().get_language()
        target = 'zh' if current == 'en' else 'en'
        get_i18n().set_language(target)

    def _on_language_changed(self, lang_code: str) -> None:
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(t('main_window.title'))

        if hasattr(self, 'central_tabs'):
            self.central_tabs.setTabText(0, t('notebook.title') or "Interactive Notebook")
            self.central_tabs.setTabText(1, t('main_window.geometry_tools') or "Geometry Canvas")

        if hasattr(self, 'notebook') and hasattr(self.notebook, 'retranslate_ui'):
            self.notebook.retranslate_ui()

        if hasattr(self, 'properties_panel') and hasattr(self.properties_panel, 'retranslate_ui'):
            self.properties_panel.retranslate_ui()

        self.file_menu.setTitle(t('menu.file'))
        self.edit_menu.setTitle(t('menu.edit'))
        self.view_menu.setTitle(t('menu.view'))
        self.tools_menu.setTitle(t('menu.tools'))
        self.help_menu.setTitle(t('menu.help'))

        self.new_action.setText(t('main_window.new_project'))
        self.open_action.setText(t('main_window.open_project'))
        self.save_action.setText(t('main_window.save_project'))
        self.save_as_action.setText(t('main_window.save_as'))
        self.export_png_action.setText(t('main_window.export_png'))
        self.export_svg_action.setText(t('main_window.export_svg'))
        self.export_latex_action.setText(t('main_window.export_latex'))
        self.exit_action.setText(t('main_window.exit'))

        self.undo_action.setText(t('main_window.undo'))
        self.redo_action.setText(t('main_window.redo'))
        self.delete_action.setText(t('main_window.delete'))

        self.algebra_panel_action.setText(t('main_window.algebra_panel'))
        self.properties_panel_action.setText(t('main_window.properties_panel'))
        self.console_action.setText(t('main_window.console'))
        self.algo_vis_action.setText(t('main_window.algorithm_visualization'))
        self.ai_tools_action.setText(t('main_window.ai_tools'))
        self.theme_action.setText(t('main_window.theme'))
        self.language_action.setText(t('main_window.language'))

        self.geometry_tool_action.setText(t('main_window.geometry_tools'))
        self.algebra_tool_action.setText(t('main_window.algebra_tools'))
        self.ai_tool_action.setText(t('main_window.ai_tools'))

        self.about_action.setText(t('main_window.about'))
        self.tutorial_action.setText(t('main_window.tutorial'))

        self.select_action.setText(t('main_window.select'))
        self.point_action.setText(t('main_window.point'))
        self.segment_action.setText(t('main_window.segment'))
        self.circle_action.setText(t('main_window.circle'))
        self.polygon_action.setText(t('main_window.polygon'))
        self.pan_action.setText(t('main_window.pan'))

        self.preferences_action.setText(t('main_window.preferences'))
        self.ai_menu.setTitle(t('menu.ai'))
        self.ai_scatter_action.setText(t('ai_tools.scatter_fitting'))
        self.ai_cluster_action.setText(t('ai_tools.clustering'))
        self.ai_digit_action.setText(t('ai_tools.digit_recognition'))
        self.ai_train_action.setText(t('ai_tools.training_notebook'))

        self.lang_btn.setToolTip(t('main_window.language'))
        self.settings_btn.setToolTip(t('main_window.preferences'))

        self.algebra_panel.setWindowTitle(t('algebra_panel.title').upper())
        self.properties_panel.setWindowTitle(t('properties_panel.title').upper())
        self.console.setWindowTitle(t('console.title').upper())
        self.algo_vis_panel.setWindowTitle(t('algo_vis.title').upper())
        self.ai_tools_panel.setWindowTitle(t('ai_tools.title').upper())
        # [I18n 修复] 补充遗漏的函数探索器标题刷新
        self.function_explorer.setWindowTitle(t('function_explorer.title').upper())

        self.algebra_panel.retranslate_ui()
        self.properties_panel.retranslate_ui()
        self.console.retranslate_ui()
        self.algo_vis_panel.retranslate_ui()
        self.ai_tools_panel.retranslate_ui()
        # [I18n 修复] 级联调用函数探索器的重绘
        self.function_explorer.retranslate_ui()

    def add_dynamic_panel(self, panel_name: str, widget, icon=None):
        """允许插件添加一个新的 UI 面板到主窗口侧边栏"""
        dock = QDockWidget(panel_name.upper(), self)
        dock.setObjectName(f"dock_dynamic_{panel_name}")
        dock.setWidget(widget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        if hasattr(self, 'ai_tools_panel'):
            self.tabifyDockWidget(self.ai_tools_panel, dock)
        dock.show()
        return dock

    
    def handle_ai_explain(self, full_code, selected_code):
        if hasattr(self, 'ai_dock'):
            self.ai_dock.setVisible(True)
            self.ai_dock.raise_()
        
        user_prompt = prompt_manager.build("code_explainer", full_code=full_code, selected_code=selected_code)
        
        if hasattr(self, 'ai_panel'):
            self.ai_panel.chat_input.setText(user_prompt)
            self.ai_panel.on_send_message()
            
    def closeEvent(self, event):
        """在窗口关闭时卸载所有插件，释放资源"""
        if hasattr(self, 'autosaver'):
            self.autosaver.clean_up()
            
        if hasattr(self, 'plugin_manager'):
            try:
                self.plugin_manager.unload_all()
            except Exception as e:
                print(f"Error unloading plugins on close: {e}")
        # 清理所有活动的异步线程
        for worker in list(self.active_workers):
            try:
                worker.quit()
                worker.wait(1000)
            except Exception:
                pass
                
        if hasattr(self, 'ipc_server') and self.ipc_server is not None:
            self.ipc_server.stop()
            
        # 🛑 优雅关闭 JupyterLab 后台进程
        if hasattr(self, 'jupyter_mgr') and self.jupyter_mgr is not None:
            try:
                self.jupyter_mgr.stop()
            except Exception as e:
                logger.warning("关闭 JupyterLab 后台时出错：%s", e)
        super().closeEvent(event)

