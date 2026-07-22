from enum import Enum
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
)
from PySide6.QtGui import QPen, QBrush, QColor, QPainter
from PySide6.QtCore import Qt, QVariantAnimation, QPointF

from mathlab.core.geogebra_engine import (
    GeometryEngine,
    GeoEntity,
    GeoPoint,
    GeoLine,
    GeoCircle,
    GeoIntersection,
)
from mathlab.core.animation import CreateAnimation


class ToolMode(Enum):
    """画板的工具状态机枚举"""

    SELECT = "select"  # 默认：选中并拖动
    POINT = "point"  # 自由打点
    LINE = "line"  # 绘制两点连线
    INTERSECT = "intersect"  # 求两图形交点


class QGeoPointItem(QGraphicsEllipseItem):
    """Qt 场景中的点图元，绑定到底层的 GeoPoint"""

    def __init__(self, geo_point: GeoPoint, scene: QGraphicsScene, engine_ui_link):
        super().__init__(-5, -5, 10, 10)
        self.geo_entity = geo_point  # 用于被状态机识别
        self.engine_ui_link = engine_ui_link

        color = QColor(geo_point.color)
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.GlobalColor.transparent))

        self.setPos(geo_point.x, geo_point.y)

        if not geo_point.parents:
            self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable)
            self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable)
            self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def itemChange(self, change, value):
        if (
            change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange
            and self.scene()
        ):
            new_pos = value
            self.geo_entity.set_coords(new_pos.x(), new_pos.y())

            canvas = self.engine_ui_link
            # 🌟 灵魂连击：拖动的瞬间，向 Jupyter 狂发坐标数据 🌟
            if hasattr(canvas, "ipc_client") and canvas.ipc_client:
                canvas.ipc_client.sync_variable(
                    f"{self.geo_entity.name}_x", new_pos.x()
                )
                canvas.ipc_client.sync_variable(
                    f"{self.geo_entity.name}_y", new_pos.y()
                )

            self.engine_ui_link.sync_ui_from_engine()
        return super().itemChange(change, value)


class AnimatedLineItem(QGraphicsLineItem):
    """支持生长动画的直线"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._full_start = QPointF(0, 0)
        self._full_end = QPointF(0, 0)
        self._progress = 1.0  # 默认完全画完

    def set_full_line(self, x1, y1, x2, y2):
        """记录直线的终极形态"""
        self._full_start = QPointF(x1, y1)
        self._full_end = QPointF(x2, y2)
        self._update_geometry()

    def set_draw_progress(self, alpha: float):
        """0.0 到 1.0 的绘制进度"""
        self._progress = alpha
        self._update_geometry()

    def _update_geometry(self):
        # 向量插值：P_current = P_start + (P_end - P_start) * alpha
        dx = self._full_end.x() - self._full_start.x()
        dy = self._full_end.y() - self._full_start.y()

        cur_x = self._full_start.x() + dx * self._progress
        cur_y = self._full_start.y() + dy * self._progress

        # 真正丢给 Qt 去画的线
        self.setLine(self._full_start.x(), self._full_start.y(), cur_x, cur_y)


class AnimatedCircleItem(QGraphicsEllipseItem):
    """支持绕圈扫影生长的圆"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._progress = 1.0
        # 设置起点为顶部 (Qt中角度以1/16度为单位，3点钟是0，12点钟是90)
        self.setStartAngle(90 * 16)

    def set_full_rect(self, x, y, w, h):
        self.setRect(x, y, w, h)
        self._update_geometry()

    def set_draw_progress(self, alpha: float):
        self._progress = alpha
        self._update_geometry()

    def _update_geometry(self):
        # 跨度角度：满圆是 360 度，乘以 16 是 Qt 的内部单位
        span = int(360 * 16 * self._progress)
        self.setSpanAngle(span)


class GeoGebraCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = GeometryEngine()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.scene.setBackgroundBrush(QColor("#1e1e1e"))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.ui_items = {}

        # 🌟 状态机核心变量 🌟
        self.current_mode = ToolMode.SELECT
        self.action_buffer = []

        # 计数器
        self._pt_counter = 1
        self._line_counter = 1
        self._circle_counter = 1
        self._intersect_counter = 1

    def set_tool_mode(self, mode: ToolMode):
        self.current_mode = mode
        self.action_buffer.clear()

        if mode == ToolMode.SELECT:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif mode == ToolMode.POINT:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        clicked_item = self.scene.itemAt(scene_pos, self.transform())

        clicked_entity = None
        if hasattr(clicked_item, "geo_entity"):
            clicked_entity = clicked_item.geo_entity

        # ── 状态 1：默认拖拽模式 ──
        if self.current_mode == ToolMode.SELECT:
            super().mousePressEvent(event)
            return

        # ── 状态 2：打点模式 ──
        elif self.current_mode == ToolMode.POINT:
            if event.button() == Qt.MouseButton.LeftButton:
                name = f"P{self._pt_counter}"
                self._pt_counter += 1
                pt = self.engine.add_free_point(name, scene_pos.x(), scene_pos.y())
                self._create_ui_item(pt)
            return

        # ── 状态 3：连线模式 (需要 2 个点) ──
        elif self.current_mode == ToolMode.LINE:
            if isinstance(clicked_entity, GeoPoint):
                pt = clicked_entity
            else:
                pt = self.engine.add_free_point(
                    f"P{self._pt_counter}", scene_pos.x(), scene_pos.y()
                )
                self._pt_counter += 1
                self._create_ui_item(pt)

            self.action_buffer.append(pt)

            if len(self.action_buffer) == 2:
                p1, p2 = self.action_buffer
                if p1 != p2:
                    line = self.engine.add_segment(f"L{self._line_counter}", p1, p2)
                    self._line_counter += 1
                    self._create_ui_item(line)
                self.action_buffer.clear()
            return

        # ── 状态 4：求交模式 (需要 2 个图形) ──
        elif self.current_mode == ToolMode.INTERSECT:
            if isinstance(clicked_entity, (GeoLine, GeoCircle)):
                if clicked_entity not in self.action_buffer:
                    self.action_buffer.append(clicked_entity)

                if len(self.action_buffer) == 2:
                    shape1, shape2 = self.action_buffer

                    i1 = GeoIntersection(
                        f"I{self._intersect_counter}", shape1, shape2, root_index=0
                    )
                    self._intersect_counter += 1
                    self.engine.entities[i1.id] = i1
                    self._create_ui_item(i1)

                    if isinstance(shape1, GeoCircle) or isinstance(shape2, GeoCircle):
                        i2 = GeoIntersection(
                            f"I{self._intersect_counter}", shape1, shape2, root_index=1
                        )
                        self._intersect_counter += 1
                        self.engine.entities[i2.id] = i2
                        self._create_ui_item(i2)

                    self.action_buffer.clear()
            return

    def _create_ui_item(self, entity, animate=True):
        if isinstance(entity, GeoPoint):
            item = QGeoPointItem(entity, self.scene, self)
            item.setZValue(10)
            self.scene.addItem(item)
            self.ui_items[entity.id] = item

            if animate:
                anim = QVariantAnimation(item)
                anim.setDuration(400)
                anim.setStartValue(0.0)
                anim.setEndValue(1.0)
                anim.valueChanged.connect(item.setOpacity)
                anim.start()
                item._appear_anim = anim

        elif isinstance(entity, GeoLine):
            item = AnimatedLineItem()
            item.geo_entity = entity
            pen = QPen(QColor(entity.color), 3)
            item.setPen(pen)
            self.scene.addItem(item)
            self.ui_items[entity.id] = item

            if animate and entity.parents and len(entity.parents) >= 2:
                item.set_full_line(
                    entity.parents[0].x,
                    entity.parents[0].y,
                    entity.parents[1].x,
                    entity.parents[1].y,
                )
                create_anim = CreateAnimation(item, duration=600)
                create_anim.play()
                item._create_anim = create_anim

        elif isinstance(entity, GeoCircle):
            item = AnimatedCircleItem()
            item.geo_entity = entity
            pen = QPen(QColor(entity.color), 3)
            item.setPen(pen)
            self.scene.addItem(item)
            self.ui_items[entity.id] = item

            if animate:
                item.set_full_rect(
                    entity.center_x - entity.r,
                    entity.center_y - entity.r,
                    entity.r * 2,
                    entity.r * 2,
                )
                create_anim = CreateAnimation(item, duration=600)
                create_anim.play()
                item._create_anim = create_anim

        self.sync_ui_from_engine()

    def sync_ui_from_engine(self):
        for entity_id, item in self.ui_items.items():
            entity = self.engine.entities.get(entity_id)
            if not entity:
                continue

            if not entity.is_visible:
                item.hide()
                continue
            else:
                item.show()

            if isinstance(entity, GeoPoint) and entity.parents:
                item.setPos(entity.x, entity.y)

            elif isinstance(entity, GeoLine):
                if isinstance(item, AnimatedLineItem):
                    item.set_full_line(
                        entity.parents[0].x,
                        entity.parents[0].y,
                        entity.parents[1].x,
                        entity.parents[1].y,
                    )
                else:
                    item.setLine(
                        entity.parents[0].x,
                        entity.parents[0].y,
                        entity.parents[1].x,
                        entity.parents[1].y,
                    )

            elif isinstance(entity, GeoCircle):
                if isinstance(item, AnimatedCircleItem):
                    item.set_full_rect(
                        entity.center_x - entity.r,
                        entity.center_y - entity.r,
                        entity.r * 2,
                        entity.r * 2,
                    )
                else:
                    item.setRect(
                        entity.center_x - entity.r,
                        entity.center_y - entity.r,
                        entity.r * 2,
                        entity.r * 2,
                    )

        if hasattr(self, "on_engine_updated") and self.on_engine_updated:
            self.on_engine_updated()
