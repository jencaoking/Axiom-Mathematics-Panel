from mathlab.core.models.base import GeometricObject


class Line(GeometricObject):
    """无限长直线：通过两个点定义，支持符号表达式"""

    def __init__(self, obj_id, name, point1_id, point2_id):
        super().__init__(obj_id, name, "Line")
        self.point1_id = point1_id
        self.point2_id = point2_id
        self.depends_on = [point1_id, point2_id]
        self.a = None  # 直线方程 ax + by + c = 0 的系数
        self.b = None
        self.c = None

    def update_coordinates(self, engine):
        p1 = engine.objects.get(self.point1_id)
        p2 = engine.objects.get(self.point2_id)
        if p1 and p2:
            x1, y1 = p1.coordinates["x"], p1.coordinates["y"]
            x2, y2 = p2.coordinates["x"], p2.coordinates["y"]

            self.a = y2 - y1
            self.b = x1 - x2
            self.c = x2 * y1 - x1 * y2

            self.coordinates = {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "a": self.a,
                "b": self.b,
                "c": self.c,
            }

    def to_latex(self):
        if self.a is None or self.b is None or self.c is None:
            return rf"Line({self.name})"

        parts = []
        if self.a != 0:
            if self.a == 1:
                parts.append("x")
            elif self.a == -1:
                parts.append("-x")
            else:
                parts.append(f"{self.a}x")

        if self.b != 0:
            if self.b == 1:
                sign = "+" if parts else ""
                parts.append(f"{sign}y")
            elif self.b == -1:
                parts.append("-y")
            else:
                sign = "+" if (parts and self.b > 0) else ""
                parts.append(f"{sign}{self.b}y")

        if self.c != 0:
            sign = "+" if (parts and self.c > 0) else ""
            parts.append(f"{sign}{self.c}")

        if not parts:
            return "0 = 0"

        return " ".join(parts) + " = 0"

    def serialize(self):
        data = super().serialize()
        data["point1_id"] = self.point1_id
        data["point2_id"] = self.point2_id
        data["a"] = self.a
        data["b"] = self.b
        data["c"] = self.c
        return data

    @classmethod
    def deserialize(cls, data):
        obj = cls(
            data["id"],
            data["name"],
            data.get("point1_id", ""),
            data.get("point2_id", ""),
        )
        obj.coordinates = data.get("coordinates", {})
        obj.constraints = data.get("constraints", [])
        obj.depends_on = data.get("depends_on", [])
        obj.a = data.get("a")
        obj.b = data.get("b")
        obj.c = data.get("c")
        return obj


class Segment(GeometricObject):
    def __init__(self, obj_id, name, point1_id, point2_id):
        super().__init__(obj_id, name, "Segment")
        self.depends_on = [point1_id, point2_id]
        self.point1_id = point1_id
        self.point2_id = point2_id

    def update_coordinates(self, engine):
        p1 = engine.objects.get(self.point1_id)
        p2 = engine.objects.get(self.point2_id)
        if p1 and p2:
            self.coordinates = {
                "x1": p1.coordinates["x"],
                "y1": p1.coordinates["y"],
                "x2": p2.coordinates["x"],
                "y2": p2.coordinates["y"],
            }

    def to_latex(self):
        return rf"\overline{{{self.name}}}"

    def serialize(self):
        data = super().serialize()
        data["point1_id"] = self.point1_id
        data["point2_id"] = self.point2_id
        return data
