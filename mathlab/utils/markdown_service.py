"""
混合架构 Markdown 渲染服务

双引擎策略：
- Python 引擎：python-markdown + matplotlib LaTeX→PNG，用于 QTextBrowser（离线、低延迟）
- JS 引擎：marked.js + KaTeX，用于 WebEngine（LaTeX 流式渲染）

智能路由：根据内容自动选择最佳引擎
"""

import re
import io
from enum import Enum
from functools import lru_cache
from typing import List, Tuple

import markdown as md_lib

from mathlab.utils.logger import get_logger

logger = get_logger(__name__)


class RenderEngine(Enum):
    """渲染引擎类型"""

    PYTHON = "python"  # python-markdown + matplotlib LaTeX
    WEBENGINE = "webengine"  # marked.js + KaTeX


class MarkdownService:
    """混合架构 Markdown 渲染服务（单例）

    使用方式::

        from mathlab.utils.markdown_service import MarkdownService

        # 获取单例
        svc = MarkdownService.get_instance()

        # QTextBrowser 场景（离线渲染，含 LaTeX→PNG）
        html = svc.render_for_text_browser(text, document=text_browser.document())

        # 纯 Markdown（不含 LaTeX）
        html = svc.render_pure_markdown(text)

        # 检测最佳引擎
        engine = svc.detect_best_engine(text)
    """

    _instance = None

    # LaTeX 定界符正则
    _LATEX_DISPLAY_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
    _LATEX_SQUARE_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
    _LATEX_INLINE_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL)
    _LATEX_BRACKET_RE = re.compile(r"\\\((.+?)\\\)", re.DOTALL)

    # 任意 LaTeX 定界符检测
    _HAS_LATEX_RE = re.compile(
        r"\$\$.+?\$\$" r"|(?<!\$)\$(?!\$).+?(?<!\$)\$(?!\$)" r"|\\\(.+?\\\)" r"|\\\[.+?\\\]",
        re.DOTALL,
    )

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 初始化 python-markdown
        self._md = md_lib.Markdown(
            extensions=[
                "extra",  # tables, fenced_code, footnotes, abbr, attr_list, def_list
                "codehilite",  # 语法高亮
                "nl2br",  # 换行转 <br>
                "sane_lists",  # 更好的列表处理
            ],
            extension_configs={
                "codehilite": {
                    "guess_lang": False,
                    "noclasses": True,
                },
            },
        )

        # 检查 matplotlib 可用性（用于 LaTeX→PNG）
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            self._plt = plt
            self._latex_render_available = True
        except ImportError:
            self._plt = None
            self._latex_render_available = False
            logger.warning("matplotlib 不可用，LaTeX 公式将以纯文本显示")

    @classmethod
    def get_instance(cls) -> "MarkdownService":
        """获取单例实例"""
        return cls()

    # ──────────────────────────────────────────────────────────────
    #  公共 API
    # ──────────────────────────────────────────────────────────────

    def has_latex(self, text: str) -> bool:
        """检测文本是否包含 LaTeX 公式"""
        return bool(self._HAS_LATEX_RE.search(text))

    def detect_best_engine(self, text: str) -> RenderEngine:
        """根据内容自动检测最佳渲染引擎

        规则：
        - 含 LaTeX 公式 → WebEngine（KaTeX 渲染效果最佳）
        - 纯 Markdown → Python（无 WebEngine 开销，延迟最低）
        """
        if self.has_latex(text):
            return RenderEngine.WEBENGINE
        return RenderEngine.PYTHON

    def render_for_text_browser(
        self,
        text: str,
        document=None,
        theme: str = "dark",
    ) -> str:
        """渲染为 QTextBrowser 可用的 HTML

        Args:
            text: Markdown 文本
            document: QTextDocument 实例（用于注册 LaTeX 图片资源）。
                      传入时 LaTeX 公式将渲染为 PNG 图片；
                      不传时 LaTeX 将以 serif 字体纯文本显示。
            theme: 主题，"dark" 或 "light"

        Returns:
            HTML 字符串
        """
        # 1. 提取并替换 LaTeX 公式为占位符
        placeholders, processed_text = self._extract_and_replace_latex(text)

        # 2. Markdown → HTML
        self._md.reset()
        html = self._md.convert(processed_text)

        # 3. 替换占位符为图片或样式化文本
        for placeholder, latex_src, display, latex_clean in placeholders:
            if document is not None and self._latex_render_available:
                img_tag = self._render_latex_to_img(document, latex_clean, display)
                html = html.replace(placeholder, img_tag)
            else:
                # 降级：以 serif 字体显示原始 LaTeX
                style = (
                    "font-family: serif; font-style: italic; display: block; " "text-align: center; margin: 8px 0;"
                    if display
                    else "font-family: serif; font-style: italic;"
                )
                html = html.replace(
                    placeholder,
                    f'<span style="{style}">{latex_src}</span>',
                )

        # 4. 包装主题 CSS
        if theme == "dark":
            return self._wrap_dark_theme(html)
        return self._wrap_light_theme(html)

    def render_pure_markdown(self, text: str, theme: str = "dark") -> str:
        """纯 Markdown 渲染（不含 LaTeX 处理）

        适用于无需数学公式的场景，如帮助文本、日志输出等。
        """
        self._md.reset()
        html = self._md.convert(text)
        if theme == "dark":
            return self._wrap_dark_theme(html)
        return self._wrap_light_theme(html)

    def render_for_webengine(self, text: str) -> str:
        """渲染为 WebEngine 可用的 HTML

        仅执行 Markdown→HTML 转换，LaTeX 公式保留原样，
        由前端 KaTeX 负责渲染。
        """
        self._md.reset()
        return self._md.convert(text)

    # ──────────────────────────────────────────────────────────────
    #  LaTeX 提取与替换
    # ──────────────────────────────────────────────────────────────

    def _extract_and_replace_latex(
        self,
        text: str,
    ) -> Tuple[List[Tuple[str, str, bool, str]], str]:
        """提取 LaTeX 公式并替换为 HTML 注释占位符

        Returns:
            (placeholders, processed_text)
            placeholders: [(placeholder, latex_src, is_display, latex_clean), ...]
        """
        placeholders = []
        counter = [0]

        def make_replacer(display: bool):
            def replacer(m):
                idx = counter[0]
                counter[0] += 1
                latex_src = m.group(0)
                placeholder = f"<!--LATEX_{idx}-->"

                # 清理 LaTeX 源码（去掉定界符）
                if latex_src.startswith("$$"):
                    latex_clean = latex_src[2:-2].strip()
                elif latex_src.startswith("\\("):
                    latex_clean = latex_src[2:-2].strip()
                elif latex_src.startswith("\\["):
                    latex_clean = latex_src[2:-2].strip()
                else:
                    latex_clean = latex_src.strip("$").strip()

                placeholders.append((placeholder, latex_src, display, latex_clean))
                return placeholder

            return replacer

        # 按优先级替换：$$ → \[\] → $ → \(\)
        # 顺序很重要，避免 $$ 被 $ 误匹配
        text = self._LATEX_DISPLAY_RE.sub(make_replacer(True), text)
        text = self._LATEX_SQUARE_RE.sub(make_replacer(True), text)
        text = self._LATEX_INLINE_RE.sub(make_replacer(False), text)
        text = self._LATEX_BRACKET_RE.sub(make_replacer(False), text)

        return placeholders, text

    # ──────────────────────────────────────────────────────────────
    #  LaTeX → PNG 渲染（带缓存）
    # ──────────────────────────────────────────────────────────────

    @lru_cache(maxsize=128)
    def _generate_latex_png(
        self,
        latex_str: str,
        color: str = "#d4d4d4",
        font_size: int = 12,
    ) -> bytes:
        """将 LaTeX 字符串渲染为 PNG 字节流（带 LRU 缓存）

        使用 matplotlib mathtext 渲染，无需系统 LaTeX 安装。
        """
        if not self._latex_render_available:
            return b""

        try:
            fig = self._plt.figure(figsize=(0.01, 0.01))
            fig.text(
                0,
                0,
                f"${latex_str}$",
                fontsize=font_size,
                color=color,
                ha="left",
                va="center",
            )

            buf = io.BytesIO()
            fig.savefig(
                buf,
                format="png",
                transparent=True,
                bbox_inches="tight",
                pad_inches=0.05,
                dpi=150,
            )
            self._plt.close(fig)
            return buf.getvalue()
        except Exception as e:
            logger.error(f"LaTeX PNG 渲染失败: {e}")
            return b""

    def _render_latex_to_img(
        self,
        document,
        latex_str: str,
        display: bool,
    ) -> str:
        """将 LaTeX 渲染为 PNG 并注册到 QTextDocument，返回 <img> 标签"""
        from PySide6.QtGui import QImage, QTextDocument
        from PySide6.QtCore import QUrl

        png_data = self._generate_latex_png(latex_str)
        if not png_data:
            return f'<span style="font-family: serif;">${latex_str}$</span>'

        img = QImage.fromData(png_data, "PNG")
        if img.isNull():
            return f'<span style="font-family: serif;">${latex_str}$</span>'

        # 使用 LaTeX 内容的 hash 作为资源 URL
        resource_url = f"latex://{abs(hash(latex_str))}"
        url = QUrl(resource_url)

        # 注册图片资源到文档（重复注册会覆盖，幂等操作）
        document.addResource(QTextDocument.ImageResource, url, img)

        if display:
            return f'<div style="text-align: center; margin: 8px 0;">' f'<img src="{resource_url}" /></div>'
        return f'<img src="{resource_url}" style="vertical-align: middle;" />'

    # ──────────────────────────────────────────────────────────────
    #  主题 CSS
    # ──────────────────────────────────────────────────────────────

    def _wrap_dark_theme(self, html: str) -> str:
        """暗黑主题 CSS（匹配 VSCode 风格）"""
        css = (
            "<style>"
            'body { color: #d4d4d4; font-family: -apple-system, "Segoe UI", '
            '"Microsoft YaHei", sans-serif; font-size: 14px; line-height: 1.6; }'
            "code { font-family: Consolas, monospace; color: #ce9178; "
            "background-color: #2d2d2d; padding: 2px 4px; border-radius: 3px; }"
            "pre { background-color: #1e1e1e; padding: 10px; border-radius: 5px; "
            "overflow-x: auto; }"
            "pre code { background-color: transparent; padding: 0; color: #d4d4d4; }"
            "blockquote { border-left: 4px solid #007acc; margin: 0; "
            "padding-left: 15px; color: #858585; }"
            "table { border-collapse: collapse; width: 100%; margin-bottom: 1em; }"
            "th, td { border: 1px solid #444; padding: 8px; text-align: left; }"
            "th { background-color: #2d2d2d; }"
            "a { color: #4EC9B0; }"
            "h1, h2, h3, h4, h5, h6 { color: #569cd6; }"
            ".codehilite { background-color: #1e1e1e; padding: 10px; "
            "border-radius: 5px; overflow-x: auto; }"
            "</style>"
        )
        return css + html

    def _wrap_light_theme(self, html: str) -> str:
        """浅色主题 CSS"""
        css = (
            "<style>"
            'body { color: #333; font-family: -apple-system, "Segoe UI", '
            '"Microsoft YaHei", sans-serif; font-size: 14px; line-height: 1.6; }'
            "code { font-family: Consolas, monospace; color: #c7254e; "
            "background-color: #f9f2f4; padding: 2px 4px; border-radius: 3px; }"
            "pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; "
            "overflow-x: auto; }"
            "pre code { background-color: transparent; padding: 0; color: #333; }"
            "blockquote { border-left: 4px solid #007acc; margin: 0; "
            "padding-left: 15px; color: #666; }"
            "table { border-collapse: collapse; width: 100%; margin-bottom: 1em; }"
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }"
            "th { background-color: #f0f0f0; }"
            "a { color: #007acc; }"
            "</style>"
        )
        return css + html
