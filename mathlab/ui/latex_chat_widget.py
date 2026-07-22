import json
import os

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView


class LatexChatWidget(QWebEngineView):
    """
    基于 WebEngine 的工业级 Markdown + LaTeX 渲染器
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 加载刚才写好的 HTML 引擎
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources", "chat_renderer.html"))
        self.setUrl(QUrl.fromLocalFile(html_path))

        # 维护一份纯净的聊天记录结构，用于整体重绘防撕裂
        self.chat_history = []
        self._current_streaming_content = ""

    def add_message(self, role: str, content: str):
        """添加一条完整的历史消息"""
        self.chat_history.append({"role": role, "content": content})
        self._current_streaming_content = ""
        self._render_to_webview()

    def update_streaming_chunk(self, chunk: str):
        """
        处理流式大模型的碎片
        【架构黑魔法】：由于网络碎片可能把 $$ 切成两半，导致渲染崩溃。
        我们的策略是：在 Python 端拼装完整 Markdown，然后让前端整体进行重绘。
        得益于 KaTeX 的极速性能，这种“整体重绘”在肉眼看来就是极其平滑的打字机效果。
        """
        self._current_streaming_content += chunk
        self._render_to_webview()

    def finalize_streaming_message(self):
        """流式输出结束，将当前内容固化到历史记录中"""
        if self._current_streaming_content:
            self.add_message("ai", self._current_streaming_content)

    def clear_chat(self):
        self.chat_history.clear()
        self._current_streaming_content = ""
        self._render_to_webview()

    def _render_to_webview(self):
        """将内部历史记录转换为 HTML 并推送到 JS 引擎"""
        html_parts = []

        # 1. 渲染历史固化消息
        for msg in self.chat_history:
            if msg["role"] == "user":
                html_parts.append(
                    f"<div class='message-container role-user'>你：<br>{self._escape_html(msg['content'])}</div>"
                )
            else:
                # 注意：这里我们借助 JS 端的 marked 库，所以 Python 端只需包一层外壳即可
                # 真正的 Markdown -> HTML 转换在 JS 端完成
                safe_content = json.dumps(msg["content"])
                html_parts.append(
                    f"<div class='message-container role-ai'>🤖 AI 助教：<br><span class='md-content' data-raw={safe_content}></span></div>"
                )

        # 2. 渲染当前正在打字的流式消息
        if self._current_streaming_content:
            safe_stream = json.dumps(self._current_streaming_content)
            html_parts.append(
                f"<div class='message-container role-ai'>🤖 AI 助教：<br><span class='md-content' data-raw={safe_stream}></span><span style='animation: blink 1s infinite;'> ▋</span></div>"
            )

        # 组合最终的 HTML 结构（附加一段简易的 JS 将 data-raw 解析为 markdown）
        full_html = "".join(html_parts)

        # 组装注入脚本，让前端解析刚才塞入的 data-raw 属性
        # [BUG修复] 转义反引号和 ${} 防止 JS 注入
        safe_html = full_html.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        js_code = f"""
        (function() {{
            let rawHtml = `{safe_html}`;
            // 创建临时容器
            let tempDiv = document.createElement('div');
            tempDiv.innerHTML = rawHtml;
            
            // 将所有带有 data-raw 的 span 替换为 marked.js 解析后的纯净 HTML
            let mdSpans = tempDiv.querySelectorAll('.md-content');
            mdSpans.forEach(span => {{
                let rawText = JSON.parse(span.getAttribute('data-raw'));
                span.innerHTML = marked.parse(rawText);
            }});
            
            // 调用核心引擎刷新界面并渲染 LaTeX
            window.updateChat(tempDiv.innerHTML);
        }})();
        """

        self.page().runJavaScript(js_code)

    def _escape_html(self, text: str) -> str:
        """简单的用户输入转义，防止 XSS"""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
