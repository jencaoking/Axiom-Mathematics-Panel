from PySide6.QtWidgets import (
    QDockWidget, QTreeWidget, QTreeWidgetItem, QMenu,
    QAbstractItemView, QHeaderView
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal

class AlgebraPanel(QDockWidget):
    object_selected = Signal(str)
    object_renamed = Signal(str, str)
    object_deleted = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__('Algebra', parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(['Name', 'Value'])
        self.tree_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree_widget.header().setSectionResizeMode(1, QHeaderView.Stretch)
        
        self.setWidget(self.tree_widget)
        
        self.object_items = {}
        
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)
    
    def add_object(self, obj_data):
        obj_id = obj_data['id']
        obj_name = obj_data['name']
        obj_type = obj_data['type']
        
        item = QTreeWidgetItem([obj_name, self.format_value(obj_data)])
        item.setData(0, Qt.UserRole, obj_id)
        item.setData(1, Qt.UserRole, obj_type)
        
        self.tree_widget.addTopLevelItem(item)
        self.object_items[obj_id] = item
    
    def update_object(self, obj_data):
        obj_id = obj_data['id']
        
        if obj_id in self.object_items:
            item = self.object_items[obj_id]
            item.setText(0, obj_data['name'])
            item.setText(1, self.format_value(obj_data))
    
    def remove_object(self, obj_id):
        if obj_id in self.object_items:
            item = self.object_items[obj_id]
            index = self.tree_widget.indexOfTopLevelItem(item)
            self.tree_widget.takeTopLevelItem(index)
            del self.object_items[obj_id]
    
    def format_value(self, obj_data):
        obj_type = obj_data['type']
        coords = obj_data.get('coordinates', {})
        
        if obj_type == 'Point':
            x = coords.get('x', 0)
            y = coords.get('y', 0)
            return f'({x:.2f}, {y:.2f})'
        elif obj_type == 'Segment':
            return 'Segment'
        elif obj_type == 'Circle':
            cx = coords.get('cx', 0)
            cy = coords.get('cy', 0)
            r = coords.get('r', 1)
            return f'Center ({cx:.2f}, {cy:.2f}), Radius {r:.2f}'
        else:
            return str(coords)
    
    def on_item_clicked(self, item, column):
        obj_id = item.data(0, Qt.UserRole)
        self.object_selected.emit(obj_id)
    
    def on_item_double_clicked(self, item, column):
        obj_id = item.data(0, Qt.UserRole)
        obj_name = item.text(0)
        
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.tree_widget.editItem(item, 0)
        
        self.tree_widget.itemChanged.connect(lambda i, col: self.on_item_edited(i, col, obj_id))
    
    def on_item_edited(self, item, column, obj_id):
        new_name = item.text(0)
        self.object_renamed.emit(obj_id, new_name)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.tree_widget.itemChanged.disconnect()
    
    def show_context_menu(self, position):
        item = self.tree_widget.itemAt(position)
        if not item:
            return
        
        obj_id = item.data(0, Qt.UserRole)
        
        menu = QMenu()
        
        rename_action = QAction('Rename', self)
        rename_action.triggered.connect(lambda: self.on_item_double_clicked(item, 0))
        
        delete_action = QAction('Delete', self)
        delete_action.triggered.connect(lambda: self.object_deleted.emit(obj_id))
        
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        
        menu.exec_(self.tree_widget.mapToGlobal(position))
    
    def clear(self):
        self.tree_widget.clear()
        self.object_items.clear()
