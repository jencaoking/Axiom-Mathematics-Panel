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
        if hasattr(self.engine, "add_listener"):
            self.engine.add_listener(self._on_scene_changed)

        self.current_state_json = "{}"

    def _on_scene_changed(self, event_type, data):
        """任何元素的移动、添加、删除都会触发这里"""
        # 重置定时器，只要用户还在疯狂拖拽，就不会触发捕获
        self._debounce_timer.start()

    def _capture_semantic_state(self):
        """核心：将画面翻译为语义 JSON"""
        state = {"points": {}, "lines": [], "circles": [], "polygons": []}

        objects = []
        if hasattr(self.engine, "get_all_objects"):
            objects = self.engine.get_all_objects()
        elif hasattr(self.engine, "objects"):
            objects = list(self.engine.objects.values())

        for obj in objects:
            item_type = obj.type
            name = obj.name

            if item_type == "Point":
                # 保留 2 位小数足矣，防止 JSON 过大
                x = obj.coordinates.get("x", 0)
                y = obj.coordinates.get("y", 0)
                state["points"][name] = {"x": round(x, 2), "y": round(y, 2)}

            elif item_type in ["Segment", "Line"]:
                length = 0.0
                if item_type == "Segment":
                    x1 = obj.coordinates.get("x1", 0)
                    y1 = obj.coordinates.get("y1", 0)
                    x2 = obj.coordinates.get("x2", 0)
                    y2 = obj.coordinates.get("y2", 0)
                    length = math.hypot(x2 - x1, y2 - y1)

                state["lines"].append(
                    {
                        "name": name,
                        "type": item_type,
                        # 本地算好长度直接给 AI，省 Token
                        "length": round(length, 2) if length else None,
                    }
                )

            elif item_type == "Circle":
                r = obj.coordinates.get("r", 0)
                state["circles"].append({"name": name, "radius": round(r, 2)})

            elif item_type == "Polygon":
                state["polygons"].append({"name": name})

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
        points = state.get("points", {})

        # 将点字典转为 (name, x, y) 列表
        pt_list = [(name, data["x"], data["y"]) for name, data in points.items()]
        if len(pt_list) < 2:
            return insights

        # ── 1. 检测三点共线 ──
        if len(pt_list) >= 3:
            from itertools import combinations

            for a, b, c in combinations(pt_list, 3):
                # 用叉积判定共线：|x_ab * y_ac - y_ab * x_ac| < epsilon
                x_ab = b[1] - a[1]
                y_ab = b[2] - a[2]
                x_ac = c[1] - a[1]
                y_ac = c[2] - a[2]
                cross = abs(x_ab * y_ac - y_ab * x_ac)
                if cross < 0.01:
                    insights.append(f"Points {a[0]}, {b[0]}, {c[0]} are collinear")

        # ── 2. 检测两条线段垂直 ──
        lines = state.get("lines", [])
        if len(lines) >= 2:
            from itertools import combinations as comb2

            # 从 lines 中提取每条线段的坐标信息（需要从 state 中补全端点坐标）
            # 由于 lines 列表只有 name/type/length，需要回到 points 中查找
            # 简化方案：检测点对之间的向量是否垂直
            if len(pt_list) >= 4:
                for a, b, c, d in comb2(pt_list, 4):
                    # 向量 AB · CD = 0 → 垂直
                    v1x, v1y = b[1] - a[1], b[2] - a[2]
                    v2x, v2y = d[1] - c[1], d[2] - c[2]
                    dot = v1x * v2x + v1y * v2y
                    len1 = math.hypot(v1x, v1y)
                    len2 = math.hypot(v2x, v2y)
                    if len1 > 0.01 and len2 > 0.01 and abs(dot) < 0.01:
                        insights.append(
                            f"Segment {a[0]}{b[0]} is perpendicular to {c[0]}{d[0]}"
                        )

        # ── 3. 检测等边三角形 ──
        if len(pt_list) >= 3:
            from itertools import combinations

            for a, b, c in combinations(pt_list, 3):
                d_ab = math.hypot(b[1] - a[1], b[2] - a[2])
                d_bc = math.hypot(c[1] - b[1], c[2] - b[2])
                d_ca = math.hypot(a[1] - c[1], a[2] - c[2])
                if d_ab > 0.01 and abs(d_ab - d_bc) < 0.05 and abs(d_bc - d_ca) < 0.05:
                    insights.append(
                        f"Points {a[0]}, {b[0]}, {c[0]} form an equilateral triangle"
                    )

        # ── 4. 检测直角三角形（勾股定理） ──
        if len(pt_list) >= 3:
            from itertools import combinations

            for a, b, c in combinations(pt_list, 3):
                d_ab = math.hypot(b[1] - a[1], b[2] - a[2])
                d_bc = math.hypot(c[1] - b[1], c[2] - b[2])
                d_ca = math.hypot(a[1] - c[1], a[2] - c[2])
                # 排序三条边
                sides = sorted([d_ab, d_bc, d_ca])
                if sides[0] > 0.01:
                    # 检查 a² + b² ≈ c²
                    if abs(sides[0] ** 2 + sides[1] ** 2 - sides[2] ** 2) < 0.1:
                        insights.append(
                            f"Points {a[0]}, {b[0]}, {c[0]} form a right triangle"
                        )

        # ── 5. 检测等距点对 ──
        if len(pt_list) >= 2:
            from itertools import combinations

            for a, b in combinations(pt_list, 2):
                dist = math.hypot(b[1] - a[1], b[2] - a[2])
                # 检查是否有其他点对距离相同
                for c, d in combinations(pt_list, 2):
                    if (a, b) == (c, d) or (a, b) == (d, c):
                        continue
                    dist2 = math.hypot(d[1] - c[1], d[2] - c[2])
                    if abs(dist - dist2) < 0.05:
                        insights.append(f"Distance {a[0]}-{b[0]} equals {c[0]}-{d[0]}")
                        break  # 每个点对只报告一次

        return insights
