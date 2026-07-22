from mathlab.core.models.base import GeometricObject


class Circle(GeometricObject):
    def __init__(self, obj_id, name, center_id, radius=1.0):
        super().__init__(obj_id, name, "Circle")
        self.center_id = center_id
        self.radius = radius
        self.depends_on = [center_id]

    def update_coordinates(self, engine):
        center = engine.objects.get(self.center_id)
        if center:
            self.coordinates = {
                "cx": center.coordinates["x"],
                "cy": center.coordinates["y"],
                "r": self.radius,
            }

    def to_latex(self):
        return rf"Circle({self.name})"

    def serialize(self):
        data = super().serialize()
        data["center_id"] = self.center_id
        data["radius"] = self.radius
        return data
