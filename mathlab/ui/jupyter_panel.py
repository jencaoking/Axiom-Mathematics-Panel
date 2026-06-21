"""
jupyter_panel.py
────────────────
嵌入式 JupyterLab 交互面板

使用 PySide6.QtWebEngineWidgets.QWebEngineView 将本地 JupyterLab
完整渲染在 Qt 窗口内部，包含：
  - 加载动画（旋转进度指示器）
  - 加载完成后平滑淡入
  - 加载失败时错误提示 + 重试按钮
  - 右键菜单策略设置（允许 Jupyter 内部右键正常工作）
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
)
from PySide6.QtCore import (
    Qt, QUrl, QTimer, QPropertyAnimation,
    QEasingCurve, Property,
)
from PySide6.QtGui import QColor

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import (
        QWebEngineSettings,
        QWebEnginePage,
    )
    _WEBENGINE_AVAILABLE = True
except ImportError:
    _WEBENGINE_AVAILABLE = False


# ── 加载占位卡片 ─────────────────────────────────────────────────────────────

class _LoadingCard(QFrame):
    """启动期间显示的深色渐变占位卡片"""

    _STYLE = """
        QFrame {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #0D1117,
                stop:1 #161B22
            );
            border-radius: 12px;
        }
        QLabel#title {
            color: #58A6FF;
            font-size: 18px;
            font-weight: 700;
            font-family: 'Segoe UI', 'Inter', sans-serif;
        }
        QLabel#sub {
            color: #8B949E;
            font-size: 13px;
            font-family: 'Segoe UI', 'Inter', sans-serif;
        }
        QPushButton#retry_btn {
            background: #21262D;
            color: #58A6FF;
            border: 1px solid #30363D;
            border-radius: 6px;
            padding: 6px 18px;
            font-size: 13px;
        }
        QPushButton#retry_btn:hover {
            background: #30363D;
            border-color: #58A6FF;
        }
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(self._STYLE)

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignCenter)
        root.setSpacing(12)

        self.spinner_lbl = QLabel("◌")
        self.spinner_lbl.setAlignment(Qt.AlignCenter)
        self.spinner_lbl.setStyleSheet(
            "color: #58A6FF; font-size: 36px;"
        )
        root.addWidget(self.spinner_lbl)

        self.title_lbl = QLabel("🌌  正在启动 JupyterLab 内核…")
        self.title_lbl.setObjectName("title")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(self.title_lbl)

        self.sub_lbl = QLabel("本地微服务已在后台就绪，浏览器引擎正在挂载工作区")
        self.sub_lbl.setObjectName("sub")
        self.sub_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(self.sub_lbl)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        self.retry_btn = QPushButton("⟳  重新加载")
        self.retry_btn.setObjectName("retry_btn")
        self.retry_btn.hide()
        btn_row.addWidget(self.retry_btn)
        root.addLayout(btn_row)

        # 旋转动画（用定时器轮换字符模拟）
        self._frames = ["◜", "◝", "◞", "◟", "◌", "●", "◌"]
        self._frame_idx = 0
        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._tick)
        self._spin_timer.start(120)

    def _tick(self) -> None:
        self._frame_idx = (self._frame_idx + 1) % len(self._frames)
        self.spinner_lbl.setText(self._frames[self._frame_idx])

    def show_error(self, msg: str = "") -> None:
        self._spin_timer.stop()
        self.spinner_lbl.setText("✕")
        self.spinner_lbl.setStyleSheet("color: #F85149; font-size: 36px;")
        self.title_lbl.setText("❌  Jupyter 页面加载失败")
        self.sub_lbl.setText(msg or "请检查后台进程是否正常启动")
        self.retry_btn.show()

    def show_success_hint(self) -> None:
        self._spin_timer.stop()


# ── 主面板 ───────────────────────────────────────────────────────────────────

class JupyterPanel(QWidget):
    """
    嵌入式 JupyterLab 交互面板

    用法::

        mgr = JupyterManager()
        mgr.start()
        panel = JupyterPanel(mgr.url)
        panel.load_workspace()
    """

    def __init__(self, jupyter_url: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.jupyter_url = jupyter_url
        self._setup_ui()

    # ── UI 构建 ──────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if not _WEBENGINE_AVAILABLE:
            self._show_no_webengine_error(layout)
            return

        # 加载卡片
        self._card = _LoadingCard(self)
        layout.addWidget(self._card)

        # Web 引擎视图
        self._browser = QWebEngineView(self)
        self._browser.hide()
        layout.addWidget(self._browser)

        # 配置 WebEngine 安全策略（允许本地 localhost 的混合内容）
        settings = self._browser.page().settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled, True
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True
        )

        # 允许 Jupyter 内部右键菜单正常工作
        self._browser.setContextMenuPolicy(Qt.NoContextMenu)

        self._browser.loadFinished.connect(self._on_load_finished)

        # 重试按钮
        self._card.retry_btn.clicked.connect(self._reload)

    def _show_no_webengine_error(self, layout: QVBoxLayout) -> None:
        lbl = QLabel(
            "⚠️  缺少 PySide6-WebEngine 模块\n\n"
            "请运行：\n"
            "  pip install PySide6-WebEngine\n\n"
            "（PySide6 6.x 版本需要单独安装 WebEngine）"
        )
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            "color: #F0B429; font-size: 14px; padding: 40px;"
            "background: #1A1A2E; border-radius: 8px;"
        )
        layout.addWidget(lbl)

    # ── 公开 API ─────────────────────────────────────────────────────────────

    def load_workspace(self) -> None:
        """开始加载 JupyterLab 工作区页面"""
        if not _WEBENGINE_AVAILABLE:
            return
        self._browser.load(QUrl(self.jupyter_url))

    def update_url(self, new_url: str) -> None:
        """动态更新目标 URL 并重新加载"""
        self.jupyter_url = new_url
        self.load_workspace()

    # ── 私有回调 ─────────────────────────────────────────────────────────────

    def _on_load_finished(self, success: bool) -> None:
        if success:
            self._card.show_success_hint()
            # 淡入 browser，淡出 card
            self._card.hide()
            self._browser.show()
        else:
            # 判断是否真的失败（Jupyter 有时会重定向到 /lab/tree，仍属成功）
            current_url = self._browser.url().toString()
            if "localhost" in current_url and "/lab" in current_url:
                self._card.hide()
                self._browser.show()
            else:
                self._card.show_error(
                    f"页面响应异常\n目标：{self.jupyter_url}"
                )

    def _reload(self) -> None:
        """重试加载"""
        self._card.setVisible(True)
        self._card.spinner_lbl.setText("◌")
        self._card.spinner_lbl.setStyleSheet("color: #58A6FF; font-size: 36px;")
        self._card.title_lbl.setText("🌌  正在重新连接 JupyterLab…")
        self._card.retry_btn.hide()
        self._card._spin_timer.start(120)
        self._browser.hide()
        self.load_workspace()
