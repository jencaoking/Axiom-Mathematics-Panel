"""
MathLab Advanced Code Editor
结合 Monaco Editor (前端) 与 Jupyter Sandbox (后端) 的智能编辑器组件
"""

import os
import json
import re
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QObject, Slot, Signal
from PySide6.QtWebChannel import QWebChannel

# 导入我们在之前建立的 Jupyter 安全沙盒
try:
    from mathlab.core.jupyter_manager import jupyter_sandbox
except ImportError:
    jupyter_sandbox = None
    print("警告: 未检测到 Jupyter 沙盒，代码将无法执行。")

class EditorBackend(QObject):
    """
    供 JavaScript (Monaco) 调用的 Python 后端对象
    负责接收前端指令、执行沙盒代码，并将结果或报错信息传回前端。
    """
    
    # 定义一个信号，用于将执行结果发送给外部（比如 Console 面板去渲染图片和文本）
    execution_finished = Signal(dict)

    def __init__(self, parent_widget):
        super().__init__()
        self.parent_widget = parent_widget

    @Slot(str)
    def execute_code(self, code):
        """当在 Monaco 中按下 Ctrl+Enter 时，前端会调用此方法"""
        print("🚀 收到 Monaco 的执行请求，正在送入 Jupyter 沙盒...")
        
        if not jupyter_sandbox:
            self.execution_finished.emit({"status": "error", "traceback": ["Jupyter 沙盒未就绪"], "text": "", "images": []})
            return

        # 1. 扔进独立的 Jupyter 内核执行 (防卡死、防恶意代码)
        result = jupyter_sandbox.execute_code(code, timeout=10)
        
        # 2. 如果发生错误，解析错误行号并反馈给 Monaco 画红波浪线
        if result['status'] == 'error' or result['status'] == 'timeout':
            error_list = self._parse_traceback(result['traceback'])
            # 将错误信息转为 JSON 字符串发给前端 JS
            js_cmd = f"setEditorErrors('{json.dumps(error_list)}');"
            self.parent_widget.web_view.page().runJavaScript(js_cmd)
        else:
            # 执行成功，清除前端所有的红波浪线
            self.parent_widget.web_view.page().runJavaScript("setEditorErrors('[]');")
            
        # 3. 发射信号，让 UI 的其他模块（如终端控制台）去渲染文字和图片输出
        self.execution_finished.emit(result)

    def _parse_traceback(self, traceback_list):
        """从 IPython 的报错信息中提取错误行号和具体原因"""
        errors = []
        full_trace = "\n".join(traceback_list)
        
        # 简单的正则匹配：寻找类似 "line 5" 的报错信息
        match = re.search(r'line (\d+)', full_trace, re.IGNORECASE)
        if match:
            line_num = int(match.group(1))
            # 提取最后一行作为具体的错误原因，并过滤掉 ANSI 转义字符 (终端颜色代码)
            clean_error = re.sub(r'\x1b\[[0-9;]*m', '', traceback_list[-1])
            errors.append({
                "line": line_num, 
                "message": clean_error
            })
        else:
            # 找不到具体行号时，默认标红第一行
            errors.append({"line": 1, "message": "执行发生错误或超时"})
            
        return errors


class MathLabCodeEditor(QWidget):
    """供外部窗口调用的主编辑器控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. 初始化 Chromium 内核视图
        self.web_view = QWebEngineView()
        # 开启调试模式（可选，方便在开发时按 F12 调试 Monaco）
        self.web_view.settings().setAttribute(self.web_view.settings().WebAttribute.DeveloperExtrasEnabled, True)
        layout.addWidget(self.web_view)

        # 2. 设置 QWebChannel 双向通信通道
        self.channel = QWebChannel()
        self.backend = EditorBackend(self)
        self.channel.registerObject("backend", self.backend)
        self.web_view.page().setWebChannel(self.channel)

        # 3. 加载本地的 monaco.html
        html_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', 'resources', 'monaco.html'
        ))
        # 必须使用 QUrl.fromLocalFile 以赋予正确的本地文件读取权限
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))

    # ==========================================
    # 暴露给外部 Python 面板的主动控制接口
    # ==========================================

    def get_code(self, callback):
        """
        供 Python 主动获取编辑器内容的接口。
        注意：由于浏览器 JS 是异步的，这里必须传入一个 callback 回调函数来接收字符串。
        """
        self.web_view.page().runJavaScript("getEditorContent();", callback)

    def set_code(self, code_text):
        """供 Python 主动向编辑器写入代码的接口"""
        # 使用 json.dumps 将 Python 字符串安全转义，防止破坏 JS 语法
        escaped_code = json.dumps(code_text)
        self.web_view.page().runJavaScript(f"setEditorContent({escaped_code});")
