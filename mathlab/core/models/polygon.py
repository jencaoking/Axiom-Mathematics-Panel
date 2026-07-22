from mathlab.core.models.base import GeometricObject


class Polygon(GeometricObject):
    def __init__(self, obj_id, name, point_ids):
        super().__init__(obj_id, name, "Polygon")
        self.point_ids = point_ids
        self.depends_on = point_ids.copy()
        self.points = []

    def update_coordinates(self, engine):
        self.points = []
        for point_id in self.point_ids:
            point = engine.objects.get(point_id)
            if point:
                self.points.append((point.coordinates["x"], point.coordinates["y"]))
        self.coordinates = {"points": self.points}

    def to_latex(self):
        return rf"Polygon({self.name})"

    def serialize(self):
        data = super().serialize()
        data["point_ids"] = self.point_ids
        data["points"] = self.points
        return data

    @classmethod
    def deserialize(cls, data):
        obj = cls(data["id"], data["name"], data.get("point_ids", []))
        obj.coordinates = data["coordinates"]
        obj.constraints = data.get("constraints", [])
        obj.depends_on = data.get("depends_on", [])
        obj.points = data.get("points", [])
        return obj
