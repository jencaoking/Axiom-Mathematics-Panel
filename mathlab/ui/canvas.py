from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainter
from PySide6.QtCore import Qt, QPointF

from mathlab.core.geometry_engine import GeometryEngine, GeoPoint, GeoLine

class QGeoPointItem(QGraphicsEllipseItem):
    """Qt 场景中的点图元，绑定到底层的 GeoPoint"""
    def __init__(self, geo_point: GeoPoint, scene: QGraphicsScene, engine_ui_link):
        super().__init__(-5, -5, 10, 10) # 以自身坐标原点为中心，半径为5的圆
        self.geo_point = geo_point
        self.engine_ui_link = engine_ui_link # 指向画布大管家
        
        # 外观设置
        color = QColor(geo_point.color)
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.GlobalColor.transparent))
        
        # 初始位置
        self.setPos(geo_point.x, geo_point.y)
        
        # 如果是自由点，允许选中和拖动
        if not geo_point.parents:
            self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable)
            self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable)
            self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def itemChange(self, change, value):
        # 拦截拖动事件
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange and self.scene():
            # 1. 更新底层数学模型
            new_pos = value
            self.geo_point.set_coords(new_pos.x(), new_pos.y())
            # 2. 通知 UI 大管家：模型变了，请重绘所有相关图形
            self.engine_ui_link.sync_ui_from_engine()
            
        return super().itemChange(change, value)

class GeometryCanvas(QGraphicsView):
    """
    交互式几何画板 UI 面板
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = GeometryEngine()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # 极客风格设置
        self.scene.setBackgroundBrush(QColor("#1e1e1e"))
        self.setRenderHint(QPainter.RenderHint.Antialiasing) # 开启抗锯齿，线条更平滑
        
        # 存储底层 ID 到 UI Item 的映射，方便查找
        self.ui_items = {}
        
        # 建立一个测试场景
        self._setup_test_scene()

    def _setup_test_scene(self):
        """创建一个带约束的测试场景：A和B是自由点，C是AB中点，并连接线段"""
        # 1. 建立数学约束关系 (只在引擎里操作)
        p_A = self.engine.add_free_point("A", 100, 100)
        p_B = self.engine.add_free_point("B", 300, 200)
        line_AB = self.engine.add_segment("AB", p_A, p_B)
        p_C = self.engine.add_midpoint("C", p_A, p_B) # C 约束为中点
        
        # 2. 将数学实体渲染到 UI
        self._create_ui_item(line_AB)  # 先画线，被点压在下面
        self._create_ui_item(p_A)
        self._create_ui_item(p_B)
        self._create_ui_item(p_C)

    def _create_ui_item(self, entity):
        if isinstance(entity, GeoPoint):
            item = QGeoPointItem(entity, self.scene, self)
            self.scene.addItem(item)
            self.ui_items[entity.id] = item
        
        elif isinstance(entity, GeoLine):
            item = QGraphicsLineItem()
            pen = QPen(QColor(entity.color), 2)
            item.setPen(pen)
            self.scene.addItem(item)
            self.ui_items[entity.id] = item
            
        self.sync_ui_from_engine() # 同步一次初始状态

    def sync_ui_from_engine(self):
        """遍历引擎中所有实体，根据其最新的计算结果更新 UI 图元"""
        for entity_id, item in self.ui_items.items():
            entity = self.engine.entities.get(entity_id)
            if not entity: continue
            
            if isinstance(entity, GeoPoint):
                # 只同步被动变化的点（约束点），自由点自己会跟着鼠标走
                if entity.parents:
                    item.setPos(entity.x, entity.y)
                    
            elif isinstance(entity, GeoLine):
                item.setLine(entity.start[0], entity.start[1], entity.end[0], entity.end[1])
