import math
from PySide6.QtCore import Qt, QPointF, QLineF
from PySide6.QtGui import QPen, QColor, QFont
from PySide6.QtWidgets import (
    QGraphicsLineItem,
    QGraphicsTextItem,
    QGraphicsScene,
    QApplication,
)


class SmartGuideManager:
    """
    负责在拖拽时渲染临时的智能辅助线（水平/垂直对齐、距离、角度）
    """

    def __init__(self, scene: QGraphicsScene):
        self.scene = scene
        self.guide_lines = []
        self.guide_texts = []

        # 样式定义：科技感的浅蓝色虚线
        self.line_pen = QPen(QColor(0, 168, 255, 180), 1.5, Qt.PenStyle.DashLine)
        self.font = QFont("Consolas", 9)  # 推荐使用等宽字体显示数字

    def clear(self):
        """清除场景中的所有临时辅助线和文字（鼠标释放时调用）"""
        for item in self.guide_lines + self.guide_texts:
            if item.scene() == self.scene:
                self.scene.removeItem(item)
        self.guide_lines.clear()
        self.guide_texts.clear()

    def draw_guides(
        self,
        current_pos: QPointF,
        other_points: list[QPointF],
        logical_threshold: float = 0.5,
    ):
        """
        判断是否对齐，并在需要时绘制辅助线与数据
        """
        # 每次重绘前先清空旧的辅助线
        self.clear()

        # 1. 拦截器：全局检测是否按下了 Shift 键（临时静音辅助线）
        modifiers = QApplication.keyboardModifiers()
        if modifiers and (modifiers & Qt.KeyboardModifier.ShiftModifier):
            return

        aligned_points = []

        for pt in other_points:
            dx = current_pos.x() - pt.x()
            dy = current_pos.y() - pt.y()

            # 判断是否触发水平 (Y轴相近) 或 垂直 (X轴相近) 对齐
            is_aligned_v = abs(dx) < logical_threshold
            is_aligned_h = abs(dy) < logical_threshold

            if is_aligned_v or is_aligned_h:
                dist = math.hypot(dx, dy)
                aligned_points.append((dist, pt, dx, dy))

        # 多点干扰过滤：只向距离最近的前 2 个触发对齐的点绘制辅助线
        aligned_points.sort(key=lambda x: x[0])
        aligned_points = aligned_points[:2]

        for dist, pt, dx, dy in aligned_points:
            # --- 1. 绘制虚线 ---
            line_item = QGraphicsLineItem(QLineF(current_pos, pt))
            line_item.setPen(self.line_pen)
            # ZValue 设为极高，保证辅助线永远浮在所有几何图形上方
            line_item.setZValue(9999)

            # 禁用辅助线的鼠标命中测试，防止阻挡用户点击画布
            line_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

            self.scene.addItem(line_item)
            self.guide_lines.append(line_item)

            # --- 2. 计算几何数据 ---
            # 计算极角并转换为角度，Qt 的 Y 轴向下，所以加负号修正为标准数学坐标系直觉
            angle = math.degrees(math.atan2(-dy, dx))
            if angle < 0:
                angle += 360

            # --- 3. 绘制文字标签 ---
            text_str = f"d: {dist:.2f}\nθ: {angle:.1f}°"
            text_item = QGraphicsTextItem(text_str)
            text_item.setFont(self.font)
            text_item.setDefaultTextColor(QColor(100, 100, 100, 220))
            text_item.setZValue(10000)

            # 计算两点中点作为文字锚点，并做轻微像素偏移防止文字被线穿过
            mid_x = (current_pos.x() + pt.x()) / 2
            mid_y = (current_pos.y() + pt.y()) / 2
            text_item.setPos(mid_x + 8, mid_y + 8)

            self.scene.addItem(text_item)
            self.guide_texts.append(text_item)
