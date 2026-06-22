import math
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QApplication

class MagnetSnapper:
    """负责处理画布拖拽时的磁吸对齐逻辑"""
    
    def __init__(self, snap_threshold_pixels=10):
        # 屏幕物理像素阈值，无论怎么缩放，用户感觉吸附距离都是固定的 10px
        self.threshold_px = snap_threshold_pixels

    def snap(self, raw_logical_pos: QPointF, scale_factor: float, existing_points: list[QPointF], grid_size: float = 1.0) -> QPointF:
        """
        计算吸附后的安全坐标
        
        :param raw_logical_pos: 鼠标当前所在/图形将要移动到的逻辑坐标
        :param scale_factor: 当前视图缩放比 (View Transform.m11)
        :param existing_points: 场景中其他点的逻辑坐标列表
        :param grid_size: 网格单位 (默认 1.0)
        """
        # 1. 拦截器：全局检测是否按下了 Shift 键（临时静音吸附）
        modifiers = QApplication.keyboardModifiers()
        if modifiers and (modifiers & Qt.KeyboardModifier.ShiftModifier):
            return raw_logical_pos

        # 2. 动态计算当前的逻辑阈值 (物理阈值 / 缩放系数)
        logical_threshold = self.threshold_px / scale_factor if scale_factor > 0 else 0.001

        snapped_x = raw_logical_pos.x()
        snapped_y = raw_logical_pos.y()

        # === 优先级 1：吸附到其他点（点对点绝对锁定）===
        best_dist = float('inf')
        target_point = None
        for pt in existing_points:
            dist = math.hypot(snapped_x - pt.x(), snapped_y - pt.y())
            if dist < logical_threshold and dist < best_dist:
                best_dist = dist
                target_point = pt
                
        if target_point:
            # 吸附到了点，直接返回该点坐标，剥夺网格的干预权
            return QPointF(target_point.x(), target_point.y())

        # === 优先级 2 & 3：吸附到坐标轴与网格（正交独立判定）===
        
        # 处理 X 坐标 (控制元素在左右方向上的吸附：Y轴 或 竖直网格)
        if abs(snapped_x) < logical_threshold:
            snapped_x = 0.0  # 强吸附到 Y 轴
        else:
            nearest_grid_x = round(snapped_x / grid_size) * grid_size
            if abs(snapped_x - nearest_grid_x) < logical_threshold:
                snapped_x = nearest_grid_x

        # 处理 Y 坐标 (控制元素在上下方向上的吸附：X轴 或 水平网格)
        if abs(snapped_y) < logical_threshold:
            snapped_y = 0.0  # 强吸附到 X 轴
        else:
            nearest_grid_y = round(snapped_y / grid_size) * grid_size
            if abs(snapped_y - nearest_grid_y) < logical_threshold:
                snapped_y = nearest_grid_y

        return QPointF(snapped_x, snapped_y)
