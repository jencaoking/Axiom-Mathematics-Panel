import json
import math
from PySide6.QtCore import QObject, Signal, QTimer
from mathlab.utils.logger import get_logger

logger = get_logger(__name__)


class CanvasShadowTracker(QObject):
    """
    画板状态追踪器：将 Qt 视觉对象翻译为 AI 能看懂的语义 JSON
    """
    # 当画板状态发生实质性改变并稳定后，抛出此信号
    state_stabilized = Signal(str)

    def __init__(self, engine, debounce_ms=800):
        super().__init__()
        self.engine = engine

        # 防抖定时器：用户拖拽结束 800ms 后才触发状态捕获
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(debounce_ms)
        self._debounce_timer.timeout.connect(self._capture_semantic_state)

        # 监听几何引擎内部的状态变动
        if hasattr(self.engine, 'add_listener'):
            self.engine.add_listener(self._on_scene_changed)

        self.current_state_json = "{}"

    def _on_scene_changed(self, event_type, data):
        """任何元素的移动、添加、删除都会触发这里"""
        # 重置定时器，只要用户还在疯狂拖拽，就不会触发捕获
        self._debounce_timer.start()

    def _capture_semantic_state(self):
        """核心：将画面翻译为语义 JSON"""
        state = {
            "points": {},
            "lines": [],
            "circles": [],
            "polygons": []
        }

        objects = []
        if hasattr(self.engine, 'get_all_objects'):
            objects = self.engine.get_all_objects()
        elif hasattr(self.engine, 'objects'):
            objects = list(self.engine.objects.values())

        for obj in objects:
            item_type = obj.type
            name = obj.name

            if item_type == 'Point':
                # 保留 2 位小数足矣，防止 JSON 过大
                x = obj.coordinates.get('x', 0)
                y = obj.coordinates.get('y', 0)
                state["points"][name] = {"x": round(x, 2), "y": round(y, 2)}

            elif item_type in ['Segment', 'Line']:
                length = 0.0
                if item_type == 'Segment':
                    x1 = obj.coordinates.get('x1', 0)
                    y1 = obj.coordinates.get('y1', 0)
                    x2 = obj.coordinates.get('x2', 0)
                    y2 = obj.coordinates.get('y2', 0)
                    length = math.hypot(x2 - x1, y2 - y1)

                state["lines"].append({
                    "name": name,
                    "type": item_type,
                    # 本地算好长度直接给 AI，省 Token
                    "length": round(length, 2) if length else None
                })

            elif item_type == 'Circle':
                r = obj.coordinates.get('r', 0)
                state["circles"].append({
                    "name": name,
                    "radius": round(r, 2)
                })

            elif item_type == 'Polygon':
                state["polygons"].append({
                    "name": name
                })

        # 【进阶智能】：本地几何预处理！
        # 让 Python 算出所有的内角，塞入 JSON。AI 看到 "angle_ABC: 90.0" 就会瞬间明白这是直角。
        state["local_insights"] = self._calculate_local_insights(state)

        self.current_state_json = json.dumps(state, ensure_ascii=False)
        logger.debug(f"👀 Shadow DOM 更新: {self.current_state_json}")
        self.state_stabilized.emit(self.current_state_json)

    def _calculate_local_insights(self, state):
        """
        本地大脑：提前帮 AI 算出隐含的几何关系
        比如：是否共线、是否有垂直、等边等
        """
        insights = []
        # 此处省略具体的数学计算代码
        # 伪代码：如果检测到三点距离相等 -> insights.append("Point A, B, C form an equilateral
        # triangle")
        return insights
