import uuid
import numpy as np
from collections import defaultdict
from sympy import symbols, Eq, parse_expr, sqrt, sin, cos, tan, pi, exp, log, Abs
from sympy.parsing.sympy_parser import standard_transformations

from PySide6.QtCore import QObject, Signal

# 重新导出所有几何模型类（已拆分到 mathlab.core.models 子包），保持向后兼容
# 现有的 `from mathlab.core.geometry_engine import XXX` 无需修改
from mathlab.core.models import (
    DAG,
    GeometricObject,
    Point,
    Sphere,
    Locus,
    Intersection,
    Line,
    Segment,
    FunctionPlot,
    ImplicitPlot,
    PolarPlot,
    Ellipse,
    Hyperbola,
    Parabola,
    ConicSection,
    Circle,
    Polygon,
)

# 星号导入用于向后兼容（外部代码可能使用 `from geometry_engine import *`）
from mathlab.core.models import *  # noqa: F401, F403

# 扩大异常捕获范围，防止 RuntimeError 等非 ImportError 导致整个模块崩溃
try:
    from mathlab.core.cs_geometry_engine import cs_geometry
except Exception as e:
    print(
        f"Warning: C# geometry engine fallback triggered in geometry_engine.py. Error: {e}"
    )
    cs_geometry = None


class GeometryEngine(QObject):
    # ── Qt 信号定义（替代手写 listener 列表） ───────────────────────────
    object_added = Signal(dict)
    object_updated = Signal(dict)
    object_removed = Signal(object)  # obj_id (str) 或包含 id 的 dict
    geometry_event = Signal(str, object)  # 通用事件：(event_type, data)

    def __init__(self):
        super().__init__()
        self.objects = {}
        self.name_counter = defaultdict(int)
        self._name_set = set()
        self.dependencies = DAG()
        self._listeners = []  # 向后兼容：旧的回调式监听器
        self._signals_blocked = False
        self.cas_provider = None
        self.is_draft_mode = False
        self.draft_ids = []

    def validate_commands(self, commands: list):
        """
        带严格逻辑校验的执行器预检。
        如果存在非法引用或逻辑冲突，立即中断并抛出明确的语义错误 ValueError。
        """
        simulated_names = set(
            obj.name for obj in self.objects.values() if hasattr(obj, "name")
        )

        for cmd in commands:
            op = cmd.get("cmd")

            if op == "add_point":
                name = cmd.get("name")
                if name:
                    simulated_names.add(name)

            elif op == "add_segment":
                p1, p2 = cmd.get("p1"), cmd.get("p2")
                if p1 not in simulated_names:
                    raise ValueError(
                        f"无法画线：画板上根本不存在名为 '{p1}' 的点。请先添加该点，或检查名称拼写。"
                    )
                if p2 not in simulated_names:
                    raise ValueError(f"无法画线：画板上根本不存在名为 '{p2}' 的点。")
                if p1 == p2:
                    raise ValueError(
                        f"无法画线：起点 '{p1}' 和终点 '{p2}' 是同一个点。"
                    )

            elif op == "add_circle":
                center = cmd.get("center")
                radius = cmd.get("radius", 0)
                if center not in simulated_names:
                    raise ValueError(f"无法画圆：找不到指定的圆心点 '{center}'。")
                if radius <= 0:
                    raise ValueError(
                        f"无法画圆：半径必须大于 0，当前给定半径为 {radius}。"
                    )

            elif op not in ["add_point", "add_segment", "add_circle", "add_polygon"]:
                raise ValueError(
                    f"引擎不支持的操作指令：'{op}'，请严格使用工具说明书里的枚举值。"
                )

    def begin_draft(self):
        self.is_draft_mode = True
        self.draft_ids = []

    def commit_draft(self):
        self.is_draft_mode = False
        for obj_id in self.draft_ids:
            obj = self.objects.get(obj_id)
            if obj:
                obj.is_draft = False
                self._notify("object_updated", obj.serialize())
        self.draft_ids.clear()

    def discard_draft(self):
        self.is_draft_mode = False
        # Remove in reverse dependency order
        for obj_id in reversed(self.draft_ids):
            if obj_id in self.objects:
                self.remove_object(obj_id)
        self.draft_ids.clear()

    def set_cas_provider(self, cas_provider):
        self.cas_provider = cas_provider

    def block_signals(self, blocked):
        self._signals_blocked = blocked

    def signals_blocked(self):
        return self._signals_blocked

    def _generate_id(self):
        return str(uuid.uuid4())

    def _generate_name(self, obj_type):
        prefix = obj_type[0].upper()
        self.name_counter[obj_type] += 1
        name = f"{prefix}{self.name_counter[obj_type]}"
        while name in self._name_set:
            self.name_counter[obj_type] += 1
            name = f"{prefix}{self.name_counter[obj_type]}"
        self._name_set.add(name)
        return name

    def add_listener(self, listener):
        """注册事件监听器（向后兼容接口）。

        新代码应直接连接 Qt 信号：
            engine.object_added.connect(callback)
            engine.object_updated.connect(callback)
            engine.object_removed.connect(callback)
        旧式回调签名 listener(event_type: str, data: dict) 仍然支持。
        """
        self._listeners.append(listener)

    def remove_listener(self, listener):
        """移除事件监听器。"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify(self, event_type, data):
        """发射 Qt 信号并通知旧式监听器。"""
        if self._signals_blocked:
            return

        if event_type == "object_added" and getattr(self, "is_draft_mode", False):
            obj_id = data.get("id")
            if obj_id:
                obj = self.objects.get(obj_id)
                if obj:
                    obj.is_draft = True
                    data["is_draft"] = True
                    if obj_id not in self.draft_ids:
                        self.draft_ids.append(obj_id)

        # 发射 Qt 信号（新接口）
        if event_type == "object_added":
            self.object_added.emit(data)
        elif event_type == "object_updated":
            self.object_updated.emit(data)
        elif event_type == "object_removed":
            self.object_removed.emit(data)

        # 通用事件信号
        self.geometry_event.emit(event_type, data)

        # 通知旧式回调监听器（向后兼容）
        for listener in self._listeners:
            listener(event_type, data)

    def add_point(self, x=0, y=0, z=0, name=None):
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("Point")
        point = Point(obj_id, name, x, y, z)  # 传入 z
        self.objects[obj_id] = point
        self._notify("object_added", point.serialize())
        return obj_id

    def add_sphere(self, center_id, radius=1.0, name=None):
        if center_id not in self.objects:
            raise ValueError("Center point not found")
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("Sphere")
        sphere = Sphere(obj_id, name, center_id, radius)
        self.objects[obj_id] = sphere
        self.dependencies.add_edge(center_id, obj_id)
        sphere.update_coordinates(self)
        self._notify("object_added", sphere.serialize())
        return obj_id

    def add_segment(self, point1_id, point2_id, name=None):
        if point1_id not in self.objects or point2_id not in self.objects:
            raise ValueError("Points not found")

        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("Segment")
        segment = Segment(obj_id, name, point1_id, point2_id)
        self.objects[obj_id] = segment
        self.dependencies.add_edge(point1_id, obj_id)
        self.dependencies.add_edge(point2_id, obj_id)
        segment.update_coordinates(self)
        self._notify("object_added", segment.serialize())
        return obj_id

    def add_line(self, point1_id, point2_id, name=None):
        if point1_id not in self.objects or point2_id not in self.objects:
            raise ValueError("Points not found")

        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("Line")
        line = Line(obj_id, name, point1_id, point2_id)
        self.objects[obj_id] = line
        self.dependencies.add_edge(point1_id, obj_id)
        self.dependencies.add_edge(point2_id, obj_id)
        line.update_coordinates(self)
        self._notify("object_added", line.serialize())
        return obj_id

    def add_intersection(self, obj1_id, obj2_id, index=0, name=None):
        if obj1_id not in self.objects or obj2_id not in self.objects:
            raise ValueError("Objects not found")

        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("Intersection")
        intersection = Intersection(obj_id, name, obj1_id, obj2_id, index)
        self.objects[obj_id] = intersection
        self.dependencies.add_edge(obj1_id, obj_id)
        self.dependencies.add_edge(obj2_id, obj_id)
        intersection.update_coordinates(self)
        self._notify("object_added", intersection.serialize())
        return obj_id

    def add_circle(self, center_id, radius=1.0, name=None):
        if center_id not in self.objects:
            raise ValueError("Center point not found")

        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("Circle")
        circle = Circle(obj_id, name, center_id, radius)
        self.objects[obj_id] = circle
        self.dependencies.add_edge(center_id, obj_id)
        circle.update_coordinates(self)
        self._notify("object_added", circle.serialize())
        return obj_id

    def add_polygon(self, point_ids, name=None):
        for point_id in point_ids:
            if point_id not in self.objects:
                raise ValueError(f"Point {point_id} not found")

        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("Polygon")
        polygon = Polygon(obj_id, name, point_ids)
        self.objects[obj_id] = polygon
        for point_id in point_ids:
            self.dependencies.add_edge(point_id, obj_id)
        polygon.update_coordinates(self)
        self._notify("object_added", polygon.serialize())
        return obj_id

    def add_ellipse(self, center_id, a=2.0, b=1.0, rotation=0, name=None):
        """添加椭圆"""
        if center_id not in self.objects:
            raise ValueError("Center point not found")

        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("Ellipse")
        ellipse = Ellipse(obj_id, name, center_id, a, b, rotation)
        self.objects[obj_id] = ellipse
        self.dependencies.add_edge(center_id, obj_id)
        ellipse.update_coordinates(self)
        self._notify("object_added", ellipse.serialize())
        return obj_id

    def add_hyperbola(self, center_id, a=1.0, b=1.0, rotation=0, name=None):
        """添加双曲线"""
        if center_id not in self.objects:
            raise ValueError("Center point not found")

        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("Hyperbola")
        hyperbola = Hyperbola(obj_id, name, center_id, a, b, rotation)
        self.objects[obj_id] = hyperbola
        self.dependencies.add_edge(center_id, obj_id)
        hyperbola.update_coordinates(self)
        self._notify("object_added", hyperbola.serialize())
        return obj_id

    def add_parabola(self, vertex_id, p=1.0, direction="up", name=None):
        """添加抛物线"""
        if vertex_id not in self.objects:
            raise ValueError("Vertex point not found")

        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("Parabola")
        parabola = Parabola(obj_id, name, vertex_id, p, direction)
        self.objects[obj_id] = parabola
        self.dependencies.add_edge(vertex_id, obj_id)
        parabola.update_coordinates(self)
        self._notify("object_added", parabola.serialize())
        return obj_id

    def add_conic_section(
        self,
        A=1,
        B=0,
        C=1,
        D=0,
        E=0,
        F=-1,
        x_range=(-10, 10),
        y_range=(-10, 10),
        name=None,
    ):
        """添加一般圆锥曲线"""
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("ConicSection")
        conic = ConicSection(obj_id, name, A, B, C, D, E, F, x_range, y_range)
        conic.generate_points()  # 生成离散点
        self.objects[obj_id] = conic
        self._notify("object_added", conic.serialize())
        return obj_id

    def add_function_plot(
        self, expression, x_range=(-10, 10), num_points=500, name=None
    ):
        """添加显函数绘图 y=f(x)"""
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("FunctionPlot")
        func_plot = FunctionPlot(obj_id, name, expression, x_range, num_points)
        self.objects[obj_id] = func_plot
        self._notify("object_added", func_plot.serialize())
        return obj_id

    def add_implicit_plot(
        self,
        expression,
        x_range=(-10, 10),
        y_range=(-10, 10),
        resolution=400,
        name=None,
    ):
        """添加隐函数绘图 f(x,y)=0"""
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("ImplicitPlot")
        impl_plot = ImplicitPlot(obj_id, name, expression, x_range, y_range, resolution)
        self.objects[obj_id] = impl_plot
        self._notify("object_added", impl_plot.serialize())
        return obj_id

    def add_polar_plot(
        self, expression, theta_range=(0, 2 * np.pi), num_points=500, name=None
    ):
        """添加极坐标绘图 r=f(θ)"""
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("PolarPlot")
        polar_plot = PolarPlot(obj_id, name, expression, theta_range, num_points)
        self.objects[obj_id] = polar_plot
        self._notify("object_added", polar_plot.serialize())
        return obj_id

    def add_locus(self, tracer_point_id, driver_point_id, max_points=1000, name=None):
        """添加动点轨迹追踪器"""
        if tracer_point_id not in self.objects or driver_point_id not in self.objects:
            raise ValueError("Tracer or driver point not found")

        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name("Locus")
        locus = Locus(obj_id, name, tracer_point_id, driver_point_id, max_points)
        self.objects[obj_id] = locus
        self.dependencies.add_edge(tracer_point_id, obj_id)
        self.dependencies.add_edge(driver_point_id, obj_id)
        self._notify("object_added", locus.serialize())
        return obj_id

    def update_locus(self, locus_id):
        """更新轨迹：添加当前追踪点位置"""
        if locus_id not in self.objects:
            return

        locus = self.objects[locus_id]
        if locus.type != "Locus":
            return

        tracer = self.objects.get(locus.tracer_point_id)
        if tracer:
            locus.add_trail_point(tracer.coordinates["x"], tracer.coordinates["y"])
            self._notify("object_updated", locus.serialize())

    def remove_object(self, obj_id):
        if obj_id not in self.objects:
            return

        # get_dependents 返回拓扑序（父→子），reversed 后保证叶子先删。
        all_dependents = self.dependencies.get_dependents(obj_id)
        for dep_id in reversed(all_dependents):
            if dep_id in self.objects:
                dep_obj = self.objects[dep_id]
                self._name_set.discard(dep_obj.name)
                # 同步递减计数器，保持名称状态一致
                if hasattr(dep_obj, "type") and dep_obj.type in self.name_counter:
                    self.name_counter[dep_obj.type] = max(
                        0, self.name_counter[dep_obj.type] - 1
                    )
                self.dependencies.remove_node(dep_id)
                self._notify("object_removed", dep_id)
                del self.objects[dep_id]

        obj = self.objects[obj_id]
        self._name_set.discard(obj.name)
        # 同步递减计数器
        if hasattr(obj, "type") and obj.type in self.name_counter:
            self.name_counter[obj.type] = max(0, self.name_counter[obj.type] - 1)
        self.dependencies.remove_node(obj_id)
        self._notify("object_removed", obj_id)
        del self.objects[obj_id]

    def update_point(self, obj_id, x=None, y=None, z=None):
        if obj_id not in self.objects:
            return

        point = self.objects[obj_id]
        if x is not None:
            point.coordinates["x"] = x
        if y is not None:
            point.coordinates["y"] = y
        if z is not None:
            point.coordinates["z"] = z

        dependents = self.dependencies.get_dependents(obj_id)
        for dep_id in dependents:
            dep_obj = self.objects.get(dep_id)  # 安全获取，避免已删除对象 KeyError
            if dep_obj is None:
                continue
            dep_obj.update_coordinates(self)
            self._notify("object_updated", dep_obj.serialize())

        self._notify("object_updated", point.serialize())

    def get_object(self, obj_id):
        return self.objects.get(obj_id)

    def get_all_objects(self):
        return list(self.objects.values())

    def get_objects_by_type(self, obj_type):
        return [obj for obj in self.objects.values() if obj.type == obj_type]

    def solve_constraints(self):
        from scipy.optimize import least_squares
        import numpy as np

        variables = []
        var_to_idx = {}
        equations = []

        points = list(self.get_objects_by_type("Point"))

        for point in points:
            safe_id = point.id.replace("-", "_")
            x_sym = symbols(f"x_{safe_id}")
            y_sym = symbols(f"y_{safe_id}")
            z_sym = symbols(f"z_{safe_id}")  # 1. 注册 z_sym

            var_to_idx[(point.id, "x")] = len(variables)
            var_to_idx[(point.id, "y")] = len(variables) + 1
            var_to_idx[(point.id, "z")] = len(variables) + 2  # 2. 索引映射
            variables.extend([x_sym, y_sym, z_sym])

        for obj in self.objects.values():
            for constraint in obj.constraints:
                if isinstance(constraint, str):
                    try:
                        allowed_symbols = {
                            "Eq": Eq,
                            "sqrt": sqrt,
                            "sin": sin,
                            "cos": cos,
                            "tan": tan,
                            "pi": pi,
                            "exp": exp,
                            "log": log,
                            "Abs": Abs,
                            "pow": pow,
                        }
                        for point in points:
                            safe_id = point.id.replace("-", "_")
                            allowed_symbols[f"x_{safe_id}"] = symbols(f"x_{safe_id}")
                            allowed_symbols[f"y_{safe_id}"] = symbols(f"y_{safe_id}")
                            allowed_symbols[f"z_{safe_id}"] = symbols(
                                f"z_{safe_id}"
                            )  # 3. 允许用户输入含 z 的约束方程
                        eq = parse_expr(
                            constraint,
                            local_dict=allowed_symbols,
                            transformations=standard_transformations,
                        )
                        equations.append(eq)
                    except Exception:
                        pass
                else:
                    equations.append(constraint)

        if not equations or not variables:
            return None

        def objective(x):
            """返回残差向量。least_squares 允许方程数与变量数不等，
            即使系统欠约束（方程 < 变量）或过约束（方程 > 变量），
            也能返回最小二乘意义上的最优解，而 fsolve 在这种情况下
            会直接抛出 shape mismatch 异常导致崩溃。"""
            result = []
            var_dict = {}
            for i, var in enumerate(variables):
                var_dict[var] = x[i]

            for eq in equations:
                try:
                    eq_expr = eq.lhs - eq.rhs if isinstance(eq, Eq) else eq
                    val = float(eq_expr.subs(var_dict).evalf())
                    result.append(val)
                except Exception as e:
                    # 求值失败时残差记为 0，避免优化器被异常打断
                    import logging

                    logging.getLogger(__name__).warning(
                        f"Constraint evaluation failed: {e}"
                    )
                    result.append(0.0)

            return np.array(result, dtype=float)

        initial_guess = []
        for point in points:
            initial_guess.append(point.coordinates.get("x", 0.0))
            initial_guess.append(point.coordinates.get("y", 0.0))
            initial_guess.append(point.coordinates.get("z", 0.0))  # 4. 初始猜测值

        try:
            # 自动选择 least_squares 算法：
            # - 'lm' (Levenberg-Marquardt)：要求方程数 ≥ 变量数，适合过约束/适定
            # - 'trf' (Trust Region Reflective)：兼容欠约束（方程数 < 变量数）
            n_eq = len(equations)
            n_var = len(variables)
            method = "lm" if n_eq >= n_var else "trf"
            result_obj = least_squares(
                objective, np.array(initial_guess), method=method
            )
            # least_squares 返回的 OptimizeResult 没有 .success 字段，
            # 使用 .status 判断：< 0 表示失败
            if result_obj.status < 0:
                return {
                    "success": False,
                    "error": f"Solver failed (status={result_obj.status})",
                }

            result = result_obj.x

            for point in points:
                x_idx = var_to_idx.get((point.id, "x"))
                y_idx = var_to_idx.get((point.id, "y"))
                z_idx = var_to_idx.get((point.id, "z"))
                if x_idx is not None and y_idx is not None and z_idx is not None:
                    # 5. 更新点坐标
                    try:
                        x_val = float(result[x_idx])
                        y_val = float(result[y_idx])
                        z_val = float(result[z_idx])
                        self.update_point(point.id, x=x_val, y=y_val, z=z_val)
                    except Exception:
                        pass

            return {"success": True, "solution": result.tolist()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_constraint(self, obj_id, constraint):
        if obj_id not in self.objects:
            return {"success": False, "error": "Object not found"}

        obj = self.objects[obj_id]
        obj.constraints.append(constraint)
        return {"success": True}

    def remove_constraint(self, obj_id, constraint):
        if obj_id not in self.objects:
            return {"success": False, "error": "Object not found"}

        obj = self.objects[obj_id]
        if constraint in obj.constraints:
            obj.constraints.remove(constraint)
            return {"success": True}
        return {"success": False, "error": "Constraint not found"}

    def serialize_all(self):
        return {
            "objects": {
                obj_id: obj.serialize() for obj_id, obj in self.objects.items()
            },
            "name_counter": dict(self.name_counter),
        }

    def deserialize_all(self, data):
        self.objects.clear()
        self._name_set.clear()
        self.name_counter = defaultdict(int, data.get("name_counter", {}))
        self.dependencies = DAG()

        for obj_id, obj_data in data.get("objects", {}).items():
            obj = GeometricObject.deserialize(obj_data)
            self.objects[obj_id] = obj
            self._name_set.add(obj.name)
            for dep in obj.depends_on:
                self.dependencies.add_edge(dep, obj_id)

        for obj in self.objects.values():
            if hasattr(obj, "update_coordinates"):
                # 所有依赖其他节点（点）的几何对象都需要刷新坐标，
                # 否则反序列化时这些对象会停留在初始默认值。
                if type(obj).__name__ in (
                    "Segment",
                    "Circle",
                    "Polygon",
                    "Ellipse",
                    "Hyperbola",
                    "Parabola",
                    "Locus",
                    "Line",
                    "Ray",
                    "Intersection",
                    "Sphere",
                ):
                    obj.update_coordinates(self)
            self._notify("object_added", obj.serialize())

    def clear(self):
        self.objects.clear()
        self._name_set.clear()
        self.name_counter.clear()
        self.dependencies = DAG()
        self._notify("canvas_cleared", None)
