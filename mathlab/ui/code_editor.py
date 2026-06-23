import os
import json
import re
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QObject, Slot, Signal, Qt
from PySide6.QtWebChannel import QWebChannel

try:
    from mathlab.core.jupyter_manager import jupyter_sandbox
except ImportError:
    jupyter_sandbox = None

class EditorBackend(QObject):
    execution_finished = Signal(dict)
    # 增加两个信号：告知主面板错误状态，以便外部处理
    error_occurred = Signal(str, str) 
    success_occurred = Signal()

    def __init__(self, parent_widget):
        super().__init__()
        self.parent_widget = parent_widget

    @Slot(str)
    def execute_code(self, code):
        if not jupyter_sandbox:
            self.execution_finished.emit({"status": "error", "traceback": ["Jupyter 沙盒未就绪"]})
            return

        result = jupyter_sandbox.execute_code(code, timeout=10)
        
        if result['status'] == 'error' or result['status'] == 'timeout':
            error_list = self._parse_traceback(result['traceback'])
            js_cmd = f"setEditorErrors('{json.dumps(error_list)}');"
            self.parent_widget.web_view.page().runJavaScript(js_cmd)
            
            # 记录崩溃时的代码和错误，并触发悬浮按钮
            error_msg = "\n".join(result['traceback'])
            self.error_occurred.emit(code, error_msg)
        else:
            self.parent_widget.web_view.page().runJavaScript("setEditorErrors('[]');")
            self.success_occurred.emit()
            
        self.execution_finished.emit(result)

    def _parse_traceback(self, traceback_list):
        errors = []
        full_trace = "\n".join(traceback_list)
        match = re.search(r'line (\d+)', full_trace, re.IGNORECASE)
        if match:
            line_num = int(match.group(1))
            clean_error = re.sub(r'\x1b\[[0-9;]*m', '', traceback_list[-1])
            errors.append({"line": line_num, "message": clean_error})
        else:
            errors.append({"line": 1, "message": "执行发生错误或超时"})
        return errors


class MathLabCodeEditor(QWidget):
    def __init__(self, ai_manager=None, parent=None):
        super().__init__(parent)
        self.ai_manager = ai_manager # 引入全局 AI 调度中心
        self._last_failed_code = ""
        self._last_error_msg = ""
        self._ai_buffer = "" # 暂存 AI 流式输出的 buffer
        self._build_ui()

    def _build_ui(self):
        # 使用绝对定位来放置悬浮按钮，因此主 Layout 不再管理它
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView(self)
        layout.addWidget(self.web_view)

        self.channel = QWebChannel()
        self.backend = EditorBackend(self)
        self.channel.registerObject("backend", self.backend)
        self.web_view.page().setWebChannel(self.channel)

        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'monaco.html'))
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))

        # --- 新增：智能修复悬浮按钮 ---
        self.fix_btn = QPushButton("✨ AI 自动修复", self.web_view)
        self.fix_btn.setStyleSheet("""
            QPushButton {
                background-color: #7B61FF; color: white;
                border-radius: 15px; padding: 5px 15px;
                font-weight: bold; font-family: 'Segoe UI', Arial;
            }
            QPushButton:hover { background-color: #8C75FF; }
        """)
        self.fix_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fix_btn.hide() # 初始隐藏
        self.fix_btn.clicked.connect(self._start_ai_fix)

        # 绑定后端信号
        self.backend.error_occurred.connect(self._on_execution_error)
        self.backend.success_occurred.connect(self._on_execution_success)

    def resizeEvent(self, event):
        """保持悬浮按钮始终在编辑器右下角"""
        super().resizeEvent(event)
        btn_width, btn_height = 120, 30
        margin_x, margin_y = 30, 30
        self.fix_btn.setGeometry(
            self.width() - btn_width - margin_x,
            self.height() - btn_height - margin_y,
            btn_width, btn_height
        )

    def _on_execution_error(self, code, error_msg):
        self._last_failed_code = code
        self._last_error_msg = error_msg
        self.fix_btn.show() # 代码报错，弹出修复按钮

    def _on_execution_success(self):
        self.fix_btn.hide() # 修复成功或执行成功，隐藏按钮

    def _start_ai_fix(self):
        if not self.ai_manager:
            print("错误：AI Manager 未挂载至编辑器。")
            return

        self.fix_btn.setText("修复中...")
        self.fix_btn.setEnabled(False)
        self._ai_buffer = ""
        
        # 1. 准备严密的 Prompt
        prompt = f"""你是一个高级 Python 几何/数据处理专家。
以下代码在 Jupyter 运行环境中报错了：

【原始代码】
```python
{self._last_failed_code}
```

【报错日志】
{self._last_error_msg}

请定位问题并给出修复后的完整代码。
规则：只返回最终修复的 Python 代码块，必须用 `python 和 ` 包裹，不要输出任何多余的解释语言或 Markdown 结构。"""

        # 2. 清空编辑器，准备打字机渲染
        self.web_view.page().runJavaScript("clearForAIFix();")

        # 3. 调用 AI 引擎的流式接口
        self.ai_manager.ask(
            user_prompt=prompt,
            on_chunk=self._on_ai_chunk,
            on_finish=self._on_ai_finish,
            on_error=self._on_ai_error
        )

    def _on_ai_chunk(self, chunk):
        """流式接收并处理 Markdown 拦截"""
        self._ai_buffer += chunk
        
        # 实时过滤掉 AI 输出的 ```python 和 ``` 标记，实现纯净代码流输入
        display_text = self._ai_buffer
        display_text = re.sub(r'```python\n?', '', display_text)
        display_text = re.sub(r'```\n?', '', display_text)
        
        # 每次清空并全量替换能避免因为正则截断导致的流式乱码问题
        escaped_code = json.dumps(display_text)
        self.web_view.page().runJavaScript(f"window.mathEditor.editor.setValue({escaped_code});")

    def _on_ai_finish(self):
        self.fix_btn.setText("✨ AI 自动修复")
        self.fix_btn.setEnabled(True)
        self.fix_btn.hide()
        
        # 修复完成后，自动帮你按下 Ctrl+Enter 验证代码
        # JS 层可以派发一个按键事件，或者我们直接在后端再调一次 execute_code
        self.web_view.page().runJavaScript("getEditorContent();", self.backend.execute_code)

    def _on_ai_error(self, err_msg):
        self.fix_btn.setText("✨ AI 自动修复")
        self.fix_btn.setEnabled(True)
        print(f"AI 修复失败: {err_msg}")
