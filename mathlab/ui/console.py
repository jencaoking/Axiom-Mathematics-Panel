from PySide6.QtWidgets import (
    QDockWidget, QPlainTextEdit, QLineEdit, QWidget, QVBoxLayout,
    QPushButton, QHBoxLayout, QLabel
)
from PySide6.QtGui import QTextCursor, QFont
from PySide6.QtCore import Qt, Signal, Slot, QTimer

try:
    from ..utils.i18n_manager import t
except ImportError:
    from utils.i18n_manager import t

class PythonConsole(QDockWidget):
    execute_command = Signal(str)
    stop_execution = Signal()

    def __init__(self, parent=None):
        super().__init__(t('console.title'), parent)
        self.setAllowedAreas(Qt.BottomDockWidgetArea)

        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # ── Header row: Execute / Stop  ──────  Python 3 | Kernel: Ready ──
        self.execute_button = QPushButton(t('console.execute'))
        self.stop_button = QPushButton(t('console.stop'))
        self.stop_button.setEnabled(False)

        self.kernel_status_label = QLabel(t('console.kernel_ready'))
        self.kernel_status_label.setStyleSheet(
            "color: #737686; font-size: 12px;"
        )
        self.kernel_status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(6, 4, 8, 4)
        self.header_layout.setSpacing(6)
        self.header_layout.addWidget(self.execute_button)
        self.header_layout.addWidget(self.stop_button)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.kernel_status_label)
        self.layout.addLayout(self.header_layout)

        self.output_area = QPlainTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont('Consolas', 12))
        self.output_area.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, monospace;
                border: none;
            }
        """)

        self.input_line = QLineEdit()
        self.input_line.setFont(QFont('Consolas', 12))
        self.input_line.setPlaceholderText(t('console.placeholder'))
        self.input_line.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                font-family: Consolas, monospace;
                border: none;
                padding: 6px;
            }
        """)

        self.layout.addWidget(self.output_area)
        self.layout.addWidget(self.input_line)

        self.setWidget(self.widget)

        self.history = []
        self.history_index = -1

        self.input_line.returnPressed.connect(self.on_execute)
        self.execute_button.clicked.connect(self.on_execute)
        self.stop_button.clicked.connect(self.on_stop)

        self.input_line.installEventFilter(self)

        self.append_output(t('console.welcome') + '\n')
        self.append_output(t('console.help_hint') + '\n')
        self.append_prompt()

    def eventFilter(self, obj, event):
        if obj == self.input_line:
            try:
                if event.type() == Qt.KeyPress:
                    if event.key() == Qt.Key_Up:
                        self.navigate_history(-1)
                        return True
                    elif event.key() == Qt.Key_Down:
                        self.navigate_history(1)
                        return True
                    elif event.key() == Qt.Key_Tab:
                        self.complete_command()
                        return True
            except:
                pass
        return False

    def append_output(self, text):
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.output_area.setTextCursor(cursor)
        self.output_area.ensureCursorVisible()

    def append_prompt(self):
        self.append_output('>>> ')

    def on_execute(self):
        command = self.input_line.text().strip()
        if not command:
            return

        self.history.append(command)
        self.history_index = len(self.history)

        self.append_output(command + '\n')
        self.input_line.clear()

        self.execute_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.execute_command.emit(command)

    def on_stop(self):
        self.stop_execution.emit()
        self.append_output('\n' + t('console.execution_stopped') + '\n')
        self.append_prompt()

        self.execute_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def display_result(self, result):
        if result.get('output'):
            self.append_output(result['output'])

        if result.get('error'):
            self.append_output(f'Error: {result["error"]}\n')

        if not result.get('more', False):
            self.append_prompt()

        self.execute_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def navigate_history(self, direction):
        if not self.history:
            return

        self.history_index += direction

        if self.history_index < 0:
            self.history_index = 0
        elif self.history_index >= len(self.history):
            self.history_index = len(self.history)
            self.input_line.clear()
            return

        self.input_line.setText(self.history[self.history_index])

    def complete_command(self):
        current_text = self.input_line.text()
        if not current_text:
            return

        words = current_text.split()
        if not words:
            return

        last_word = words[-1]
        completions = self.get_completions(last_word)

        if len(completions) == 1:
            self.input_line.setText(current_text[:-len(last_word)] + completions[0])
        elif len(completions) > 1:
            self.append_output('\n'.join(completions) + '\n')
            self.append_prompt()
            self.input_line.setText(current_text)

    def get_completions(self, prefix):
        common_commands = [
            'draw_point', 'draw_segment', 'draw_circle',
            'clear_canvas', 'solve', 'simplify',
            'integrate', 'differentiate', 'limit'
        ]

        return [cmd for cmd in common_commands if cmd.startswith(prefix)]

    def retranslate_ui(self):
        self.setWindowTitle(t('console.title'))
        self.input_line.setPlaceholderText(t('console.placeholder'))
        self.execute_button.setText(t('console.execute'))
        self.stop_button.setText(t('console.stop'))
        self.kernel_status_label.setText(t('console.kernel_ready'))

    def clear(self):
        self.output_area.clear()
        self.append_output(t('console.welcome') + '\n')
        self.append_prompt()
