import os
import uuid

from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QToolButton,
    QMenuBar, QMenu, QDockWidget, QStatusBar,
    QFileDialog, QMessageBox, QDialog, QVBoxLayout,
    QLabel, QComboBox, QPushButton, QHBoxLayout,
    QSpacerItem, QSizePolicy
)
from PySide6.QtGui import QAction, QPainter as QtPainter, QShortcut, QKeySequence
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

try:
    from core.geometry_engine import GeometryEngine
    from core.python_repl import PythonREPL
    from core.ai_manager import AIManager
    from core.cas_provider import CASProvider
    from core.async_workers import AIFitWorker, AIClusterWorker, AIRecognizeWorker, AIGeneratePointsWorker
    from core.command_manager import CommandManager, Command
except ImportError:
    from ..core.geometry_engine import GeometryEngine
    from ..core.python_repl import PythonREPL
    from ..core.ai_manager import AIManager
    from ..core.cas_provider import CASProvider
    from ..core.async_workers import AIFitWorker, AIClusterWorker, AIRecognizeWorker, AIGeneratePointsWorker
    from ..core.command_manager import CommandManager, Command

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

        # 命令管理器（必须在 setup_ui 前创建，供各面板注册命令）
        self.cmd_manager = CommandManager()

        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_docks()

        self.load_stylesheet()

        self.current_project = None

        self.active_workers = set()

        self.connect_signals()
        self._register_commands()  # 注册命令面板命令

        get_i18n().add_language_change_listener(self._on_language_changed)

    def setup_ui(self):
        self.central_widget = GeometryCanvas(self)
        self.setCentralWidget(self.central_widget)

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

        self.function_explorer_action = QAction(t('function_explorer.title'), self)
        self.function_explorer_action.setCheckable(True)

        self.theme_action    = QAction(t('main_window.theme'), self)
        self.language_action = QAction(t('main_window.language'), self)

        self.view_menu.addAction(self.algebra_panel_action)
        self.view_menu.addAction(self.properties_panel_action)
        self.view_menu.addAction(self.console_action)
        self.view_menu.addAction(self.algo_vis_action)
        self.view_menu.addAction(self.ai_tools_action)
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

        self.tools_menu.addAction(self.geometry_tool_action)
        self.tools_menu.addAction(self.algebra_tool_action)
        self.tools_menu.addAction(self.ai_tool_action)

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
        self.ai_tools_action.triggered.connect(self.toggle_ai_tools_panel)
        self.function_explorer_action.triggered.connect(self.toggle_function_explorer)

        self.theme_action.triggered.connect(self.show_theme_dialog)
        self.language_action.triggered.connect(self.show_language_dialog)
        self.preferences_action.triggered.connect(self.show_preferences_dialog)

        self.ai_scatter_action.triggered.connect(lambda: self.toggle_ai_tools_panel(True))
        self.ai_cluster_action.triggered.connect(lambda: self.toggle_ai_tools_panel(True))
        self.ai_digit_action.triggered.connect(lambda: self.toggle_ai_tools_panel(True))
        self.ai_train_action.triggered.connect(lambda: self.toggle_ai_tools_panel(True))

        self.about_action.triggered.connect(self.show_about)

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
            '  font-size:16px;'
            '  color:#434655;'
            '}'
            'QPushButton:hover{'
            '  background:#e5eeff;'
            '  border-radius:4px;'
            '  color:#004ac6;'
            '}'
        )
        self.settings_btn.setText('⚙')
        self.settings_btn.clicked.connect(self.show_preferences_dialog)
        self.toolbar.addWidget(self.settings_btn)

        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self._connect_tool_actions()

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

    def load_stylesheet(self):
        try:
            stylesheet_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 'ui', 'styles.qss'
            )
            with open(stylesheet_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f'Warning: Could not load stylesheet: {e}')

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
            # TODO: 后续需要实现颜色、透明度等属性的同步逻辑
            # self.properties_panel.color_changed.connect(self.on_object_color_changed)
        self.console.execute_command.connect(self.on_console_command)
        self.command_bar.command_entered.connect(self.on_command_entered)

        self.ai_tools_panel.action_requested.connect(self.execute_ai_action)
        self.ai_tools_panel.fit_requested.connect(self.on_ai_fit_requested)
        self.ai_tools_panel.cluster_requested.connect(self.on_ai_cluster_requested)
        self.ai_tools_panel.recognize_requested.connect(self.on_ai_recognize_requested)
        self.ai_tools_panel.generate_points.connect(self.on_ai_generate_points)

        self.ai_tools_panel.code_editor.request_completions.connect(self.on_code_completion_requested)

        # 连接函数探索器信号
        self.function_explorer.function_added.connect(self.on_function_added)
        self.function_explorer.function_updated.connect(self.on_function_updated)

    def on_code_completion_requested(self, code_text: str, line: int, column: int):
        if hasattr(self, 'python_repl'):
            completions = self.python_repl.get_completions(code_text, line, column)
            self.ai_tools_panel.code_editor.set_completions(completions)

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
            
            # 保存原始表达式和参数信息到对象中
            obj = self.geometry_engine.get_object(obj_id)
            if obj:
                obj.original_expression = expression
                obj.parameters = func_data.get('parameters', {})
        except Exception as e:
            QMessageBox.warning(self, t('dialogs.error'), 
                              f"{t('errors.invalid_expression')}: {str(e)}")
    
    def on_function_updated(self, func_data: dict):
        """处理函数探索器更新的函数（参数变化）"""
        try:
            plot_type = func_data.get('plot_type', 'FunctionPlot')
            expression = func_data.get('expression', '')
            original_expr = func_data.get('original_expression', expression)
            
            if not expression:
                return
            
            # 使用保存的 current_function_id 定位对象，而非假设最后一个
            obj_id = self.current_function_id
            if obj_id:
                last_func = self.geometry_engine.get_object(obj_id)
                if last_func and hasattr(last_func, '_generate_points'):
                    last_func.expression = expression
                    last_func._generate_points()
                    
                    # 通知更新
                    self.on_geometry_event('object_updated', last_func.serialize())
        except Exception as e:
            print(f"Error updating function: {e}")

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
        
        if obj.type == 'Line' or obj.type == 'Segment':
            new_coords = self.cas_provider.extract_line_control_points(new_equation)
            if len(new_coords) >= 2:
                self.geometry_engine.block_signals(True)
                
                if obj.type == 'Line':
                    p1_id = obj.point1_id
                    p2_id = obj.point2_id
                else:
                    p1_id = obj.point1_id
                    p2_id = obj.point2_id
                
                self.geometry_engine.update_point(p1_id, x=new_coords[0][0], y=new_coords[0][1])
                self.geometry_engine.update_point(p2_id, x=new_coords[1][0], y=new_coords[1][1])
                
                self.geometry_engine.block_signals(False)
                obj.update_coordinates(self.geometry_engine)
                self.on_geometry_event('object_updated', obj.serialize())

    def execute_ai_action(self, action_data: dict) -> None:
        action = action_data.get('action')
        
        if action == 'add_point':
            x = action_data.get('x', 0.0)
            y = action_data.get('y', 0.0)
            name = action_data.get('name', '')
            if hasattr(self, 'geometry_engine'):
                self.geometry_engine.add_point(x, y, name=name)
            else:
                # 移除错误的第三个参数，on_point_added 只接受2个参数
                self.on_point_added(x, y)
        
        elif action == 'add_segment':
            point1_id = action_data.get('point1_id')
            point2_id = action_data.get('point2_id')
            if point1_id and point2_id and hasattr(self, 'geometry_engine'):
                self.geometry_engine.add_segment(point1_id, point2_id)
        
        elif action == 'add_circle':
            center_id = action_data.get('center_id')
            radius = action_data.get('radius', 1.0)
            if center_id and hasattr(self, 'geometry_engine'):
                self.geometry_engine.add_circle(center_id, radius)
        
        elif action == 'add_polygon':
            point_ids = action_data.get('point_ids', [])
            if len(point_ids) >= 3 and hasattr(self, 'geometry_engine'):
                self.geometry_engine.add_polygon(point_ids)
        
        elif action == 'update_point':
            point_id = action_data.get('point_id')
            x = action_data.get('x')
            y = action_data.get('y')
            if point_id and (x is not None or y is not None) and hasattr(self, 'geometry_engine'):
                kwargs = {}
                if x is not None:
                    kwargs['x'] = x
                if y is not None:
                    kwargs['y'] = y
                self.geometry_engine.update_point(point_id, **kwargs)
        
        elif action == 'remove_object':
            obj_id = action_data.get('obj_id')
            if obj_id:
                self.on_object_deleted(obj_id)
        
        elif action == 'clear':
            self.on_console_command('%clear')
        
        elif action == 'solve':
            expression = action_data.get('expression', '')
            if expression and hasattr(self, 'cas_provider'):
                result = self.cas_provider.solve_equation(expression, 'x')
                if result.get('success'):
                    self.console.display_result({
                        'success': True,
                        'output': str(result.get('result', '')),
                        'error': '',
                        'more': False
                    })

    def on_ai_fit_requested(self, points: list, model_type: str, params: dict = None) -> None:
        if not points:
            return

        if params is None:
            params = {}

        self.ai_tools_panel.set_loading_state(True)
        self.statusBar().showMessage(f"正在训练 {model_type} 模型，请稍候...")

        self.fit_worker = AIFitWorker(self.ai_manager, points, model_type, **params)
        self.active_workers.add(self.fit_worker)
        self.fit_worker.finished.connect(lambda res: self.on_ai_worker_finished(res, self.fit_worker))
        self.fit_worker.error.connect(lambda msg: self.on_ai_worker_error(msg, self.fit_worker))
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

        self.ai_tools_panel.set_loading_state(True)
        self.statusBar().showMessage(f"正在进行 {method} 聚类分析...")

        self.cluster_worker = AIClusterWorker(self.ai_manager, points, method, params)
        self.active_workers.add(self.cluster_worker)
        self.cluster_worker.finished.connect(lambda res: self.on_ai_worker_finished(res, self.cluster_worker))
        self.cluster_worker.error.connect(lambda msg: self.on_ai_worker_error(msg, self.cluster_worker))
        self.cluster_worker.start()

    def on_ai_recognize_requested(self, image_data: list) -> None:
        self.ai_tools_panel.set_loading_state(True)
        self.statusBar().showMessage("正在识别数字...")

        self.recognize_worker = AIRecognizeWorker(self.ai_manager, image_data)
        self.active_workers.add(self.recognize_worker)
        self.recognize_worker.finished.connect(lambda res: self.on_ai_worker_finished(res, self.recognize_worker))
        self.recognize_worker.error.connect(lambda msg: self.on_ai_worker_error(msg, self.recognize_worker))
        self.recognize_worker.start()

    def on_ai_worker_error(self, error_msg: str, worker=None):
        if worker and worker in self.active_workers:
            self.active_workers.remove(worker)
            worker.deleteLater()
        
        self.ai_tools_panel.set_loading_state(False)
        self.statusBar().showMessage(f"后台运算出错: {error_msg}", 5000)

    def on_ai_generate_points(self, n: int) -> None:
        self.ai_tools_panel.set_loading_state(True)
        self.statusBar().showMessage("正在生成随机点...")

        self.generate_points_worker = AIGeneratePointsWorker(self.ai_manager, n, x_range=(-200, 200), y_range=(-200, 200))
        self.active_workers.add(self.generate_points_worker)
        self.generate_points_worker.finished.connect(lambda res: self.on_generate_points_worker_finished(res, self.generate_points_worker))
        self.generate_points_worker.error.connect(lambda msg: self.on_ai_worker_error(msg, self.generate_points_worker))
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
        reg(C('sys.theme',       '切换主题',             self.show_theme_dialog,       '系统'))
        reg(C('sys.language',    '切换语言',             self.show_language_dialog,    '系统'))
        reg(C('sys.about',       '关于 Axiom Mathematics', self.show_about,              '系统'))
        reg(C('sys.console.clear', '清空控制台',         self.console.clear,           '系统'))

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

            if hasattr(self, 'geometry_engine') and 'name_counter' in data:
                self.geometry_engine.deserialize_all(data)
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
        self.algebra_panel.setVisible(visible)

    def toggle_properties_panel(self, visible: bool) -> None:
        self.properties_panel.setVisible(visible)

    def toggle_console(self, visible: bool) -> None:
        self.console.setVisible(visible)

    def toggle_algo_vis_panel(self, visible: bool) -> None:
        if visible:
            self.algo_vis_panel.show()
            self.algo_vis_panel.raise_()
        else:
            self.algo_vis_panel.hide()

    def toggle_ai_tools_panel(self, visible: bool) -> None:
        if visible:
            self.ai_tools_panel.show()
            self.ai_tools_panel.raise_()
        else:
            self.ai_tools_panel.hide()

    def toggle_function_explorer(self, visible: bool) -> None:
        if visible:
            self.function_explorer.show()
            self.function_explorer.raise_()
        else:
            self.function_explorer.hide()

    def show_about(self) -> None:
        QMessageBox.about(self, t('dialogs.about_title'), t('dialogs.about_text'))

    def show_preferences_dialog(self) -> None:
        if PreferencesDialog is None:
            self.show_theme_dialog()
            return
        dlg = PreferencesDialog(self)
        dlg.theme_changed.connect(lambda name: set_theme(
            next((k for k, v in THEMES.items() if v['name'] == name), 'light')
        ))
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
            set_theme(combo.currentData())
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

        self.algebra_panel.retranslate_ui()
        self.properties_panel.retranslate_ui()
        self.console.retranslate_ui()
        self.algo_vis_panel.retranslate_ui()
        self.ai_tools_panel.retranslate_ui()

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

    def closeEvent(self, event):
        """在窗口关闭时卸载所有插件，释放资源"""
        if hasattr(self, 'plugin_manager'):
            try:
                self.plugin_manager.unload_all()
            except Exception as e:
                print(f"Error unloading plugins on close: {e}")
        # 清理所有活动的异步线程
        for worker in list(self.active_workers):
            try:
                worker.terminate()
                worker.wait()
            except Exception:
                pass
        super().closeEvent(event)

