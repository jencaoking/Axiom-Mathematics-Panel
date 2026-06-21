from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem,
    QGraphicsTextItem, QMenu, QGraphicsSceneMouseEvent
)
from PySide6.QtGui import QPolygonF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QCursor, QPainter, QPainterPath
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QTimer, QLineF
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtSvg import QSvgRenderer

# 导入 LaTeX 渲染缓存
try:
    from mathlab.utils.latex_renderer import (
        SharedSvgRendererCache, is_latex_rendering_available
    )
except ImportError:
    SharedSvgRendererCache = None
    is_latex_rendering_available = lambda: False


class MathGraphicsItem(QGraphicsSvgItem):
    """
    支持 LaTeX 公式渲染的图形项
    
    采用混合渲染策略：
    - 静态时：使用 SVG 渲染高质量的 LaTeX 公式
    - 拖拽时：降级为普通文本，保证 60 FPS 流畅度
    
    特性：
    - LRU 缓存：相同公式只渲染一次
    - 共享渲染器：多个实例共享同一个 QSvgRenderer
    - 设备坐标缓存：防止拖动时重新光栅化
    """
    
    def __init__(self, text: str, parent=None, use_latex: bool = True):
        """
        Args:
            text: 显示文本，可以是普通文本或 LaTeX 公式
            parent: 父图形项
            use_latex: 是否启用 LaTeX 渲染（默认启用）
        """
        super().__init__(parent)
        self._text = text
        self._use_latex = use_latex and is_latex_rendering_available()
        self._fallback_item = None  # 降级渲染的文本项
        self._is_dragging = False
        
        # 开启图形缓存，防止拖动画布时重新光栅化
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        
        self._update_rendering()
    
    def _update_rendering(self):
        """更新渲染内容"""
        if self._use_latex and not self._is_dragging:
            # 尝试使用 LaTeX SVG 渲染
            renderer = SharedSvgRendererCache.get_renderer(self._text)
            if renderer is not None:
                self.setSharedRenderer(renderer)
                self.setVisible(True)
                # 隐藏降级文本
                if self._fallback_item:
                    self._fallback_item.setVisible(False)
                return
        
        # 降级：使用普通文本渲染
        self._create_fallback_text()
    
    def _create_fallback_text(self):
        """创建降级文本项"""
        if self._fallback_item is None:
            self._fallback_item = QGraphicsTextItem(self)
            self._fallback_item.setFont(QFont('Arial', 12, QFont.Bold))
            self._fallback_item.setDefaultTextColor(QColor('#0b1c30'))
        
        self._fallback_item.setPlainText(self._text)
        self._fallback_item.setVisible(True)
        # 隐藏 SVG 项
        self.setVisible(False)
    
    def set_text(self, new_text: str):
        """更新显示文本"""
        if self._text != new_text:
            self._text = new_text
            self._update_rendering()
    
    def set_dragging(self, is_dragging: bool):
        """
        设置拖拽状态
        
        拖拽时降级为普通文本以保证帧率，
        松开后恢复 LaTeX 渲染。
        """
        if self._is_dragging != is_dragging:
            self._is_dragging = is_dragging
            if is_dragging:
                # 拖拽中：立即切换到降级渲染
                self._create_fallback_text()
            else:
                # 拖拽结束：恢复 LaTeX 渲染
                self._update_rendering()
    
    def text(self) -> str:
        """返回当前文本"""
        return self._text
    
    def boundingRect(self) -> QRectF:
        """返回边界矩形"""
        if self._fallback_item and self._fallback_item.isVisible():
            return self._fallback_item.boundingRect()
        return super().boundingRect()


class GeometryCanvas(QGraphicsView):
    # 原有信号：由 main_window 连接，触发模型层写入
    point_added = Signal(float, float)
    segment_added = Signal(str, str)       # 保留，供外部兼容使用
    circle_added = Signal(str, float)      # 保留，供外部兼容使用
    object_selected = Signal(str)
    object_moved = Signal(str, float, float)

    # BUG2 修复：新增坐标信号，替代 add_segment/circle/polygon 中的直接绘制
    segment_added_coords = Signal(float, float, float, float)   # x1, y1, x2, y2
    circle_added_coords  = Signal(float, float, float)          # cx, cy, radius
    polygon_added_coords = Signal(list)                         # [(x,y), ...]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_obj = QGraphicsScene(self)
        self.setScene(self.scene_obj)

        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        # 性能优化：禁用不必要的渲染更新
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)
        self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)

        self.scene_obj.setBackgroundBrush(QColor('#ffffff'))
        self.scene_obj.setSceneRect(-500, -500, 1000, 1000)

        self.current_tool = 'select'
        self.selected_item = None
        self.object_map = {}
        self.drawing_points = []

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0

        # 保留字典，供将来可能的其他用途；不在 add_* 方法中填充
        self.point_items   = {}
        self.segment_items = {}
        self.circle_items  = {}
        self.polygon_items = {}
        self.curve_items   = {}  # 存储所有曲线类型（圆锥曲线、函数绘图等）
        self.preview_item  = None
        
        # ------------------------------------------------------------------
        # 混合渲染优化：防抖定时器和待渲染队列
        # ------------------------------------------------------------------
        self.latex_render_timer = QTimer()
        self.latex_render_timer.setSingleShot(True)
        self.latex_render_timer.timeout.connect(self._flush_latex_rendering)
        self.pending_latex_updates = {}  # {obj_id: latex_str}
        self._is_dragging = False  # 全局拖拽状态标记

    # ------------------------------------------------------------------
    # 网格绘制（重写 drawBackground，只绘制可见区域，无独立 Item 开销）
    # ------------------------------------------------------------------
    def drawBackground(self, painter: QPainter, rect: QRectF):
        """重写背景绘制：使用单次 Painter 调用绘制网格，替代 404 个 QGraphicsLineItem"""
        super().drawBackground(painter, rect)

        grid_pen = QPen(QColor('#d3e4fe'), 0.5)
        grid_pen.setStyle(Qt.DashLine)
        painter.setPen(grid_pen)

        # 计算可见区域范围内的网格线（避免绘制不可见区域）
        grid_spacing = 20
        left   = int(rect.left()   // grid_spacing) * grid_spacing
        right  = int(rect.right()  // grid_spacing + 1) * grid_spacing
        top    = int(rect.top()    // grid_spacing) * grid_spacing
        bottom = int(rect.bottom() // grid_spacing + 1) * grid_spacing

        # 批量绘制垂直线
        path_v = QPainterPath()
        for x in range(left, right + 1, grid_spacing):
            path_v.moveTo(x, top)
            path_v.lineTo(x, bottom)
        painter.drawPath(path_v)

        # 批量绘制水平线
        path_h = QPainterPath()
        for y in range(top, bottom + 1, grid_spacing):
            path_h.moveTo(left, y)
            path_h.lineTo(right, y)
        painter.drawPath(path_h)

        # 坐标轴
        origin_pen = QPen(QColor('#737686'), 1)
        painter.setPen(origin_pen)
        painter.drawLine(QLineF(0, top, 0, bottom))
        painter.drawLine(QLineF(left, 0, right, 0))

    # ------------------------------------------------------------------
    # 缩放
    # ------------------------------------------------------------------
    def wheelEvent(self, event):
        zoom_in_factor  = 1.1
        zoom_out_factor = 1 / 1.1

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.apply_zoom(zoom_factor)

    def apply_zoom(self, zoom_factor):
        new_zoom = self.zoom_factor * zoom_factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.zoom_factor = new_zoom
            self.scale(zoom_factor, zoom_factor)

    def zoom_in(self):
        self.apply_zoom(1.1)

    def zoom_out(self):
        self.apply_zoom(1 / 1.1)

    # ------------------------------------------------------------------
    # BUG3 修复：set_tool 根据工具类型设置正确的拖动模式
    #   pan    -> ScrollHandDrag   （平移画布）
    #   select -> RubberBandDrag   （框选对象）
    #   其他   -> NoDrag           （几何绘制，避免拖动干扰点击坐标）
    # ------------------------------------------------------------------
    def set_tool(self, tool):
        self.current_tool = tool
        if tool == 'pan':
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        elif tool == 'select':
            self.setDragMode(QGraphicsView.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.NoDrag)

    # ------------------------------------------------------------------
    # 鼠标事件
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())

        if self.current_tool == 'select':
            super().mousePressEvent(event)
            return

        # 多边形：右键完成绘制
        if (event.button() == Qt.RightButton
                and self.current_tool == 'polygon'
                and len(self.drawing_points) >= 3):
            self.add_polygon()
            return

        if self.current_tool == 'point':
            self.add_point(scene_pos.x(), scene_pos.y())

        elif self.current_tool == 'segment':
            self.drawing_points.append((scene_pos.x(), scene_pos.y()))
            if len(self.drawing_points) == 2:
                self.add_segment()
                self.drawing_points.clear()

        elif self.current_tool == 'circle':
            if len(self.drawing_points) == 0:
                self.drawing_points.append((scene_pos.x(), scene_pos.y()))
            else:
                dx = scene_pos.x() - self.drawing_points[0][0]
                dy = scene_pos.y() - self.drawing_points[0][1]
                radius = (dx**2 + dy**2) ** 0.5
                self.add_circle(self.drawing_points[0], radius)
                self.drawing_points.clear()

        elif self.current_tool == 'polygon':
            self.drawing_points.append((scene_pos.x(), scene_pos.y()))
            if len(self.drawing_points) >= 2:
                self.update_polygon_preview()

        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())

        if self.current_tool == 'segment' and len(self.drawing_points) == 1:
            self.update_segment_preview(scene_pos)
        elif self.current_tool == 'circle' and len(self.drawing_points) == 1:
            self.update_circle_preview(scene_pos)
        elif self.current_tool == 'polygon' and len(self.drawing_points) >= 1:
            self.update_polygon_preview(scene_pos)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.current_tool in ['segment', 'circle']:
            pass
        super().mouseReleaseEvent(event)

    # ------------------------------------------------------------------
    # BUG2 修复：add_point 只发射信号，不直接绘制
    #   实际绘制由 main_window.on_point_added -> draw_object 统一完成
    # ------------------------------------------------------------------
    def add_point(self, x, y):
        self.point_added.emit(x, y)

    # ------------------------------------------------------------------
    # BUG2 修复：add_segment 移除预览项，只发射坐标信号，不直接绘制
    # ------------------------------------------------------------------
    def add_segment(self):
        if len(self.drawing_points) != 2:
            return

        # 移除预览线
        if self.preview_item is not None:
            self.scene_obj.removeItem(self.preview_item)
            self.preview_item = None

        p1, p2 = self.drawing_points
        self.segment_added_coords.emit(p1[0], p1[1], p2[0], p2[1])

    # ------------------------------------------------------------------
    # BUG2 修复：add_circle 移除预览项，只发射坐标信号，不直接绘制
    # ------------------------------------------------------------------
    def add_circle(self, center, radius):
        # 移除预览圆
        if self.preview_item is not None:
            self.scene_obj.removeItem(self.preview_item)
            self.preview_item = None

        cx, cy = center
        self.circle_added_coords.emit(cx, cy, radius)

    # ------------------------------------------------------------------
    # BUG1 + BUG2 修复：
    #   - 先保存点列表再清空（BUG1）
    #   - 移除预览项（清理）
    #   - 只发射信号，不直接绘制（BUG2）
    # ------------------------------------------------------------------
    def add_polygon(self):
        if len(self.drawing_points) < 3:
            return

        # BUG1 修复：先保存，再清空，最后用保存的列表发射信号
        saved_points = self.drawing_points.copy()
        self.drawing_points.clear()

        # 移除预览多边形
        if self.preview_item is not None:
            self.scene_obj.removeItem(self.preview_item)
            self.preview_item = None

        self.polygon_added_coords.emit(saved_points)

    # ------------------------------------------------------------------
    # 预览辅助方法（绘制虚线预览，不写入 object_map）
    # ------------------------------------------------------------------
    def update_segment_preview(self, scene_pos):
        if len(self.drawing_points) != 1:
            return

        p1 = self.drawing_points[0]
        if self.preview_item is not None:
            self.scene_obj.removeItem(self.preview_item)

        self.preview_item = QGraphicsLineItem(p1[0], p1[1], scene_pos.x(), scene_pos.y())
        self.preview_item.setPen(QPen(QColor('#4b41e1'), 2, Qt.DashLine))
        self.scene_obj.addItem(self.preview_item)

    def update_circle_preview(self, scene_pos):
        if len(self.drawing_points) != 1:
            return

        cx, cy = self.drawing_points[0]
        dx = scene_pos.x() - cx
        dy = scene_pos.y() - cy
        radius = (dx**2 + dy**2) ** 0.5

        if self.preview_item is not None:
            self.scene_obj.removeItem(self.preview_item)

        self.preview_item = QGraphicsEllipseItem(
            cx - radius, cy - radius, radius * 2, radius * 2
        )
        self.preview_item.setPen(QPen(QColor('#006058'), 2, Qt.DashLine))
        self.preview_item.setBrush(QBrush(Qt.NoBrush))
        self.scene_obj.addItem(self.preview_item)

    def update_polygon_preview(self, scene_pos=None):
        if len(self.drawing_points) < 1:
            return

        if self.preview_item is not None:
            self.scene_obj.removeItem(self.preview_item)

        polygon = QPolygonF()
        for point in self.drawing_points:
            polygon.append(QPointF(point[0], point[1]))

        if scene_pos:
            polygon.append(QPointF(scene_pos.x(), scene_pos.y()))

        self.preview_item = QGraphicsPolygonItem(polygon)
        self.preview_item.setPen(QPen(QColor('#9333ea'), 2, Qt.DashLine))
        self.preview_item.setBrush(QBrush(QColor('#9333ea'), Qt.Dense4Pattern))
        self.scene_obj.addItem(self.preview_item)

    # ------------------------------------------------------------------
    # 清空画布
    # ------------------------------------------------------------------
    def clear_canvas(self):
        self.scene_obj.clear()
        self.object_map.clear()
        self.point_items.clear()
        self.segment_items.clear()
        self.circle_items.clear()
        self.polygon_items.clear()
        self.curve_items.clear()
        self.drawing_points.clear()
        self.preview_item = None
        # 重置绘制状态，防止下次 mouseMoveEvent 操作野指针
        # 注意：不强制重置 current_tool，保持用户当前的工具选择（如用户正在连续画点）

    # ------------------------------------------------------------------
    # 由 main_window 调用，统一绘制并写入 object_map
    # ------------------------------------------------------------------
    def draw_object(self, obj_id, obj_data):
        obj_type = obj_data.get('type')

        if obj_type == 'Point':
            x    = obj_data['coordinates'].get('x', 0)
            y    = obj_data['coordinates'].get('y', 0)
            name = obj_data.get('name', '')

            point_item = QGraphicsEllipseItem(x - 5, y - 5, 10, 10)
            point_item.setBrush(QBrush(QColor('#004ac6')))
            point_item.setPen(QPen(QColor('#004ac6'), 1))
            point_item.setFlags(
                QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable
            )
            point_item.setZValue(10)

            # 使用 MathGraphicsItem 替代 QGraphicsTextItem，支持 LaTeX 渲染
            text_item = MathGraphicsItem(name, use_latex=True)
            text_item.setPos(x + 8, y - 12)
            text_item.setZValue(11)

            self.scene_obj.addItem(point_item)
            self.scene_obj.addItem(text_item)

            self.object_map[obj_id] = {'point': point_item, 'text': text_item}

        elif obj_type == 'Segment':
            x1 = obj_data['coordinates'].get('x1', 0)
            y1 = obj_data['coordinates'].get('y1', 0)
            x2 = obj_data['coordinates'].get('x2', 0)
            y2 = obj_data['coordinates'].get('y2', 0)

            segment_item = QGraphicsLineItem(x1, y1, x2, y2)
            segment_item.setPen(QPen(QColor('#4b41e1'), 2))
            segment_item.setFlags(QGraphicsItem.ItemIsSelectable)

            self.scene_obj.addItem(segment_item)
            self.object_map[obj_id] = {'segment': segment_item}

        elif obj_type == 'Circle':
            cx = obj_data['coordinates'].get('cx', 0)
            cy = obj_data['coordinates'].get('cy', 0)
            r  = obj_data['coordinates'].get('r', 1)

            circle_item = QGraphicsEllipseItem(cx - r, cy - r, r * 2, r * 2)
            circle_item.setPen(QPen(QColor('#006058'), 2))
            circle_item.setBrush(QBrush(Qt.NoBrush))
            circle_item.setFlags(QGraphicsItem.ItemIsSelectable)

            self.scene_obj.addItem(circle_item)
            self.object_map[obj_id] = {'circle': circle_item}

        elif obj_type == 'Polygon':
            points = obj_data.get('points', [])
            name   = obj_data.get('name', '')

            polygon_item = QGraphicsPolygonItem()
            polygon = QPolygonF()
            for point in points:
                polygon.append(QPointF(point[0], point[1]))
            polygon_item.setPolygon(polygon)
            polygon_item.setPen(QPen(QColor('#9333ea'), 2))
            polygon_item.setBrush(QBrush(QColor('#9333ea'), Qt.Dense4Pattern))
            polygon_item.setFlags(QGraphicsItem.ItemIsSelectable)

            self.scene_obj.addItem(polygon_item)
            self.object_map[obj_id] = {'polygon': polygon_item}

        # 新增：圆锥曲线和函数绘图
        elif obj_type in ['Ellipse', 'Hyperbola', 'Parabola', 'ConicSection', 
                          'FunctionPlot', 'ImplicitPlot', 'PolarPlot', 'Locus']:
            points = obj_data.get('points_data', []) or obj_data.get('coordinates', {}).get('points', [])
            
            if not points:
                return
            
            # 使用 QPainterPath 绘制平滑曲线
            path = QPainterPath()
            if len(points) > 0:
                path.moveTo(QPointF(points[0][0], points[0][1]))
                for point in points[1:]:
                    path.lineTo(QPointF(point[0], point[1]))
            
            # 根据类型设置不同颜色
            color_map = {
                'Ellipse': QColor('#ff6b00'),
                'Hyperbola': QColor('#d90429'),
                'Parabola': QColor('#7209b7'),
                'ConicSection': QColor('#f72585'),
                'FunctionPlot': QColor('#4cc9f0'),
                'ImplicitPlot': QColor('#4361ee'),
                'PolarPlot': QColor('#3a0ca3'),
                'Locus': QColor('#f72585'),
            }
            color = color_map.get(obj_type, QColor('#004ac6'))
            
            curve_item = self.scene_obj.addPath(path, QPen(color, 2), QBrush(Qt.NoBrush))
            curve_item.setFlags(QGraphicsItem.ItemIsSelectable)
            
            self.object_map[obj_id] = {'curve': curve_item}
            self.curve_items[obj_id] = curve_item

    def update_object(self, obj_id, obj_data):
        if obj_id not in self.object_map:
            self.draw_object(obj_id, obj_data)
            return

        obj_type = obj_data.get('type')
        obj_info = self.object_map[obj_id]

        if obj_type == 'Point':
            x = obj_data['coordinates'].get('x', 0)
            y = obj_data['coordinates'].get('y', 0)

            obj_info['point'].setRect(x - 5, y - 5, 10, 10)
            
            # [P0修复 Bug3] 同步更新关联的文本图元内容
            text_item = obj_info.get('text')
            new_name = obj_data.get('name', '')
            if text_item:
                if hasattr(text_item, 'set_text'):
                    text_item.set_text(new_name)
                elif hasattr(text_item, 'setPlainText'):
                    text_item.setPlainText(new_name)
                # 同步更新文本的位置，保持相对偏移
                text_item.setPos(x + 8, y - 12)

        elif obj_type == 'Segment':
            x1 = obj_data['coordinates'].get('x1', 0)
            y1 = obj_data['coordinates'].get('y1', 0)
            x2 = obj_data['coordinates'].get('x2', 0)
            y2 = obj_data['coordinates'].get('y2', 0)

            obj_info['segment'].setLine(x1, y1, x2, y2)

        elif obj_type == 'Circle':
            cx = obj_data['coordinates'].get('cx', 0)
            cy = obj_data['coordinates'].get('cy', 0)
            r  = obj_data['coordinates'].get('r', 1)

            obj_info['circle'].setRect(cx - r, cy - r, r * 2, r * 2)

        elif obj_type == 'Polygon':
            points = obj_data.get('points', [])
            polygon = QPolygonF()
            for point in points:
                polygon.append(QPointF(point[0], point[1]))
            obj_info['polygon'].setPolygon(polygon)

        # 新增：更新曲线对象
        elif obj_type in ['Ellipse', 'Hyperbola', 'Parabola', 'ConicSection', 
                          'FunctionPlot', 'ImplicitPlot', 'PolarPlot', 'Locus']:
            # 删除旧曲线并重新绘制
            self.remove_object(obj_id)
            self.draw_object(obj_id, obj_data)

    def remove_object(self, obj_id):
        if obj_id in self.object_map:
            obj_info = self.object_map[obj_id]
            for item in obj_info.values():
                self.scene_obj.removeItem(item)
            del self.object_map[obj_id]
            # 如果是曲线对象，也从 curve_items 中删除
            if obj_id in self.curve_items:
                del self.curve_items[obj_id]

    def select_object(self, obj_id):
        if obj_id in self.object_map:
            for item in self.object_map[obj_id].values():
                item.setSelected(True)

    def focus_on_object(self, obj_id):
        if obj_id in self.object_map:
            first_item = list(self.object_map[obj_id].values())[0]
            self.centerOn(first_item.sceneBoundingRect().center())
    
    # ------------------------------------------------------------------
    # 混合渲染优化：降级渲染与防抖机制
    # ------------------------------------------------------------------
    def update_object_equation(self, obj_id: str, new_latex: str):
        """
        更新对象的公式显示（带防抖优化）
        
        拖拽时疯狂调用这个方法：
        1. 先用普通文本极速占位（降级渲染）
        2. 存入待渲染队列，重启 200ms 的防抖定时器
        
        Args:
            obj_id: 对象 ID
            new_latex: 新的 LaTeX 公式字符串
        """
        # 1. 立即更新为普通文本占位符（极速）
        self._set_fast_fallback_text(obj_id, new_latex)
        
        # 2. 存入待渲染队列，重启防抖定时器
        self.pending_latex_updates[obj_id] = new_latex
        self.latex_render_timer.start(200)  # 200ms 防抖
    
    def _set_fast_fallback_text(self, obj_id: str, text: str):
        """
        设置快速降级文本（拖拽时使用）
        
        Args:
            obj_id: 对象 ID
            text: 显示文本
        """
        if obj_id not in self.object_map:
            return
        
        obj_info = self.object_map[obj_id]
        text_item = obj_info.get('text')
        
        if text_item is None:
            return
        
        # 如果是 MathGraphicsItem，设置为拖拽模式
        if isinstance(text_item, MathGraphicsItem):
            text_item.set_dragging(True)
            text_item.set_text(text)
        elif isinstance(text_item, QGraphicsTextItem):
            # 兼容旧的 QGraphicsTextItem
            text_item.setPlainText(text)
    
    def _flush_latex_rendering(self):
        """
        鼠标停下 200ms 后执行：将占位符替换为真正的高清 LaTeX SVG
        """
        if not self.pending_latex_updates:
            return
        
        for obj_id, latex_str in self.pending_latex_updates.items():
            if obj_id in self.object_map:
                obj_info = self.object_map[obj_id]
                text_item = obj_info.get('text')
                
                if text_item is None:
                    continue
                
                # 如果是 MathGraphicsItem，恢复 LaTeX 渲染
                if isinstance(text_item, MathGraphicsItem):
                    text_item.set_dragging(False)
                    text_item.set_text(latex_str)
        
        self.pending_latex_updates.clear()
    
    def begin_drag_operation(self):
        """
        开始拖拽操作：通知所有 MathGraphicsItem 进入降级模式
        """
        self._is_dragging = True
        for obj_info in self.object_map.values():
            text_item = obj_info.get('text')
            if isinstance(text_item, MathGraphicsItem):
                text_item.set_dragging(True)
    
    def end_drag_operation(self):
        """
        结束拖拽操作：恢复 LaTeX 渲染
        """
        self._is_dragging = False
        # 触发一次延迟渲染
        if self.pending_latex_updates:
            self._flush_latex_rendering()
        else:
            # 如果没有待更新的公式，直接恢复所有项
            for obj_info in self.object_map.values():
                text_item = obj_info.get('text')
                if isinstance(text_item, MathGraphicsItem):
                    text_item.set_dragging(False)
