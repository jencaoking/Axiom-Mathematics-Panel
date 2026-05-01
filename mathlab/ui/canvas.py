from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem,
    QGraphicsTextItem, QMenu, QGraphicsSceneMouseEvent
)
from PySide6.QtGui import QPolygonF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QCursor, QPainter
from PySide6.QtCore import Qt, QPointF, QRectF, Signal

class GeometryCanvas(QGraphicsView):
    point_added = Signal(float, float)
    segment_added = Signal(str, str)
    circle_added = Signal(str, float)
    object_selected = Signal(str)
    object_moved = Signal(str, float, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_obj = QGraphicsScene(self)
        self.setScene(self.scene_obj)
        
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        self.init_grid()
        
        self.current_tool = 'select'
        self.selected_item = None
        self.object_map = {}
        self.drawing_points = []
        
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        
        self.point_items = {}
        self.segment_items = {}
        self.circle_items = {}
        self.polygon_items = {}
        self.preview_item = None
        
    def init_grid(self):
        self.scene_obj.setBackgroundBrush(QColor('#ffffff'))
        
        grid_pen = QPen(QColor('#d3e4fe'), 0.5)
        grid_pen.setStyle(Qt.DashLine)
        
        for i in range(-100, 101):
            x = i * 20
            self.scene_obj.addLine(x, -1000, x, 1000, grid_pen)
            self.scene_obj.addLine(-1000, x, 1000, x, grid_pen)
        
        origin_pen = QPen(QColor('#737686'), 1)
        self.scene_obj.addLine(0, -1000, 0, 1000, origin_pen)
        self.scene_obj.addLine(-1000, 0, 1000, 0, origin_pen)
        
        self.scene_obj.setSceneRect(-500, -500, 1000, 1000)
    
    def wheelEvent(self, event):
        zoom_in_factor = 1.1
        zoom_out_factor = 1 / 1.1
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        
        new_zoom = self.zoom_factor * zoom_factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.zoom_factor = new_zoom
            self.scale(zoom_factor, zoom_factor)
    
    def set_tool(self, tool):
        self.current_tool = tool
        if tool == 'pan':
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        else:
            self.setDragMode(QGraphicsView.RubberBandDrag)
    
    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        
        if self.current_tool == 'select':
            super().mousePressEvent(event)
            return
        
        if event.button() == Qt.RightButton and self.current_tool == 'polygon' and len(self.drawing_points) >= 3:
            self.add_polygon()
            return
        
        if self.current_tool == 'point':
            self.add_point(scene_pos.x(), scene_pos.y())
        elif self.current_tool == 'segment':
            if len(self.drawing_points) == 0:
                self.drawing_points.append((scene_pos.x(), scene_pos.y()))
            else:
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
                radius = (dx**2 + dy**2)**0.5
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
    
    def add_point(self, x, y):
        point_item = QGraphicsEllipseItem(x - 5, y - 5, 10, 10)
        point_item.setBrush(QBrush(QColor('#004ac6')))
        point_item.setPen(QPen(QColor('#004ac6'), 1))
        point_item.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        point_item.setZValue(10)
        
        self.scene_obj.addItem(point_item)
        self.point_items[point_item] = {'x': x, 'y': y}
        
        self.point_added.emit(x, y)
    
    def add_segment(self):
        if len(self.drawing_points) != 2:
            return
        
        p1, p2 = self.drawing_points
        segment_item = QGraphicsLineItem(p1[0], p1[1], p2[0], p2[1])
        segment_item.setPen(QPen(QColor('#4b41e1'), 2))
        segment_item.setFlags(QGraphicsItem.ItemIsSelectable)
        
        self.scene_obj.addItem(segment_item)
        self.segment_items[segment_item] = {'p1': p1, 'p2': p2}
    
    def add_circle(self, center, radius):
        cx, cy = center
        circle_item = QGraphicsEllipseItem(
            cx - radius, cy - radius,
            radius * 2, radius * 2
        )
        circle_item.setPen(QPen(QColor('#006058'), 2))
        circle_item.setBrush(QBrush(Qt.NoBrush))
        circle_item.setFlags(QGraphicsItem.ItemIsSelectable)
        
        self.scene_obj.addItem(circle_item)
        self.circle_items[circle_item] = {'cx': cx, 'cy': cy, 'r': radius}
    
    def add_polygon(self):
        if len(self.drawing_points) < 3:
            return
        
        polygon_item = QGraphicsPolygonItem()
        polygon = QPolygonF()
        for point in self.drawing_points:
            polygon.append(QPointF(point[0], point[1]))
        polygon_item.setPolygon(polygon)
        polygon_item.setPen(QPen(QColor('#9333ea'), 2))
        polygon_item.setBrush(QBrush(QColor('#9333ea'), Qt.Dense4Pattern))
        polygon_item.setFlags(QGraphicsItem.ItemIsSelectable)
        
        self.scene_obj.addItem(polygon_item)
        self.polygon_items[polygon_item] = {'points': self.drawing_points.copy()}
        self.drawing_points.clear()
        
        if hasattr(self, 'polygon_added'):
            self.polygon_added.emit(self.drawing_points)
    
    def update_segment_preview(self, scene_pos):
        if len(self.drawing_points) != 1:
            return
        
        p1 = self.drawing_points[0]
        if hasattr(self, 'preview_item') and self.preview_item:
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
        radius = (dx**2 + dy**2)**0.5
        
        if hasattr(self, 'preview_item') and self.preview_item:
            self.scene_obj.removeItem(self.preview_item)
        
        self.preview_item = QGraphicsEllipseItem(cx - radius, cy - radius, radius * 2, radius * 2)
        self.preview_item.setPen(QPen(QColor('#006058'), 2, Qt.DashLine))
        self.preview_item.setBrush(QBrush(Qt.NoBrush))
        self.scene_obj.addItem(self.preview_item)
    
    def update_polygon_preview(self, scene_pos=None):
        if len(self.drawing_points) < 1:
            return
        
        if hasattr(self, 'preview_item') and self.preview_item:
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
    
    def clear_canvas(self):
        self.scene_obj.clear()
        self.init_grid()
        self.point_items.clear()
        self.segment_items.clear()
        self.circle_items.clear()
        self.polygon_items.clear()
        self.drawing_points.clear()
        self.preview_item = None
    
    def draw_object(self, obj_id, obj_data):
        obj_type = obj_data.get('type')
        
        if obj_type == 'Point':
            x = obj_data['coordinates'].get('x', 0)
            y = obj_data['coordinates'].get('y', 0)
            name = obj_data.get('name', '')
            
            point_item = QGraphicsEllipseItem(x - 5, y - 5, 10, 10)
            point_item.setBrush(QBrush(QColor('#004ac6')))
            point_item.setPen(QPen(QColor('#004ac6'), 1))
            point_item.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
            point_item.setZValue(10)
            
            text_item = QGraphicsTextItem(name)
            text_item.setPos(x + 8, y - 12)
            text_item.setFont(QFont('Arial', 12, QFont.Bold))
            text_item.setDefaultTextColor(QColor('#0b1c30'))
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
            r = obj_data['coordinates'].get('r', 1)
            
            circle_item = QGraphicsEllipseItem(cx - r, cy - r, r * 2, r * 2)
            circle_item.setPen(QPen(QColor('#006058'), 2))
            circle_item.setBrush(QBrush(Qt.NoBrush))
            circle_item.setFlags(QGraphicsItem.ItemIsSelectable)
            
            self.scene_obj.addItem(circle_item)
            self.object_map[obj_id] = {'circle': circle_item}
        
        elif obj_type == 'Polygon':
            points = obj_data.get('points', [])
            name = obj_data.get('name', '')
            
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
    
    def update_object(self, obj_id, obj_data):
        if obj_id not in self.object_map:
            self.draw_object(obj_id, obj_data)
            return
        
        obj_type = obj_data.get('type')
        obj_info = self.object_map[obj_id]
        
        if obj_type == 'Point':
            x = obj_data['coordinates'].get('x', 0)
            y = obj_data['coordinates'].get('y', 0)
            
            point_item = obj_info['point']
            point_item.setRect(x - 5, y - 5, 10, 10)
            
            text_item = obj_info['text']
            text_item.setPos(x + 8, y - 12)
        
        elif obj_type == 'Segment':
            x1 = obj_data['coordinates'].get('x1', 0)
            y1 = obj_data['coordinates'].get('y1', 0)
            x2 = obj_data['coordinates'].get('x2', 0)
            y2 = obj_data['coordinates'].get('y2', 0)
            
            segment_item = obj_info['segment']
            segment_item.setLine(x1, y1, x2, y2)
        
        elif obj_type == 'Circle':
            cx = obj_data['coordinates'].get('cx', 0)
            cy = obj_data['coordinates'].get('cy', 0)
            r = obj_data['coordinates'].get('r', 1)
            
            circle_item = obj_info['circle']
            circle_item.setRect(cx - r, cy - r, r * 2, r * 2)
    
    def remove_object(self, obj_id):
        if obj_id in self.object_map:
            obj_info = self.object_map[obj_id]
            for item in obj_info.values():
                self.scene_obj.removeItem(item)
            del self.object_map[obj_id]
    
    def select_object(self, obj_id):
        if obj_id in self.object_map:
            obj_info = self.object_map[obj_id]
            for item in obj_info.values():
                item.setSelected(True)
    
    def focus_on_object(self, obj_id):
        if obj_id in self.object_map:
            obj_info = self.object_map[obj_id]
            first_item = list(obj_info.values())[0]
            self.centerOn(first_item.pos())
