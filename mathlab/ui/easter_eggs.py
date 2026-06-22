import math
import re
from PySide6.QtCore import Qt, QTimer, QRectF, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget

class RainbowOverlay(QWidget):
    """
    全局透明的彩虹动画遮罩层
    触发欧拉公式时，在窗口上方全屏显示彩虹特效
    """
    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        
        # 避免重复生成
        for child in parent_widget.children():
            if isinstance(child, RainbowOverlay) and child is not self:
                self.deleteLater()
                return

        # 核心设置：让窗口透明且不拦截任何鼠标事件（完全穿透）
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 覆盖整个父窗口
        self.resize(parent_widget.size())
        self.show()

        # 动画状态机
        self.progress = 0.0  # 0.0 到 1.0
        self.fade_out = 1.0
        
        # 彩虹的七种颜色
        self.colors = [
            QColor(255, 0, 0),    # 红
            QColor(255, 127, 0),  # 橙
            QColor(255, 255, 0),  # 黄
            QColor(0, 255, 0),    # 绿
            QColor(0, 0, 255),    # 蓝
            QColor(75, 0, 130),   # 靛
            QColor(148, 0, 211)   # 紫
        ]

        # 核心替换：使用 QVariantAnimation 实现基于系统时钟的丝滑动画
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(1500) # 1.5 秒动画周期
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.2)
        # 丝滑曲线：带有一点冲击感后极度平滑的减速展开
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._on_anim_step)
        self.anim.finished.connect(self.deleteLater)
        self.anim.start()

    def _on_anim_step(self, value: float):
        self.progress = value
        
        # 进度超过 0.7 时开始淡出计算：映射进度 [0.7, 1.2] 到透明度 [1.0, 0.0]
        if self.progress > 0.7:
            self.fade_out = max(0.0, 1.0 - (self.progress - 0.7) / 0.5)
            
        self.update() # 触发重绘

    def paintEvent(self, event):
        if self.fade_out <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 设置整体透明度（实现淡出）
        painter.setOpacity(max(0.0, min(1.0, self.fade_out)))

        center = self.rect().center()
        base_radius = min(self.width(), self.height()) * 0.3
        thickness = base_radius * 0.15

        # 限制圆弧的最大绘制角度 (进度 0.0->0.5 时展开至 180 度)
        draw_ratio = min(1.0, self.progress * 2.0)
        span_angle = int(180 * 16 * draw_ratio) # Qt 的 drawArc 需要角度乘 16

        for i, color in enumerate(self.colors):
            # 从外向内依次绘制圆弧
            radius = base_radius - (i * thickness)
            
            pen = QPen(color)
            pen.setWidthF(thickness + 1.0) # 加1.0防止圆弧之间出现白线间隙
            pen.setCapStyle(Qt.PenCapStyle.RoundCap) # 圆润的边缘
            painter.setPen(pen)

            rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
            # 起始角度从 0 (三点钟方向) 开始，可以调整为 0 以形成彩虹拱门
            painter.drawArc(rect, 0 * 16, span_angle)
            
        painter.end()


class EasterEggDetector:
    """负责检测数学输入并触发对应的彩蛋特效"""
    
    def __init__(self, main_window):
        # 必须传入主窗口作为参数，因为特效遮罩需要挂载在最顶层
        self.main_window = main_window

    def _normalize_math_string(self, text: str) -> str:
        """极简归一化：去空格、去反斜杠、全小写，剥离大括号"""
        t = text.lower().replace(" ", "").replace("\\", "").replace("{", "").replace("}", "")
        return t

    def check_and_trigger(self, raw_input: str):
        normalized = self._normalize_math_string(raw_input)
        
        # 1. 欧拉公式彩蛋 $e^{i\pi} + 1 = 0$
        # 兼容输入：e^(i\pi)+1=0, e^i\pi+1=0, e**(ipi)+1=0
        if "e^ipi+1=0" in normalized or "e**(ipi)+1=0" in normalized or "e^i*pi+1=0" in normalized:
            RainbowOverlay(self.main_window)
            return True
            
        # 2. 情人节彩蛋：心形线方程 $(x^2+y^2-1)^3 - x^2y^3 = 0$
        if "x^2+y^2-1^3" in normalized and "x^2y^3=0" in normalized:
            # 留作拓展：调用 HeartPulseOverlay(self.main_window)
            pass
            
        # 3. 宇宙终极答案彩蛋
        if normalized == "42":
            # 留作拓展：调用 TextFlashOverlay("Don't Panic", self.main_window)
            pass

        return False
