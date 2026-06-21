from PySide6.QtWidgets import QPlainTextEdit, QCompleter
from PySide6.QtCore import Qt, QStringListModel, Signal
from PySide6.QtGui import QTextCursor, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QObject, Slot, QUrl
import os

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
        
        if len(prefix) > 0:
            tc.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(prefix))
        tc.insertText(completion)
        self.setTextCursor(tc)
        self.completer.popup().hide()

    def text_under_cursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def keyPressEvent(self, event):
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return):
                self.completer.activated.emit(self.completer.currentCompletion())
                event.accept()
                return
            if event.key() in (Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
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

class Bridge(QObject):
    """通信桥梁：负责接收来自 JS 的信号"""
    execute_requested = Signal(str)

    @Slot(str)
    def receiveCodeExecution(self, code: str):
        """JS 按下 Shift+Enter 时会调用这个函数"""
        self.execute_requested.emit(code)

class MonacoCodeEditor(QWidget):
    """
    基于 VS Code 内核 (Monaco Editor) 的原生封装组件
    你可以像用普通的 QTextEdit 一样使用它
    """
    # 转发桥接器的信号给外部 UI
    execute_requested = Signal(str)

    def __init__(self, initial_text="", parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. 初始化 Web 引擎
        self.browser = QWebEngineView()
        self.layout.addWidget(self.browser)
        
        # 为了美观，给 WebEngine 设置一个背景色，防止加载时闪白光
        self.browser.page().setBackgroundColor(self.palette().color(self.backgroundRole()))

        # 2. 注册通信信道
        self.channel = QWebChannel()
        self.bridge = Bridge()
        # 将信号接通
        self.bridge.execute_requested.connect(self.execute_requested.emit)
        # 暴露给 JS，JS 中通过 channel.objects.pyBridge 访问
        self.channel.registerObject("pyBridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)

        # 3. 读取 HTML 并注入初始代码
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'monaco.html'))
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 替换占位符（注意处理转义字符）
        safe_text = initial_text.replace('\\', '\\\\').replace('`', '\\`')
        html_content = html_content.replace('%INITIAL_CODE%', safe_text)

        # 4. 加载页面
        # 注意：必须设置 baseUrl，否则 qrc:///qtwebchannel/qwebchannel.js 可能加载失败
        base_url = QUrl.fromLocalFile(html_path)
        self.browser.setHtml(html_content, baseUrl=base_url)

    def get_text(self, callback) -> None:
        """
        异步获取编辑器中的代码
        注意：因为跨进程，返回值需要通过 callback(result) 接收
        """
        self.browser.page().runJavaScript("getEditorValue();", callback)

    def set_text(self, text: str) -> None:
        """设置编辑器中的代码"""
        safe_text = text.replace('\\', '\\\\').replace('`', '\\`').replace('\n', '\\n')
        self.browser.page().runJavaScript(f"setEditorValue(`{safe_text}`);")

