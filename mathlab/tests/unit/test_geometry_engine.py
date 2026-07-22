"""Tests for the GeometryEngine and geometric object primitives.

Covers core geometry construction (points, segments, circles, polygons),
object lifecycle, serialization, conic sections, function plots, and
locus tracking. Merged from the legacy ``test_core.py`` and
``test_analytic_geometry.py`` modules.
"""

import numpy as np
import pytest

from mathlab.core.geometry_engine import (
    Circle,
    GeometricObject,
    GeometryEngine,
    Point,
    Polygon,
    Segment,
)


class TestGeometryEngine:
    """Tests for the GeometryEngine CRUD and serialization API."""

    @pytest.mark.unit
    def test_add_point(self, engine):
        point_id = engine.add_point(3.0, 4.0, name="A")
        assert point_id is not None
        assert point_id in engine.objects

        point = engine.objects[point_id]
        assert point.name == "A"
        assert point.type == "Point"
        assert point.coordinates["x"] == 3.0
        assert point.coordinates["y"] == 4.0

    @pytest.mark.unit
    def test_add_segment(self, engine):
        p1_id = engine.add_point(0.0, 0.0)
        p2_id = engine.add_point(3.0, 4.0)
        seg_id = engine.add_segment(p1_id, p2_id)

        segment = engine.objects[seg_id]
        assert segment.type == "Segment"
        assert segment.point1_id == p1_id
        assert segment.point2_id == p2_id

    @pytest.mark.unit
    def test_add_circle(self, engine):
        center_id = engine.add_point(0.0, 0.0)
        circle_id = engine.add_circle(center_id, radius=5.0)

        circle = engine.objects[circle_id]
        assert circle.type == "Circle"
        assert circle.radius == 5.0

    @pytest.mark.unit
    def test_add_polygon(self, engine):
        p1 = engine.add_point(0.0, 0.0)
        p2 = engine.add_point(1.0, 0.0)
        p3 = engine.add_point(0.5, 1.0)
        poly_id = engine.add_polygon([p1, p2, p3])

        polygon = engine.objects[poly_id]
        assert polygon.type == "Polygon"
        assert len(polygon.point_ids) == 3

    @pytest.mark.unit
    def test_remove_object(self, engine):
        p1_id = engine.add_point(0.0, 0.0)
        p2_id = engine.add_point(1.0, 1.0)
        seg_id = engine.add_segment(p1_id, p2_id)

        engine.remove_object(p1_id)

        assert p1_id not in engine.objects
        assert seg_id not in engine.objects

    @pytest.mark.unit
    def test_update_point(self, engine):
        point_id = engine.add_point(0.0, 0.0)
        engine.update_point(point_id, x=5.0, y=10.0)

        point = engine.objects[point_id]
        assert point.coordinates["x"] == 5.0
        assert point.coordinates["y"] == 10.0

    @pytest.mark.unit
    def test_get_objects_by_type(self, engine):
        engine.add_point(0.0, 0.0)
        engine.add_point(1.0, 1.0)
        center_id = engine.add_point(0.0, 0.0)
        engine.add_circle(center_id, radius=2.0)

        points = engine.get_objects_by_type("Point")
        assert len(points) == 3

    @pytest.mark.unit
    def test_serialize_deserialize(self, engine):
        p1 = engine.add_point(3.0, 4.0, name="A")
        data = engine.serialize_all()

        new_engine = GeometryEngine()
        new_engine.deserialize_all(data)

        assert p1 in new_engine.objects
        assert new_engine.objects[p1].name == "A"


class TestGeometricObject:
    """Tests for direct geometric object construction and serialization."""

    @pytest.mark.unit
    def test_point_creation(self):
        point = Point("p1", "A", 1.0, 2.0)
        assert point.name == "A"
        assert point.coordinates["x"] == 1.0
        assert point.coordinates["y"] == 2.0

    @pytest.mark.unit
    def test_segment_creation(self):
        seg = Segment("s1", "AB", "p1", "p2")
        assert seg.type == "Segment"
        assert seg.point1_id == "p1"
        assert seg.point2_id == "p2"

    @pytest.mark.unit
    def test_circle_creation(self):
        circle = Circle("c1", "C", "p1", 5.0)
        assert circle.type == "Circle"
        assert circle.radius == 5.0

    @pytest.mark.unit
    def test_polygon_creation(self):
        poly = Polygon("poly1", "P", ["p1", "p2", "p3"])
        assert poly.type == "Polygon"
        assert len(poly.point_ids) == 3

    @pytest.mark.unit
    def test_serialize(self):
        point = Point("p1", "A", 1.0, 2.0)
        data = point.serialize()
        assert data["id"] == "p1"
        assert data["name"] == "A"

    @pytest.mark.unit
    def test_deserialize(self):
        data = {
            "id": "p1",
            "name": "A",
            "type": "Point",
            "coordinates": {"x": 1.0, "y": 2.0},
            "constraints": [],
            "depends_on": [],
        }
        point = GeometricObject.deserialize(data)
        assert point.name == "A"
        assert point.coordinates["x"] == 1.0


class TestConicSections:
    """Tests for conic section construction (ellipse, hyperbola, parabola)."""

    @pytest.mark.unit
    def test_ellipse_created(self, engine):
        center_id = engine.add_point(0, 0, name="C1")
        ellipse_id = engine.add_ellipse(center_id, a=3.0, b=2.0)
        ellipse = engine.get_object(ellipse_id)
        assert ellipse is not None
        assert len(ellipse.coordinates.get("points", [])) > 0

    @pytest.mark.unit
    def test_ellipse_latex(self, engine):
        center_id = engine.add_point(0, 0)
        ellipse_id = engine.add_ellipse(center_id, a=3.0, b=2.0)
        ellipse = engine.get_object(ellipse_id)
        latex = ellipse.to_latex()
        assert "frac" in latex or "x" in latex

    @pytest.mark.unit
    def test_hyperbola_created(self, engine):
        center_id = engine.add_point(5, 0, name="C2")
        hyp_id = engine.add_hyperbola(center_id, a=2.0, b=1.5)
        hyp = engine.get_object(hyp_id)
        assert hyp is not None
        assert hyp.type == "Hyperbola"

    @pytest.mark.unit
    def test_parabola_created(self, engine):
        vertex_id = engine.add_point(0, -2, name="V1")
        par_id = engine.add_parabola(vertex_id, p=1.0, direction="up")
        par = engine.get_object(par_id)
        assert par is not None
        assert par.type == "Parabola"

    @pytest.mark.unit
    def test_conic_section_circle(self, engine):
        conic_id = engine.add_conic_section(A=1, B=0, C=1, D=0, E=0, F=-4)
        conic = engine.get_object(conic_id)
        assert conic is not None
        assert len(conic.points_data) > 0


class TestFunctionPlots:
    """Tests for explicit, implicit, and polar function plotting."""

    @pytest.mark.unit
    def test_explicit_function(self, engine):
        func_id = engine.add_function_plot("x**2", x_range=(-5, 5), num_points=200)
        func = engine.get_object(func_id)
        assert func is not None
        assert len(func.points_data) > 0

    @pytest.mark.unit
    def test_sine_function(self, engine):
        func_id = engine.add_function_plot("sin(x)", x_range=(-6.28, 6.28), num_points=300)
        func = engine.get_object(func_id)
        assert func is not None
        assert len(func.points_data) > 0

    @pytest.mark.unit
    def test_implicit_plot(self, engine):
        impl_id = engine.add_implicit_plot("x**2 + y**2 - 1", x_range=(-2, 2), y_range=(-2, 2))
        impl = engine.get_object(impl_id)
        assert impl is not None
        assert len(impl.points_data) > 0

    @pytest.mark.unit
    def test_polar_plot(self, engine):
        polar_id = engine.add_polar_plot("2*cos(theta)", theta_range=(0, 2 * np.pi), num_points=300)
        polar = engine.get_object(polar_id)
        assert polar is not None
        assert len(polar.points_data) > 0


class TestLocus:
    """Tests for locus creation and trail tracking."""

    @pytest.mark.unit
    def test_locus_creation(self, engine):
        driver_id = engine.add_point(0, 0, name="Driver")
        tracer_id = engine.add_point(2, 0, name="Tracer")
        locus_id = engine.add_locus(tracer_id, driver_id, max_points=100)
        locus = engine.get_object(locus_id)
        assert locus is not None
        assert locus.type == "Locus"

    @pytest.mark.unit
    def test_locus_trail(self, engine):
        driver_id = engine.add_point(0, 0, name="Driver")
        tracer_id = engine.add_point(2, 0, name="Tracer")
        locus_id = engine.add_locus(tracer_id, driver_id, max_points=100)

        for i in range(10):
            angle = i * 0.5
            engine.update_point(driver_id, x=3 * np.cos(angle), y=3 * np.sin(angle))
            engine.update_point(tracer_id, x=3 * np.cos(angle) + 1, y=3 * np.sin(angle))
            engine.update_locus(locus_id)

        locus = engine.get_object(locus_id)
        assert len(locus.trail_points) > 0


class TestSerialization:
    """Tests for engine serialize/deserialize round-trips."""

    @pytest.mark.unit
    def test_roundtrip(self, engine):
        center_id = engine.add_point(0, 0, name="Center")
        engine.add_ellipse(center_id, a=3.0, b=2.0)
        engine.add_function_plot("x**2", x_range=(-5, 5))

        data = engine.serialize_all()
        engine2 = GeometryEngine()
        engine2.deserialize_all(data)

        assert len(engine2.objects) == len(data["objects"])
        names = [obj.name for obj in engine2.objects.values()]
        assert "Center" in names
