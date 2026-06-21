import sys
import uuid
import math
from typing import List, Dict

from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainter
from PySide6.QtCore import Qt

# =======================================================================
# MathLab GeoGebra Prototype Core Engine (Phase 1 & 2)
# =======================================================================

class GeoEntity:
    def __init__(self, name: str, parents: List['GeoEntity'] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.parents = parents or []
        self.children = []
        self.is_visible = True
        
    def add_child(self, child: 'GeoEntity'):
        if child not in self.children:
            self.children.append(child)
            
    def compute(self):
        pass
        
    def notify_update(self):
        self.compute()
        for child in self.children:
            child.notify_update()

class GeoPoint(GeoEntity):
    def __init__(self, name: str, x: float = 0, y: float = 0, parents=None):
        super().__init__(name, parents)
        self.x = x
        self.y = y
        self.color = "#4cc9f0" if not parents else "#f72585"
        
    def set_coords(self, x: float, y: float):
        if not self.parents:
            self.x = x
            self.y = y
            self.notify_update()

class GeoLine(GeoEntity):
    def __init__(self, name: str, p1: GeoPoint, p2: GeoPoint):
        super().__init__(name, parents=[p1, p2])
        p1.add_child(self)
        p2.add_child(self)
        self.color = "#4361ee"
        
    def compute(self):
        pass

class GeoCircle(GeoEntity):
    """由圆心和圆上一点定义的圆"""
    def __init__(self, name: str, center: GeoPoint, radius_point: GeoPoint):
        super().__init__(name)
        self.parents = [center, radius_point]
        center.add_child(self)
        radius_point.add_child(self)
        self.color = "#d4d4d4"
        
        self.center_x = 0.0
        self.center_y = 0.0
        self.r = 0.0
        self.compute()

    def compute(self):
        c, rp = self.parents
        self.center_x, self.center_y = c.x, c.y
        # 计算欧氏距离作为半径
        self.r = math.hypot(rp.x - c.x, rp.y - c.y)

# ──────────────────────────────────────────────────────────
# 核心解析求解器 (Analytical Solvers)
# ──────────────────────────────────────────────────────────

def solve_line_circle(line: GeoLine, circle: GeoCircle, root_index: int):
    """
    直线与圆的交点求解器 (使用参数方程避免斜率无穷大问题)
    """
    p1, p2 = line.parents
    c = circle.parents[0] # 圆心
    
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    
    fx = p1.x - circle.center_x
    fy = p1.y - circle.center_y
    
    a = dx*dx + dy*dy
    b = 2 * (fx*dx + fy*dy)
    c_eq = fx*fx + fy*fy - circle.r*circle.r
    
    if a == 0:
        return None, False

    delta = b*b - 4*a*c_eq
    
    if delta < 0:
        return None, False
        
    sign = 1 if root_index == 0 else -1
    t = (-b + sign * math.sqrt(delta)) / (2 * a)
    
    intersect_x = p1.x + t * dx
    intersect_y = p1.y + t * dy
    
    return (intersect_x, intersect_y), True

def solve_line_line(l1: GeoLine, l2: GeoLine):
    x1, y1 = l1.parents[0].x, l1.parents[0].y
    x2, y2 = l1.parents[1].x, l1.parents[1].y
    x3, y3 = l2.parents[0].x, l2.parents[0].y
    x4, y4 = l2.parents[1].x, l2.parents[1].y

    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-8:
        return None, False

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    px = x1 + t * (x2 - x1)
    py = y1 + t * (y2 - y1)
    return (px, py), True

class GeoIntersection(GeoPoint):
    """高级交点实体"""
    def __init__(self, name: str, shape1: GeoEntity, shape2: GeoEntity, root_index: int = 0):
        super().__init__(name, parents=[shape1, shape2])
        shape1.add_child(self)
        shape2.add_child(self)
        self.root_index = root_index
        self.color = "#C586C0" # 交点使用紫色高亮
        self.compute()

    def compute(self):
        s1, s2 = self.parents
        
        result = None
        is_valid = False
        
        if isinstance(s1, GeoLine) and isinstance(s2, GeoCircle):
            result, is_valid = solve_line_circle(s1, s2, self.root_index)
        elif isinstance(s1, GeoCircle) and isinstance(s2, GeoLine):
            result, is_valid = solve_line_circle(s2, s1, self.root_index)
        elif isinstance(s1, GeoLine) and isinstance(s2, GeoLine):
            result, is_valid = solve_line_line(s1, s2)
            
        if is_valid and result:
            self.x, self.y = result
            self.is_visible = True
        else:
            self.is_visible = False


class GeometryEngine:
    def __init__(self):
        self.entities: Dict[str, GeoEntity] = {}
        
    def add_free_point(self, name: str, x: float, y: float):
        pt = GeoPoint(name, x, y)
        self.entities[pt.id] = pt
        return pt
        
    def add_segment(self, name: str, p1: GeoPoint, p2: GeoPoint):
        line = GeoLine(name, p1, p2)
        self.entities[line.id] = line
        return line


# =======================================================================
# MathLab GeoGebra Prototype UI Components
# =======================================================================

class QGeoPointItem(QGraphicsEllipseItem):
    """Qt 场景中的点图元，绑定到底层的 GeoPoint"""
    def __init__(self, geo_point: GeoPoint, scene: QGraphicsScene, engine_ui_link):
        super().__init__(-5, -5, 10, 10) # 以自身坐标原点为中心，半径为5的圆
        self.geo_point = geo_point
        self.engine_ui_link = engine_ui_link
        
        color = QColor(geo_point.color)
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.GlobalColor.transparent))
        
        self.setPos(geo_point.x, geo_point.y)
        
        # 自由点可拖动
        if not geo_point.parents:
            self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable)
            self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable)
            self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            self.geo_point.set_coords(new_pos.x(), new_pos.y())
            self.engine_ui_link.sync_ui_from_engine()
        return super().itemChange(change, value)


class GeometryCanvas(QGraphicsView):
    """交互式几何画板 UI 面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = GeometryEngine()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.scene.setBackgroundBrush(QColor("#1e1e1e"))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        self.ui_items = {}
        self._setup_test_scene()

    def _setup_test_scene(self):
        # 1. 创建一条直线
        p1 = self.engine.add_free_point("P1", 100, 150)
        p2 = self.engine.add_free_point("P2", 400, 150)
        line = self.engine.add_segment("L", p1, p2)
        
        # 2. 创建一个圆
        c_center = self.engine.add_free_point("Center", 250, 250)
        c_edge = self.engine.add_free_point("Edge", 250, 150)
        circle = GeoCircle("C", c_center, c_edge)
        self.engine.entities[circle.id] = circle
        
        # 3. 创建两个交点
        intersect1 = GeoIntersection("I1", line, circle, root_index=0)
        intersect2 = GeoIntersection("I2", line, circle, root_index=1)
        self.engine.entities[intersect1.id] = intersect1
        self.engine.entities[intersect2.id] = intersect2
        
        # 将它们统统添加到画布渲染
        self._create_ui_item(circle)
        self._create_ui_item(line)
        self._create_ui_item(p1)
        self._create_ui_item(p2)
        self._create_ui_item(c_center)
        self._create_ui_item(c_edge)
        self._create_ui_item(intersect1)
        self._create_ui_item(intersect2)

    def _create_ui_item(self, entity):
        if isinstance(entity, GeoPoint):
            item = QGeoPointItem(entity, self.scene, self)
            # 提升点图元的 Z 轴层级，防止被线遮挡
            item.setZValue(10)
            self.scene.addItem(item)
            self.ui_items[entity.id] = item
            
        elif isinstance(entity, GeoLine):
            item = QGraphicsLineItem()
            pen = QPen(QColor(entity.color), 2)
            item.setPen(pen)
            self.scene.addItem(item)
            self.ui_items[entity.id] = item
            
        elif isinstance(entity, GeoCircle):
            item = QGraphicsEllipseItem()
            pen = QPen(QColor(entity.color), 2)
            item.setPen(pen)
            self.scene.addItem(item)
            self.ui_items[entity.id] = item
            
        self.sync_ui_from_engine()

    def sync_ui_from_engine(self):
        """遍历引擎中所有实体，根据其最新的计算结果更新 UI 图元"""
        for entity_id, item in self.ui_items.items():
            entity = self.engine.entities.get(entity_id)
            if not entity: continue
            
            # 处理拓扑可见性
            if not entity.is_visible:
                item.hide()
                continue
            else:
                item.show()
            
            # 更新坐标
            if isinstance(entity, GeoPoint) and entity.parents:
                item.setPos(entity.x, entity.y)
                
            elif isinstance(entity, GeoLine):
                item.setLine(entity.parents[0].x, entity.parents[0].y, 
                             entity.parents[1].x, entity.parents[1].y)
                             
            elif isinstance(entity, GeoCircle):
                item.setRect(entity.center_x - entity.r, entity.center_y - entity.r, 
                             entity.r * 2, entity.r * 2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GeometryCanvas()
    window.setWindowTitle("MathLab GeoGebra Prototype (Phase 2)")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
