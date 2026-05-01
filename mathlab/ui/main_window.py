import os
from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QToolButton,
    QMenuBar, QMenu, QDockWidget, QStatusBar,
    QFileDialog, QMessageBox, QDialog, QVBoxLayout,
    QLabel, QComboBox, QPushButton, QHBoxLayout
)
from PySide6.QtGui import QIcon, QPainter, QAction, QPicture, QPainter as QtPainter
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
    from ..utils.latex_renderer import export_canvas_to_latex
except ImportError:
    from utils.latex_renderer import export_canvas_to_latex

try:
    from ..utils.theme_manager import THEMES, set_theme, get_current_theme
except ImportError:
    from utils.theme_manager import THEMES, set_theme, get_current_theme

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MathLab - Interactive Mathematics')
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_docks()
        
        self.load_stylesheet()
        
        self.current_project = None
        
        self.connect_signals()
    
    def setup_ui(self):
        self.central_widget = GeometryCanvas(self)
        self.setCentralWidget(self.central_widget)
    
    def setup_menus(self):
        menu_bar = QMenuBar(self)
        
        file_menu = QMenu('File', self)
        new_action = QAction('New Project', self)
        open_action = QAction('Open Project', self)
        save_action = QAction('Save Project', self)
        save_as_action = QAction('Save As...', self)
        export_png_action = QAction('Export as PNG', self)
        export_svg_action = QAction('Export as SVG', self)
        export_latex_action = QAction('Export as LaTeX', self)
        exit_action = QAction('Exit', self)
        
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(export_png_action)
        file_menu.addAction(export_svg_action)
        file_menu.addAction(export_latex_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        edit_menu = QMenu('Edit', self)
        undo_action = QAction('Undo', self)
        redo_action = QAction('Redo', self)
        delete_action = QAction('Delete', self)
        
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(delete_action)
        
        view_menu = QMenu('View', self)
        algebra_panel_action = QAction('Algebra Panel', self)
        algebra_panel_action.setCheckable(True)
        algebra_panel_action.setChecked(True)
        
        properties_panel_action = QAction('Properties Panel', self)
        properties_panel_action.setCheckable(True)
        properties_panel_action.setChecked(True)
        
        console_action = QAction('Console', self)
        console_action.setCheckable(True)
        console_action.setChecked(True)
        
        algo_vis_action = QAction('Algorithm Visualization', self)
        algo_vis_action.setCheckable(True)
        
        ai_tools_action = QAction('AI Tools', self)
        ai_tools_action.setCheckable(True)
        
        theme_action = QAction('Theme...', self)
        
        view_menu.addAction(algebra_panel_action)
        view_menu.addAction(properties_panel_action)
        view_menu.addAction(console_action)
        view_menu.addAction(algo_vis_action)
        view_menu.addAction(ai_tools_action)
        view_menu.addSeparator()
        view_menu.addAction(theme_action)
        
        tools_menu = QMenu('Tools', self)
        geometry_tool_action = QAction('Geometry Tools', self)
        algebra_tool_action = QAction('Algebra Tools', self)
        ai_tool_action = QAction('AI Tools', self)
        
        tools_menu.addAction(geometry_tool_action)
        tools_menu.addAction(algebra_tool_action)
        tools_menu.addAction(ai_tool_action)
        
        help_menu = QMenu('Help', self)
        about_action = QAction('About MathLab', self)
        tutorial_action = QAction('Tutorial', self)
        
        help_menu.addAction(tutorial_action)
        help_menu.addAction(about_action)
        
        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(edit_menu)
        menu_bar.addMenu(view_menu)
        menu_bar.addMenu(tools_menu)
        menu_bar.addMenu(help_menu)
        
        self.setMenuBar(menu_bar)
        
        new_action.triggered.connect(self.on_new_project)
        open_action.triggered.connect(self.on_open_project)
        save_action.triggered.connect(self.on_save_project)
        save_as_action.triggered.connect(self.on_save_project_as)
        export_png_action.triggered.connect(self.on_export_png)
        export_svg_action.triggered.connect(self.on_export_svg)
        export_latex_action.triggered.connect(self.on_export_latex)
        exit_action.triggered.connect(self.close)
        
        algebra_panel_action.triggered.connect(self.toggle_algebra_panel)
        properties_panel_action.triggered.connect(self.toggle_properties_panel)
        console_action.triggered.connect(self.toggle_console)
        algo_vis_action.triggered.connect(self.toggle_algo_vis_panel)
        ai_tools_action.triggered.connect(self.toggle_ai_tools_panel)
        
        theme_action.triggered.connect(self.show_theme_dialog)
        
        about_action.triggered.connect(self.show_about)
    
    def setup_toolbar(self):
        self.toolbar = QToolBar('Main Toolbar')
        self.toolbar.setIconSize(QSize(32, 32))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        self.select_action = QAction('Select', self)
        self.select_action.setCheckable(True)
        self.select_action.setChecked(True)
        
        self.point_action = QAction('Point', self)
        self.point_action.setCheckable(True)
        
        self.segment_action = QAction('Segment', self)
        self.segment_action.setCheckable(True)
        
        self.circle_action = QAction('Circle', self)
        self.circle_action.setCheckable(True)
        
        self.polygon_action = QAction('Polygon', self)
        self.polygon_action.setCheckable(True)
        
        self.pan_action = QAction('Pan', self)
        self.pan_action.setCheckable(True)
        
        self.zoom_in_action = QAction('Zoom In', self)
        self.zoom_out_action = QAction('Zoom Out', self)
        
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
        
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        
        self._connect_tool_actions()
        
        self.zoom_in_action.triggered.connect(self.on_zoom_in)
        self.zoom_out_action.triggered.connect(self.on_zoom_out)
    
    def _connect_tool_actions(self):
        actions = [
            ('select', self.select_action),
            ('point', self.point_action),
            ('segment', self.segment_action),
            ('circle', self.circle_action),
            ('polygon', self.polygon_action),
            ('pan', self.pan_action),
        ]
        for tool_name, action in actions:
            action.triggered.connect(lambda checked, t=tool_name: self.on_action_selected(t))
    
    def setup_docks(self):
        self.algebra_panel = AlgebraPanel(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.algebra_panel)
        
        self.properties_panel = PropertiesPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_panel)
        
        self.console = PythonConsole(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console)
        
        self.algo_vis_panel = AlgoVisPanel(self)
        self.algo_vis_panel.hide()
        
        self.ai_tools_panel = AIToolsPanel(self)
        self.ai_tools_panel.hide()
        
        self.tabifyDockWidget(self.algo_vis_panel, self.ai_tools_panel)
    
    def load_stylesheet(self):
        try:
            stylesheet_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ui', 'styles.qss')
            with open(stylesheet_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f'Warning: Could not load stylesheet: {e}')
    
    def connect_signals(self):
        self.central_widget.point_added.connect(self.on_point_added)
        self.algebra_panel.object_selected.connect(self.on_algebra_item_selected)
        self.algebra_panel.object_deleted.connect(self.on_object_deleted)
        self.console.execute_command.connect(self.on_console_command)
        self.command_bar.command_entered.connect(self.on_command_entered)
    
    def on_action_selected(self, tool_name):
        for action in self.tool_actions:
            action.setChecked(False)
        
        action_map = {
            'select': self.select_action,
            'point': self.point_action,
            'segment': self.segment_action,
            'circle': self.circle_action,
            'polygon': self.polygon_action,
            'pan': self.pan_action
        }
        
        if tool_name in action_map:
            action_map[tool_name].setChecked(True)
        
        self.central_widget.set_tool(tool_name)
    
    def on_zoom_in(self):
        self.central_widget.scale(1.2, 1.2)
    
    def on_zoom_out(self):
        self.central_widget.scale(0.8, 0.8)
    
    def on_point_added(self, x, y):
        obj_data = {
            'id': f'point_{id(x)}',
            'name': 'New Point',
            'type': 'Point',
            'coordinates': {'x': x, 'y': y}
        }
        self.algebra_panel.add_object(obj_data)
        self.central_widget.draw_object(obj_data['id'], obj_data)
    
    def on_algebra_item_selected(self, obj_id):
        self.central_widget.select_object(obj_id)
    
    def on_object_deleted(self, obj_id):
        if hasattr(self, 'geometry_engine'):
            self.geometry_engine.remove_object(obj_id)
        else:
            self.central_widget.remove_object(obj_id)
            self.algebra_panel.remove_object(obj_id)
    
    def on_console_command(self, command):
        if command == '%clear':
            self.central_widget.clear_canvas()
            self.algebra_panel.clear()
            result = {'success': True, 'output': 'Canvas cleared', 'error': '', 'more': False}
        elif hasattr(self, 'python_repl'):
            result = self.python_repl.execute(command)
        else:
            result = {'success': False, 'output': '', 'error': 'Python REPL not initialized', 'more': False}
        
        self.console.display_result(result)
    
    def on_command_entered(self, command):
        try:
            parts = command.split('=')
            if len(parts) == 2:
                name = parts[0].strip()
                value = parts[1].strip()
                
                if value.startswith('(') and value.endswith(')'):
                    coords = value[1:-1].split(',')
                    if len(coords) == 2:
                        x, y = float(coords[0].strip()), float(coords[1].strip())
                        obj_data = {
                            'id': f'point_{id(name)}',
                            'name': name,
                            'type': 'Point',
                            'coordinates': {'x': x, 'y': y}
                        }
                        self.algebra_panel.add_object(obj_data)
                        self.central_widget.draw_object(obj_data['id'], obj_data)
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Invalid command: {str(e)}')
    
    def on_new_project(self):
        self.central_widget.clear_canvas()
        self.algebra_panel.clear()
        self.properties_panel.clear()
        self.console.clear()
        self.current_project = None
    
    def on_open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Open Project', '', 'MathLab Files (*.mathlab)'
        )
        if file_path:
            try:
                import json
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                self.on_new_project()
                
                for obj_id, obj_data in data.get('objects', {}).items():
                    self.algebra_panel.add_object(obj_data)
                    self.central_widget.draw_object(obj_id, obj_data)
                
                self.current_project = file_path
                self.statusBar().showMessage(f'Opened: {file_path}')
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Failed to open project: {str(e)}')
    
    def on_save_project(self):
        if self.current_project:
            self._save_project(self.current_project)
        else:
            self.on_save_project_as()
    
    def on_save_project_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Save Project', '', 'MathLab Files (*.mathlab)'
        )
        if file_path:
            if not file_path.endswith('.mathlab'):
                file_path += '.mathlab'
            self._save_project(file_path)
    
    def _save_project(self, file_path):
        try:
            import json
            data = {'objects': {}}
            
            for obj_id, item in self.algebra_panel.object_items.items():
                obj_data = {
                    'id': obj_id,
                    'name': item.text(0),
                    'type': item.data(1, Qt.UserRole),
                    'coordinates': {}
                }
                data['objects'][obj_id] = obj_data
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.current_project = file_path
            self.statusBar().showMessage(f'Saved: {file_path}')
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to save project: {str(e)}')
    
    def on_export_png(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export as PNG', '', 'PNG Files (*.png)'
        )
        if file_path:
            if not file_path.endswith('.png'):
                file_path += '.png'
            try:
                pixmap = self.central_widget.grab()
                pixmap.save(file_path)
                self.statusBar().showMessage(f'Exported: {file_path}')
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Failed to export: {str(e)}')
    
    def on_export_svg(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export as SVG', '', 'SVG Files (*.svg)'
        )
        if file_path:
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
                
                self.statusBar().showMessage(f'Exported SVG: {file_path}')
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Failed to export SVG: {str(e)}')
    
    def on_export_latex(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export as LaTeX', '', 'LaTeX Files (*.tex)'
        )
        if file_path:
            if not file_path.endswith('.tex'):
                file_path += '.tex'
            try:
                objects_data = []
                for obj_id, item in self.algebra_panel.object_items.items():
                    obj_data = {
                        'id': obj_id,
                        'name': item.text(0),
                        'type': item.data(1, Qt.UserRole),
                        'coordinates': {}
                    }
                    objects_data.append(obj_data)
                
                latex_content = export_canvas_to_latex(objects_data)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                
                self.statusBar().showMessage(f'Exported LaTeX: {file_path}')
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Failed to export LaTeX: {str(e)}')
    
    def toggle_algebra_panel(self, visible):
        self.algebra_panel.setVisible(visible)
    
    def toggle_properties_panel(self, visible):
        self.properties_panel.setVisible(visible)
    
    def toggle_console(self, visible):
        self.console.setVisible(visible)
    
    def toggle_algo_vis_panel(self, visible):
        if visible:
            self.algo_vis_panel.show()
            self.tabifyDockWidget(self.algo_vis_panel, self.ai_tools_panel)
            self.algo_vis_panel.raise_()
    
    def toggle_ai_tools_panel(self, visible):
        if visible:
            self.ai_tools_panel.show()
            self.tabifyDockWidget(self.algo_vis_panel, self.ai_tools_panel)
            self.ai_tools_panel.raise_()
    
    def show_about(self):
        QMessageBox.about(self, 'About MathLab',
            'MathLab - Interactive Mathematics and AI Teaching Software\n\n'
            'Version 1.0\n\n'
            'A powerful tool for learning mathematics and AI concepts through interactive visualization.'
        )

    def show_theme_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Select Theme')
        dialog.setModal(True)
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)

        label = QLabel('Choose a theme:')
        layout.addWidget(label)

        combo = QComboBox()
        current_theme = get_current_theme()
        for theme_id, theme_data in THEMES.items():
            combo.addItem(theme_data['name'], theme_id)
            if theme_id == current_theme:
                combo.setCurrentIndex(combo.count() - 1)

        layout.addWidget(combo)

        button_layout = QHBoxLayout()
        ok_button = QPushButton('Apply')
        cancel_button = QPushButton('Cancel')
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        def on_apply():
            selected_theme = combo.currentData()
            set_theme(selected_theme)
            dialog.accept()

        ok_button.clicked.connect(on_apply)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()
