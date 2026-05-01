from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QToolButton,
    QMenuBar, QMenu, QDockWidget, QStatusBar,
    QFileDialog, QMessageBox
)
from PySide6.QtGui import QIcon, QPainter, QAction
from PySide6.QtCore import Qt, QSize

from .canvas import GeometryCanvas
from .algebra_panel import AlgebraPanel
from .console import PythonConsole
from .properties_panel import PropertiesPanel
from .command_bar import CommandBar
from .algo_vis_panel import AlgoVisPanel
from .ai_tools_panel import AIToolsPanel

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
        exit_action = QAction('Exit', self)
        
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(export_png_action)
        file_menu.addAction(export_svg_action)
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
        
        view_menu.addAction(algebra_panel_action)
        view_menu.addAction(properties_panel_action)
        view_menu.addAction(console_action)
        view_menu.addAction(algo_vis_action)
        view_menu.addAction(ai_tools_action)
        
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
        exit_action.triggered.connect(self.close)
        
        algebra_panel_action.triggered.connect(self.toggle_algebra_panel)
        properties_panel_action.triggered.connect(self.toggle_properties_panel)
        console_action.triggered.connect(self.toggle_console)
        algo_vis_action.triggered.connect(self.toggle_algo_vis_panel)
        ai_tools_action.triggered.connect(self.toggle_ai_tools_panel)
        
        about_action.triggered.connect(self.show_about)
    
    def setup_toolbar(self):
        self.toolbar = QToolBar('Main Toolbar')
        self.toolbar.setIconSize(QSize(24, 24))
        
        self.select_tool = QToolButton()
        self.select_tool.setText('Select')
        self.select_tool.setCheckable(True)
        self.select_tool.setChecked(True)
        
        self.point_tool = QToolButton()
        self.point_tool.setText('Point')
        self.point_tool.setCheckable(True)
        
        self.segment_tool = QToolButton()
        self.segment_tool.setText('Segment')
        self.segment_tool.setCheckable(True)
        
        self.circle_tool = QToolButton()
        self.circle_tool.setText('Circle')
        self.circle_tool.setCheckable(True)
        
        self.polygon_tool = QToolButton()
        self.polygon_tool.setText('Polygon')
        self.polygon_tool.setCheckable(True)
        
        self.pan_tool = QToolButton()
        self.pan_tool.setText('Pan')
        self.pan_tool.setCheckable(True)
        
        self.zoom_in_tool = QToolButton()
        self.zoom_in_tool.setText('Zoom In')
        
        self.zoom_out_tool = QToolButton()
        self.zoom_out_tool.setText('Zoom Out')
        
        tool_group = [self.select_tool, self.point_tool, self.segment_tool, 
                      self.circle_tool, self.polygon_tool, self.pan_tool]
        
        for tool in tool_group:
            self.toolbar.addWidget(tool)
            tool.clicked.connect(self.on_tool_selected)
        
        self.toolbar.addSeparator()
        
        self.toolbar.addWidget(self.zoom_in_tool)
        self.toolbar.addWidget(self.zoom_out_tool)
        
        self.toolbar.addSeparator()
        
        self.command_bar = CommandBar()
        self.toolbar.addWidget(self.command_bar)
        
        self.addToolBar(self.toolbar)
        
        self.zoom_in_tool.clicked.connect(self.on_zoom_in)
        self.zoom_out_tool.clicked.connect(self.on_zoom_out)
    
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
            with open('mathlab/ui/styles.qss', 'r') as f:
                self.setStyleSheet(f.read())
        except:
            pass
    
    def connect_signals(self):
        self.central_widget.point_added.connect(self.on_point_added)
        self.algebra_panel.object_selected.connect(self.on_algebra_item_selected)
        self.algebra_panel.object_deleted.connect(self.on_object_deleted)
        self.console.execute_command.connect(self.on_console_command)
        self.command_bar.command_entered.connect(self.on_command_entered)
    
    def on_tool_selected(self):
        sender = self.sender()
        
        tools = [self.select_tool, self.point_tool, self.segment_tool, 
                 self.circle_tool, self.polygon_tool, self.pan_tool]
        
        for tool in tools:
            tool.setChecked(tool == sender)
        
        if sender == self.select_tool:
            self.central_widget.set_tool('select')
        elif sender == self.point_tool:
            self.central_widget.set_tool('point')
        elif sender == self.segment_tool:
            self.central_widget.set_tool('segment')
        elif sender == self.circle_tool:
            self.central_widget.set_tool('circle')
        elif sender == self.polygon_tool:
            self.central_widget.set_tool('polygon')
        elif sender == self.pan_tool:
            self.central_widget.set_tool('pan')
    
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
        self.central_widget.remove_object(obj_id)
        self.algebra_panel.remove_object(obj_id)
    
    def on_console_command(self, command):
        result = {'success': True, 'output': '', 'error': '', 'more': False}
        
        if command == '%clear':
            self.central_widget.clear_canvas()
            self.algebra_panel.clear()
            result['output'] = 'Canvas cleared'
        else:
            try:
                exec(command, globals())
                result['output'] = 'Command executed'
            except Exception as e:
                result['error'] = str(e)
                result['success'] = False
        
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
            self.statusBar().showMessage('SVG export not fully implemented yet')
    
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
