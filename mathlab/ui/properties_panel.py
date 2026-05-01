from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QDoubleSpinBox, QPushButton, QLabel
)
from PySide6.QtCore import Signal, Qt

try:
    from ..utils.i18n_manager import t
except ImportError:
    from utils.i18n_manager import t

class PropertiesPanel(QDockWidget):
    property_changed = Signal(str, str, object)
    object_renamed = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(t('properties_panel.title'), parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)
        
        self.form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.type_label = QLabel()
        self.x_spin = QDoubleSpinBox()
        self.y_spin = QDoubleSpinBox()
        self.radius_spin = QDoubleSpinBox()
        
        self.x_spin.setRange(-1000, 1000)
        self.y_spin.setRange(-1000, 1000)
        self.radius_spin.setRange(0.1, 1000)
        
        self.form_layout.addRow(t('properties_panel.name') + ':', self.name_edit)
        self.form_layout.addRow(t('properties_panel.type') + ':', self.type_label)
        self.form_layout.addRow(t('properties_panel.x') + ':', self.x_spin)
        self.form_layout.addRow(t('properties_panel.y') + ':', self.y_spin)
        self.form_layout.addRow('Radius:', self.radius_spin)
        
        self.apply_button = QPushButton(t('dialogs.apply'))
        self.apply_button.clicked.connect(self.on_apply)
        
        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.apply_button)
        self.layout.addStretch()
        
        self.setWidget(self.widget)
        
        self.current_obj_id = None
        self.current_obj_type = None
        
        self.name_edit.textChanged.connect(self.on_name_changed)
        self.x_spin.valueChanged.connect(self.on_x_changed)
        self.y_spin.valueChanged.connect(self.on_y_changed)
        self.radius_spin.valueChanged.connect(self.on_radius_changed)
    
    def set_object(self, obj_data):
        self.current_obj_id = obj_data['id']
        self.current_obj_type = obj_data['type']
        
        self.name_edit.setText(obj_data.get('name', ''))
        self.type_label.setText(obj_data.get('type', ''))
        
        coords = obj_data.get('coordinates', {})
        
        if self.current_obj_type == 'Point':
            self.x_spin.setValue(coords.get('x', 0))
            self.y_spin.setValue(coords.get('y', 0))
            self.x_spin.show()
            self.y_spin.show()
            self.radius_spin.hide()
        elif self.current_obj_type == 'Circle':
            self.x_spin.setValue(coords.get('cx', 0))
            self.y_spin.setValue(coords.get('cy', 0))
            self.radius_spin.setValue(coords.get('r', 1))
            self.x_spin.show()
            self.y_spin.show()
            self.radius_spin.show()
        else:
            self.x_spin.hide()
            self.y_spin.hide()
            self.radius_spin.hide()
    
    def clear(self):
        self.name_edit.clear()
        self.type_label.clear()
        self.x_spin.setValue(0)
        self.y_spin.setValue(0)
        self.radius_spin.setValue(1)
        self.current_obj_id = None
        self.current_obj_type = None
    
    def on_name_changed(self, text):
        if self.current_obj_id:
            self.object_renamed.emit(self.current_obj_id, text)
    
    def on_x_changed(self, value):
        if self.current_obj_id and self.current_obj_type == 'Point':
            self.property_changed.emit(self.current_obj_id, 'x', value)
        elif self.current_obj_id and self.current_obj_type == 'Circle':
            self.property_changed.emit(self.current_obj_id, 'cx', value)
    
    def on_y_changed(self, value):
        if self.current_obj_id and self.current_obj_type == 'Point':
            self.property_changed.emit(self.current_obj_id, 'y', value)
        elif self.current_obj_id and self.current_obj_type == 'Circle':
            self.property_changed.emit(self.current_obj_id, 'cy', value)
    
    def on_radius_changed(self, value):
        if self.current_obj_id and self.current_obj_type == 'Circle':
            self.property_changed.emit(self.current_obj_id, 'r', value)
    
    def on_apply(self):
        if self.current_obj_id:
            pass
