from PySide6.QtCore import (
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    QSequentialAnimationGroup,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget


class AnimationManager:
    """
    生命周期安全的动画管理器。
    确保同一个控件只能同时存在一个动效实例，并在任务结束时彻底释放资源，防止 C++ 内存泄漏。
    """

    @classmethod
    def register(cls, widget: QWidget, animation: QObject):
        # 注册前先停掉并销毁旧的动画
        cls.stop(widget)

        # 强绑定父对象，当控件被销毁时，C++ 层的动画也会被自动回收
        animation.setParent(widget)
        widget._current_animation = animation

        def on_finished():
            # 动画正常结束时的清理
            if getattr(widget, "_current_animation", None) == animation:
                widget._current_animation = None
                animation.deleteLater()

        animation.finished.connect(on_finished)

    @classmethod
    def stop(cls, widget: QWidget):
        anim = getattr(widget, "_current_animation", None)
        if anim:
            anim.stop()
            anim.deleteLater()
            widget._current_animation = None


def stop_animation(widget: QWidget):
    """停止并释放控件上的所有动画，重置透明度（主要用于显式终止呼吸灯）。"""
    AnimationManager.stop(widget)
    effect = widget.graphicsEffect()
    if isinstance(effect, QGraphicsOpacityEffect):
        effect.setOpacity(1.0)


def get_opacity_effect(widget: QWidget) -> QGraphicsOpacityEffect:
    """获取或为 widget 创建 QGraphicsOpacityEffect。"""
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    return effect


def fade_in(widget: QWidget, duration: int = 200, callback=None):
    """在指定时间内淡入 widget。"""
    try:
        effect = get_opacity_effect(widget)
        effect.setOpacity(0.0)

        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        if callback:
            animation.finished.connect(callback)

        AnimationManager.register(widget, animation)
        animation.start()
    except Exception as e:
        print(f"Warning: Fade in animation failed: {e}")
        # Fallback: 直接显示并执行回调
        if callback:
            callback()


def fade_out(widget: QWidget, duration: int = 200, callback=None):
    """在指定时间内淡出 widget。"""
    try:
        effect = get_opacity_effect(widget)

        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(effect.opacity())
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        def on_finished():
            # 还原为可见状态，供下次显示
            effect.setOpacity(1.0)
            if callback:
                callback()

        animation.finished.connect(on_finished)

        AnimationManager.register(widget, animation)
        animation.start()
    except Exception as e:
        print(f"Warning: Fade out animation failed: {e}")
        # Fallback: 直接执行回调
        if callback:
            callback()


def start_breathing_effect(widget, property_name=b"opacity", duration=800):
    """
    为控件添加连续的“呼吸”微动效（如正在计算中的 AI 图标或按钮）
    """
    effect = get_opacity_effect(widget)

    # 渐暗
    anim_out = QPropertyAnimation(effect, property_name)
    anim_out.setDuration(duration)
    anim_out.setStartValue(1.0)
    anim_out.setEndValue(0.4)
    anim_out.setEasingCurve(QEasingCurve.InOutSine)

    # 渐亮
    anim_in = QPropertyAnimation(effect, property_name)
    anim_in.setDuration(duration)
    anim_in.setStartValue(0.4)
    anim_in.setEndValue(1.0)
    anim_in.setEasingCurve(QEasingCurve.InOutSine)

    # 组合为无限循环
    group = QSequentialAnimationGroup()
    group.addAnimation(anim_out)
    group.addAnimation(anim_in)
    group.setLoopCount(-1)  # 无限循环

    AnimationManager.register(widget, group)
    group.start()

    return group  # 返回组对象，以便外部调用（不过推荐以后改用 stop_animation）
