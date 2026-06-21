from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect

def get_opacity_effect(widget: QWidget) -> QGraphicsOpacityEffect:
    """获取或为 widget 创建 QGraphicsOpacityEffect。"""
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    return effect

def fade_in(widget: QWidget, duration: int = 200, callback = None):
    """在指定时间内淡入 widget。"""
    try:
        effect = get_opacity_effect(widget)
        effect.setOpacity(0.0)
        
        animation = QPropertyAnimation(effect, b"opacity", widget)
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 保持动画对象的引用以防止被垃圾回收
        if not hasattr(widget, '_fade_in_anim'):
            widget._fade_in_anim = None
        widget._fade_in_anim = animation
        
        if callback:
            animation.finished.connect(callback)
            
        animation.start()
    except Exception as e:
        print(f"Warning: Fade in animation failed: {e}")
        # Fallback: 直接显示并执行回调
        if callback:
            callback()

def fade_out(widget: QWidget, duration: int = 200, callback = None):
    """在指定时间内淡出 widget。"""
    try:
        effect = get_opacity_effect(widget)
        
        animation = QPropertyAnimation(effect, b"opacity", widget)
        animation.setDuration(duration)
        animation.setStartValue(effect.opacity())
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        if not hasattr(widget, '_fade_out_anim'):
            widget._fade_out_anim = None
        widget._fade_out_anim = animation
        
        def on_finished():
            # 还原为可见状态，供下次显示
            effect.setOpacity(1.0)
            if callback:
                callback()
                
        animation.finished.connect(on_finished)
        animation.start()
    except Exception as e:
        print(f"Warning: Fade out animation failed: {e}")
        # Fallback: 直接执行回调
        if callback:
            callback()
