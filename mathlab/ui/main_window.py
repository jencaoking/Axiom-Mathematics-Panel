import os
import uuid

from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QToolButton,
    QMenuBar, QMenu, QDockWidget, QStatusBar,
    QFileDialog, QMessageBox, QDialog, QVBoxLayout,
    QLabel, QComboBox, QPushButton, QHBoxLayout
)
from PySide6.QtGui import QAction, QPainter as QtPainter
from PySide6.QtCore import Qt, QSize
from PySide6.QtSvg import QSvgGenerator

from .canvas import GeometryCanvas
from .algebra_panel import AlgebraPanel
from .console import PythonConsole
from .properties_panel import PropertiesPanel
from .command_bar import CommandBar
from .algo_vis_panel import AlgoVisPanel
from .ai_tools_panel import AIToolsPanel

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

        # Runtime object data store (id → obj_data dict) used for save/export
        self._objects_data: dict = {}

        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_docks()

        self.load_stylesheet()

        self.current_project = None

        self.connect_signals()

        # Register for automatic UI retranslation on language change
        get_i18n().add_language_change_listener(self._on_language_changed)

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------
    def setup_ui(self):
        self.central_widget = GeometryCanvas(self)
        self.setCentralWidget(self.central_widget)

    def setup_menus(self):
        menu_bar = QMenuBar(self)

        # ── File menu ──────────────────────────────────────────────────
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

        # ── Edit menu ──────────────────────────────────────────────────
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

        # ── View menu ──────────────────────────────────────────────────
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

        self.theme_action    = QAction(t('main_window.theme'), self)
        self.language_action = QAction(t('main_window.language'), self)

        self.view_menu.addAction(self.algebra_panel_action)
        self.view_menu.addAction(self.properties_panel_action)
        self.view_menu.addAction(self.console_action)
        self.view_menu.addAction(self.algo_vis_action)
        self.view_menu.addAction(self.ai_tools_action)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.theme_action)
        self.view_menu.addAction(self.language_action)
        self.preferences_action = QAction(t('main_window.preferences'), self)
        self.preferences_action.setShortcut('Ctrl+,')
        self.view_menu.addAction(self.preferences_action)

        # ── AI menu ────────────────────────────────────────────────────
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

        # ── Tools menu ─────────────────────────────────────────────────
        self.tools_menu = QMenu(t('menu.tools'), self)

        self.geometry_tool_action = QAction(t('main_window.geometry_tools'), self)
        self.algebra_tool_action  = QAction(t('main_window.algebra_tools'), self)
        self.ai_tool_action       = QAction(t('main_window.ai_tools'), self)

        self.tools_menu.addAction(self.geometry_tool_action)
        self.tools_menu.addAction(self.algebra_tool_action)
        self.tools_menu.addAction(self.ai_tool_action)

        # ── Help menu ──────────────────────────────────────────────────
        self.help_menu = QMenu(t('menu.help'), self)

        self.about_action   = QAction(t('main_window.about'), self)
        self.tutorial_action = QAction(t('main_window.tutorial'), self)

        self.help_menu.addAction(self.tutorial_action)
        self.help_menu.addAction(self.about_action)

        # ── Assemble menu bar ─────────────────────────────────────────
        menu_bar.addMenu(self.file_menu)
        menu_bar.addMenu(self.edit_menu)
        menu_bar.addMenu(self.view_menu)
        menu_bar.addMenu(self.tools_menu)
        menu_bar.addMenu(self.ai_menu)
        menu_bar.addMenu(self.help_menu)

        self.setMenuBar(menu_bar)

        # ── Wire up actions ───────────────────────────────────────────
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
        self.toolbar.setIconSize(QSize(32, 32))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

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

        self.zoom_in_action  = QAction(t('main_window.zoom_in'), self)
        self.zoom_out_action = QAction(t('main_window.zoom_out'), self)

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
        self.toolbar.addAction(self.zoom_in_action)
        self.toolbar.addAction(self.zoom_out_action)
        self.toolbar.addSeparator()

        self.command_bar = CommandBar()
        self.toolbar.addWidget(self.command_bar)

        # ── Right side: Language toggle + Settings ────────────────────
        self.toolbar.addSeparator()
        self.lang_btn = QPushButton('EN/ZH')
        self.lang_btn.setToolTip(t('main_window.language'))
        self.lang_btn.setObjectName('lang_btn')
        self.lang_btn.setFixedHeight(28)
        self.lang_btn.setStyleSheet(
            'QPushButton{background:transparent;border:1px solid #c3c6d7;'
            'border-radius:4px;padding:2px 8px;font-size:11px;font-weight:700;color:#434655;}'
            'QPushButton:hover{background:#e5eeff;border-color:#004ac6;color:#004ac6;}'
        )
        self.lang_btn.clicked.connect(self._toggle_language)
        self.toolbar.addWidget(self.lang_btn)

        self.settings_btn = QPushButton('⚙')
        self.settings_btn.setToolTip(t('main_window.preferences'))
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setStyleSheet(
            'QPushButton{background:transparent;border:none;font-size:16px;color:#434655;}'
            'QPushButton:hover{background:#e5eeff;border-radius:4px;}'
        )
        self.settings_btn.clicked.connect(self.show_preferences_dialog)
        self.toolbar.addWidget(self.settings_btn)

        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self._connect_tool_actions()
        self.zoom_in_action.triggered.connect(self.on_zoom_in)
        self.zoom_out_action.triggered.connect(self.on_zoom_out)

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
        # Qt does not support text-transform in QSS — set title text as uppercase
        self.algebra_panel.setWindowTitle(t('algebra_panel.title').upper())

        self.properties_panel = PropertiesPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_panel)
        self.properties_panel.setWindowTitle(t('properties_panel.title').upper())

        self.console = PythonConsole(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console)
        self.console.setWindowTitle(t('console.title').upper())

        self.algo_vis_panel = AlgoVisPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.algo_vis_panel)
        self.algo_vis_panel.setWindowTitle(t('algo_vis.title').upper())
        self.algo_vis_panel.hide()

        self.ai_tools_panel = AIToolsPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.ai_tools_panel)
        self.ai_tools_panel.setWindowTitle(t('ai_tools.title').upper())
        self.ai_tools_panel.hide()

        self.tabifyDockWidget(self.algo_vis_panel, self.ai_tools_panel)

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
        # Canvas geometry signals
        self.central_widget.point_added.connect(self.on_point_added)
        self.central_widget.segment_added_coords.connect(self.on_segment_added)
        self.central_widget.circle_added_coords.connect(self.on_circle_added)
        self.central_widget.polygon_added_coords.connect(self.on_polygon_added)

        # Panel signals
        self.algebra_panel.object_selected.connect(self.on_algebra_item_selected)
        self.algebra_panel.object_deleted.connect(self.on_object_deleted)
        self.console.execute_command.connect(self.on_console_command)
        self.command_bar.command_entered.connect(self.on_command_entered)

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------
    def _add_object(self, obj_data: dict) -> None:
        """Unified entry point: track, show in panel, and draw on canvas."""
        obj_id = obj_data['id']
        self._objects_data[obj_id] = obj_data
        self.algebra_panel.add_object(obj_data)
        self.central_widget.draw_object(obj_id, obj_data)

    # ------------------------------------------------------------------
    # Tool / zoom handlers
    # ------------------------------------------------------------------
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
        self.central_widget.scale(1.2, 1.2)

    def on_zoom_out(self) -> None:
        self.central_widget.scale(0.8, 0.8)

    # ------------------------------------------------------------------
    # Canvas geometry event handlers
    # ------------------------------------------------------------------
    def on_point_added(self, x: float, y: float) -> None:
        """Slot for GeometryCanvas.point_added — no double-draw."""
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
        """Slot for GeometryCanvas.segment_added_coords."""
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
        """Slot for GeometryCanvas.circle_added_coords."""
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
        """Slot for GeometryCanvas.polygon_added_coords."""
        if hasattr(self, 'geometry_engine'):
            p_ids = [self.geometry_engine.add_point(pt[0], pt[1]) for pt in points]
            self.geometry_engine.add_polygon(p_ids)
        else:
            obj_id = str(uuid.uuid4())
            obj_data = {
                'id': obj_id,
                'name': t('geometry.polygon'),
                'type': 'Polygon',
                'coordinates': {},
                'points': list(points),
            }
            self._add_object(obj_data)

    # ------------------------------------------------------------------
    # Panel interaction handlers
    # ------------------------------------------------------------------
    def on_algebra_item_selected(self, obj_id: str) -> None:
        self.central_widget.select_object(obj_id)

    def on_object_deleted(self, obj_id: str) -> None:
        if hasattr(self, 'geometry_engine'):
            self.geometry_engine.remove_object(obj_id)
        else:
            self.central_widget.remove_object(obj_id)
            self.algebra_panel.remove_object(obj_id)
        self._objects_data.pop(obj_id, None)

    def on_console_command(self, command: str) -> None:
        if command == '%clear':
            self.central_widget.clear_canvas()
            self.algebra_panel.clear()
            self._objects_data.clear()
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
        """Parse a GeoGebra-style command from the command bar."""
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

    # ------------------------------------------------------------------
    # Project management
    # ------------------------------------------------------------------
    def on_new_project(self) -> None:
        self.central_widget.clear_canvas()
        self.algebra_panel.clear()
        self.properties_panel.clear()
        self.console.clear()
        self._objects_data.clear()
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

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Panel visibility toggles
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------
    def show_about(self) -> None:
        QMessageBox.about(self, t('dialogs.about_title'), t('dialogs.about_text'))

    def show_preferences_dialog(self) -> None:
        """Open the full MathLab Settings / Preferences dialog."""
        if PreferencesDialog is None:
            # Fallback to old theme dialog
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
            # set_language triggers _on_language_changed via listener
            get_i18n().set_language(combo.currentData())
            dialog.accept()

        ok_btn.clicked.connect(on_apply)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    # ------------------------------------------------------------------
    # Internationalization
    # ------------------------------------------------------------------
    def _toggle_language(self) -> None:
        """Quick EN ↔ ZH toggle from the toolbar button."""
        current = get_i18n().get_language()
        target = 'zh' if current == 'en' else 'en'
        get_i18n().set_language(target)   # triggers _on_language_changed

    def _on_language_changed(self, lang_code: str) -> None:
        """Automatically called by I18nManager when language changes."""
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Update every translatable string in the window and its children."""
        # Window
        self.setWindowTitle(t('main_window.title'))

        # Menu titles
        self.file_menu.setTitle(t('menu.file'))
        self.edit_menu.setTitle(t('menu.edit'))
        self.view_menu.setTitle(t('menu.view'))
        self.tools_menu.setTitle(t('menu.tools'))
        self.help_menu.setTitle(t('menu.help'))

        # File menu actions
        self.new_action.setText(t('main_window.new_project'))
        self.open_action.setText(t('main_window.open_project'))
        self.save_action.setText(t('main_window.save_project'))
        self.save_as_action.setText(t('main_window.save_as'))
        self.export_png_action.setText(t('main_window.export_png'))
        self.export_svg_action.setText(t('main_window.export_svg'))
        self.export_latex_action.setText(t('main_window.export_latex'))
        self.exit_action.setText(t('main_window.exit'))

        # Edit menu actions
        self.undo_action.setText(t('main_window.undo'))
        self.redo_action.setText(t('main_window.redo'))
        self.delete_action.setText(t('main_window.delete'))

        # View menu actions
        self.algebra_panel_action.setText(t('main_window.algebra_panel'))
        self.properties_panel_action.setText(t('main_window.properties_panel'))
        self.console_action.setText(t('main_window.console'))
        self.algo_vis_action.setText(t('main_window.algorithm_visualization'))
        self.ai_tools_action.setText(t('main_window.ai_tools'))
        self.theme_action.setText(t('main_window.theme'))
        self.language_action.setText(t('main_window.language'))

        # Tools menu actions
        self.geometry_tool_action.setText(t('main_window.geometry_tools'))
        self.algebra_tool_action.setText(t('main_window.algebra_tools'))
        self.ai_tool_action.setText(t('main_window.ai_tools'))

        # Help menu actions
        self.about_action.setText(t('main_window.about'))
        self.tutorial_action.setText(t('main_window.tutorial'))

        # Toolbar actions
        self.select_action.setText(t('main_window.select'))
        self.point_action.setText(t('main_window.point'))
        self.segment_action.setText(t('main_window.segment'))
        self.circle_action.setText(t('main_window.circle'))
        self.polygon_action.setText(t('main_window.polygon'))
        self.pan_action.setText(t('main_window.pan'))
        self.zoom_in_action.setText(t('main_window.zoom_in'))
        self.zoom_out_action.setText(t('main_window.zoom_out'))

        # Preferences & AI menu actions
        self.preferences_action.setText(t('main_window.preferences'))
        self.ai_menu.setTitle(t('menu.ai'))
        self.ai_scatter_action.setText(t('ai_tools.scatter_fitting'))
        self.ai_cluster_action.setText(t('ai_tools.clustering'))
        self.ai_digit_action.setText(t('ai_tools.digit_recognition'))
        self.ai_train_action.setText(t('ai_tools.training_notebook'))

        # Toolbar side buttons tooltip
        self.lang_btn.setToolTip(t('main_window.language'))
        self.settings_btn.setToolTip(t('main_window.preferences'))

        # Dock titles (uppercase for label-caps style)
        self.algebra_panel.setWindowTitle(t('algebra_panel.title').upper())
        self.properties_panel.setWindowTitle(t('properties_panel.title').upper())
        self.console.setWindowTitle(t('console.title').upper())
        self.algo_vis_panel.setWindowTitle(t('algo_vis.title').upper())
        self.ai_tools_panel.setWindowTitle(t('ai_tools.title').upper())

        # Child panels
        self.algebra_panel.retranslate_ui()
        self.properties_panel.retranslate_ui()
        self.console.retranslate_ui()
        self.algo_vis_panel.retranslate_ui()
        self.ai_tools_panel.retranslate_ui()
