from PySide6.QtWidgets import QPlainTextEdit, QCompleter
from PySide6.QtCore import Qt, QStringListModel, Signal
from PySide6.QtGui import QTextCursor, QFont


class AutocompleteTextEdit(QPlainTextEdit):
    request_completions = Signal(str, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.completer = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        self.completer.activated.connect(self.insert_completion)

    def set_completions(self, completions: list):
        if not completions:
            self.completer.popup().hide()
            return

        words = [c['name'] for c in completions]
        model = QStringListModel(words, self.completer)
        self.completer.setModel(model)

        cursor_rect = self.cursorRect()
        cursor_rect.setWidth(self.completer.popup().sizeHintForColumn(0) + 20)
        
        self.completer.complete(cursor_rect)

    def insert_completion(self, completion: str):
        tc = self.textCursor()
        prefix = self.completer.completionPrefix()
        extra = len(completion) - len(prefix)
        
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def text_under_cursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def keyPressEvent(self, event):
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return

        is_shortcut = (event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Space)
        is_trigger_char = (event.key() == Qt.Key_Period)

        super().keyPressEvent(event)

        if is_shortcut or is_trigger_char or event.text().isalnum():
            prefix = self.text_under_cursor()
            if is_trigger_char:
                prefix = ""
            
            self.completer.setCompletionPrefix(prefix)

            cursor = self.textCursor()
            line = cursor.blockNumber() + 1
            column = cursor.columnNumber()
            code_text = self.toPlainText()

            self.request_completions.emit(code_text, line, column)
