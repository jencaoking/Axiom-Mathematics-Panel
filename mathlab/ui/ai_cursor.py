from PySide6.QtCore import Qt, QPointF, Property, QPropertyAnimation, QEasingCurve, Signal, QRectF, QTimer
from PySide6.QtWidgets import QGraphicsObject
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

class AICursorItem(QGraphicsObject):
    """
    AI 专属光标：一个带有科技感呼吸光晕的小圆点
    """
    # 定义属性改变的信号，供动画引擎底层调用
    cursorPosChanged = Signal()

    def __init__(self):
        super().__init__()
        # 让光标永远浮在最顶层，不被任何几何图形遮挡
        self.setZValue(99999)
        # 初始不可见，只有 AI 动作时才显现
        self.setVisible(False)
        self.setOpacity(0.9)
        
        # 核心动画控制器
        self.move_anim = QPropertyAnimation(self, b"cursorPos")
        self.move_anim.setEasingCurve(QEasingCurve.Type.InOutQuad) # 模拟人类手臂运动的缓动曲线

    def boundingRect(self):
        # 光标的光晕范围
        return QRectF(-15, -15, 30, 30)

    def paint(self, painter: QPainter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. 绘制外部淡蓝色光晕
        glow_color = QColor(0, 191, 255, 60)
        painter.setBrush(QBrush(glow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), 12, 12)
        
        # 2. 绘制内部高亮实心点
        core_color = QColor(0, 191, 255, 255)
        painter.setBrush(QBrush(core_color))
        painter.setPen(QPen(Qt.GlobalColor.white, 1.5))
        painter.drawEllipse(QPointF(0, 0), 4, 4)

    # --- 必须通过 Property 暴露坐标，动画引擎才能驱动它 ---
    def get_cursor_pos(self):
        return self.scenePos()

    def set_cursor_pos(self, pos):
        if self.parentItem():
            self.setPos(self.parentItem().mapFromScene(pos))
        else:
            self.setPos(pos)
        self.cursorPosChanged.emit()

    cursorPos = Property(QPointF, get_cursor_pos, set_cursor_pos, notify=cursorPosChanged)

    def move_to(self, target_pos: QPointF, duration_ms: int = 600):
        """控制光标飞向目标点"""
        self.setVisible(True)
        self.move_anim.stop()
        self.move_anim.setDuration(duration_ms)
        self.move_anim.setStartValue(self.scenePos())
        self.move_anim.setEndValue(target_pos)
        
        try:
            self.move_anim.finished.disconnect()
        except RuntimeError:
            pass
            
        self.move_anim.finished.connect(lambda: QTimer.singleShot(1000, self.hide))
        self.move_anim.start()
