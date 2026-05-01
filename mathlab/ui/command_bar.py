from PySide6.QtWidgets import QLineEdit, QCompleter, QToolBar
from PySide6.QtCore import Qt, Signal

class CommandBar(QToolBar):
    command_entered = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__('Command Bar', parent)
        
        self.command_edit = QLineEdit()
        self.command_edit.setPlaceholderText('Enter command (e.g., A = (1,2), Circle(A, 3))')
        self.command_edit.setStyleSheet("""
            QLineEdit {
                padding: 4px 12px;
                border: 1px solid #c3c6d7;
                border-radius: 4px;
                background-color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #004ac6;
            }
        """)
        
        self.addWidget(self.command_edit)
        
        self.command_edit.returnPressed.connect(self.on_command_entered)
        
        self.setup_completer()
    
    def setup_completer(self):
        commands = [
            'Point', 'Circle', 'Segment', 'Polygon',
            'Line', 'Ray', 'Angle', 'Midpoint',
            'Perpendicular', 'Parallel', 'Intersection',
            'Distance', 'Angle', 'Area', 'Clear'
        ]
        
        self.completer = QCompleter(commands, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.command_edit.setCompleter(self.completer)
    
    def on_command_entered(self):
        command = self.command_edit.text().strip()
        if command:
            self.command_entered.emit(command)
            self.command_edit.clear()
    
    def set_text(self, text):
        self.command_edit.setText(text)
    
    def clear(self):
        self.command_edit.clear()
