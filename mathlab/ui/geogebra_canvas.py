from enum import Enum
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainter
from PySide6.QtCore import Qt

from mathlab.core.geogebra_engine import GeometryEngine, GeoEntity, GeoPoint, GeoLine, GeoCircle, GeoIntersection

class ToolMode(Enum):
    """画板的工具状态机枚举"""
    SELECT = "select"       # 默认：选中并拖动
    POINT = "point"         # 自由打点
    LINE = "line"           # 绘制两点连线
    INTERSECT = "intersect" # 求两图形交点


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
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            self.geo_entity.set_coords(new_pos.x(), new_pos.y())
            self.engine_ui_link.sync_ui_from_engine()
        return super().itemChange(change, value)


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
        if hasattr(clicked_item, 'geo_entity'):
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
                pt = self.engine.add_free_point(f"P{self._pt_counter}", scene_pos.x(), scene_pos.y())
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
                    
                    i1 = GeoIntersection(f"I{self._intersect_counter}", shape1, shape2, root_index=0)
                    self._intersect_counter += 1
                    self.engine.entities[i1.id] = i1
                    self._create_ui_item(i1)
                    
                    if isinstance(shape1, GeoCircle) or isinstance(shape2, GeoCircle):
                        i2 = GeoIntersection(f"I{self._intersect_counter}", shape1, shape2, root_index=1)
                        self._intersect_counter += 1
                        self.engine.entities[i2.id] = i2
                        self._create_ui_item(i2)
                        
                    self.action_buffer.clear()
            return

    def _create_ui_item(self, entity):
        if isinstance(entity, GeoPoint):
            item = QGeoPointItem(entity, self.scene, self)
            item.setZValue(10)
            self.scene.addItem(item)
            self.ui_items[entity.id] = item
            
        elif isinstance(entity, GeoLine):
            item = QGraphicsLineItem()
            item.geo_entity = entity
            pen = QPen(QColor(entity.color), 3)
            item.setPen(pen)
            self.scene.addItem(item)
            self.ui_items[entity.id] = item
            
        elif isinstance(entity, GeoCircle):
            item = QGraphicsEllipseItem()
            item.geo_entity = entity
            pen = QPen(QColor(entity.color), 3)
            item.setPen(pen)
            self.scene.addItem(item)
            self.ui_items[entity.id] = item
            
        self.sync_ui_from_engine()

    def sync_ui_from_engine(self):
        for entity_id, item in self.ui_items.items():
            entity = self.engine.entities.get(entity_id)
            if not entity: continue
            
            if not entity.is_visible:
                item.hide()
                continue
            else:
                item.show()
                
            if isinstance(entity, GeoPoint) and entity.parents:
                item.setPos(entity.x, entity.y)
                
            elif isinstance(entity, GeoLine):
                item.setLine(entity.parents[0].x, entity.parents[0].y, 
                             entity.parents[1].x, entity.parents[1].y)
                             
            elif isinstance(entity, GeoCircle):
                item.setRect(entity.center_x - entity.r, entity.center_y - entity.r, 
                             entity.r * 2, entity.r * 2)
