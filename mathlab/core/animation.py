from PySide6.QtCore import QEasingCurve, QObject, QVariantAnimation
from PySide6.QtWidgets import QGraphicsItem


class AnimationManager:
    """全局动画管理器（可选用于串联排队动画，目前MVP版本先独立运行）"""

    pass


class CreateAnimation(QObject):
    """
    高仿 Manim 的 Create() 动画
    通过控制图形的绘制百分比 (0.0 到 1.0) 来实现生长的视觉效果
    """

    def __init__(self, item: QGraphicsItem, duration: int = 800):
        super().__init__()
        self.item = item

        # 核心：Qt 数值插值动画
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(duration)  # 毫秒
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)

        # 注入灵魂：缓动曲线！InOutQuad 会让动画有“缓慢加速，再缓慢减速”的极度舒适感
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # 每次数值变化时，调用我们的渲染回调
        self.anim.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, val: float):
        """将 0~1 的进度传递给具体的 UI 图元"""
        if hasattr(self.item, "set_draw_progress"):
            self.item.set_draw_progress(val)

    def play(self):
        """播放动画"""
        # 播放前确保图形初始化为不可见状态 (0%)
        if hasattr(self.item, "set_draw_progress"):
            self.item.set_draw_progress(0.0)

        # 绑定引用防止 GC 提前回收，并在结束时清理
        self.item._create_anim_ref = self
        self.anim.finished.connect(lambda: setattr(self.item, "_create_anim_ref", None))

        self.anim.start()
