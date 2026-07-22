from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QGraphicsDropShadowEffect,
    QFrame,
    QApplication,
)
from PySide6.QtGui import QColor, QFont, QKeyEvent


class OmniBar(QWidget):
    search_submitted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # ✨ 魔法标志：脱离主窗体、无边框、永远置顶、背景透明
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setup_ui()
        self.setup_animations()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # 为阴影留出空间

        # 核心载体：带圆角和毛玻璃质感的 Frame
        self.panel = QFrame(self)
        self.panel.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 12px;
            }
        """)

        # 增加高级的 Mac 风格物理阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.panel.setGraphicsEffect(shadow)

        # 面板内部布局
        panel_layout = QHBoxLayout(self.panel)
        panel_layout.setContentsMargins(15, 10, 15, 10)

        # 1. 当前 Agent 身份指示器
        self.agent_icon = QLabel("🟢")
        self.agent_icon.setStyleSheet("font-size: 20px; background: transparent; border: none;")

        # 2. 无边框的主输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("唤醒 AI，或输入 / 执行命令 (如 /clear)...")
        font = QFont("PingFang SC", 14)  # 稍微大一点的字体，提升输入沉浸感
        self.input_field.setFont(font)
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: #333;
            }
        """)
        # 回车发送信号
        self.input_field.returnPressed.connect(self.on_submit)

        # 3. 极其克制的状态微标 (Token / 状态)
        self.status_label = QLabel("💤")
        self.status_label.setStyleSheet("font-size: 14px; background: transparent; border: none; color: #888;")

        panel_layout.addWidget(self.agent_icon)
        panel_layout.addWidget(self.input_field)
        panel_layout.addWidget(self.status_label)

        main_layout.addWidget(self.panel)

        # 默认隐藏
        self.setWindowOpacity(0.0)
        self.hide()

    def setup_animations(self):
        # 透明度渐变动画
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(150)  # 150ms 极速响应
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutSine)

    def summon(self, parent_rect: QRect):
        """召唤命令盘：居中浮现"""
        # 计算完美居中的位置 (相对于父窗口，通常在靠上的黄金分割点)
        width = 600
        height = 80
        x = parent_rect.x() + (parent_rect.width() - width) // 2
        y = parent_rect.y() + parent_rect.height() // 4

        self.setGeometry(x, y, width, height)
        self.show()

        # 执行淡入动画
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

        # 强制抢占焦点，光标直接进入输入框
        self.activateWindow()
        self.input_field.setFocus()

    def dismiss(self):
        """驱散命令盘：优雅淡出"""
        self.fade_anim.setStartValue(self.windowOpacity())
        self.fade_anim.setEndValue(0.0)

        # 动画结束后真正隐藏，节约系统资源
        self.fade_anim.finished.connect(self._on_fade_out_finished)
        self.fade_anim.start()

    def _on_fade_out_finished(self):
        try:
            # [BUG修复] 增加 try-except 保护，防止重复 disconnect 导致 RuntimeError
            self.fade_anim.finished.disconnect(self._on_fade_out_finished)
        except RuntimeError:
            pass
        self.hide()
        self.input_field.clear()

    # --- 核心交互 UX ---
    def focusOutEvent(self, event):
        """当用户点击了画板的其他地方，Omni-Bar 自动识趣地消失"""
        self.dismiss()
        super().focusOutEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """按下 Esc 键立即消失"""
        if event.key() == Qt.Key.Key_Escape:
            self.dismiss()
        super().keyPressEvent(event)

    def on_submit(self):
        # [BUG修复] 去抖动：防止快速连按回车导致重复发送
        if getattr(self, "_is_submitting", False):
            return
        self._is_submitting = True

        try:
            text = self.input_field.text().strip()
            if not text:
                return

            self.search_submitted.emit(text)

            # [BUG修复] 安全的属性访问，防御父窗体已被销毁或属性不存在的情况
            parent_win = self.parent()
            if parent_win and hasattr(parent_win, "ai_tools_panel") and parent_win.ai_tools_panel:
                parent_win.ai_tools_panel.chat_input.setText(text)
                parent_win.ai_tools_panel.on_send_message()

            # 发送完后自动功成身退
            self.dismiss()
        finally:
            self._is_submitting = False
