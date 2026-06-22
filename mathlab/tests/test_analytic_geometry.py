"""
解析几何深化功能测试套件
测试圆锥曲线、函数绘图和轨迹追踪功能
"""
import numpy as np
import os
import sys
import importlib.util

mathlab_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, mathlab_dir)

spec = importlib.util.spec_from_file_location(
    "geometry_engine", os.path.join(mathlab_dir, "core", "geometry_engine.py")
)
geometry_engine_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geometry_engine_module)
GeometryEngine = geometry_engine_module.GeometryEngine


class TestConicSections:
    def test_ellipse_created(self):
        engine = GeometryEngine()
        center_id = engine.add_point(0, 0, name="C1")
        ellipse_id = engine.add_ellipse(center_id, a=3.0, b=2.0)
        ellipse = engine.get_object(ellipse_id)
        assert ellipse is not None
        assert len(ellipse.coordinates.get("points", [])) > 0

    def test_ellipse_latex(self):
        engine = GeometryEngine()
        center_id = engine.add_point(0, 0)
        ellipse_id = engine.add_ellipse(center_id, a=3.0, b=2.0)
        ellipse = engine.get_object(ellipse_id)
        latex = ellipse.to_latex()
        assert "frac" in latex or "x" in latex

    def test_hyperbola_created(self):
        engine = GeometryEngine()
        center_id = engine.add_point(5, 0, name="C2")
        hyp_id = engine.add_hyperbola(center_id, a=2.0, b=1.5)
        hyp = engine.get_object(hyp_id)
        assert hyp is not None
        assert hyp.type == "Hyperbola"

    def test_parabola_created(self):
        engine = GeometryEngine()
        vertex_id = engine.add_point(0, -2, name="V1")
        par_id = engine.add_parabola(vertex_id, p=1.0, direction="up")
        par = engine.get_object(par_id)
        assert par is not None
        assert par.type == "Parabola"

    def test_conic_section_circle(self):
        engine = GeometryEngine()
        conic_id = engine.add_conic_section(A=1, B=0, C=1, D=0, E=0, F=-4)
        conic = engine.get_object(conic_id)
        assert conic is not None
        assert len(conic.points_data) > 0


class TestFunctionPlots:
    def test_explicit_function(self):
        engine = GeometryEngine()
        func_id = engine.add_function_plot("x**2", x_range=(-5, 5), num_points=200)
        func = engine.get_object(func_id)
        assert func is not None
        assert len(func.points_data) > 0

    def test_sine_function(self):
        engine = GeometryEngine()
        func_id = engine.add_function_plot("sin(x)", x_range=(-6.28, 6.28), num_points=300)
        func = engine.get_object(func_id)
        assert func is not None
        assert len(func.points_data) > 0

    def test_implicit_plot(self):
        engine = GeometryEngine()
        impl_id = engine.add_implicit_plot("x**2 + y**2 - 1", x_range=(-2, 2), y_range=(-2, 2))
        impl = engine.get_object(impl_id)
        assert impl is not None
        assert len(impl.points_data) > 0

    def test_polar_plot(self):
        engine = GeometryEngine()
        polar_id = engine.add_polar_plot("2*cos(theta)", theta_range=(0, 2 * np.pi), num_points=300)
        polar = engine.get_object(polar_id)
        assert polar is not None
        assert len(polar.points_data) > 0


class TestLocus:
    def test_locus_creation(self):
        engine = GeometryEngine()
        driver_id = engine.add_point(0, 0, name="Driver")
        tracer_id = engine.add_point(2, 0, name="Tracer")
        locus_id = engine.add_locus(tracer_id, driver_id, max_points=100)
        locus = engine.get_object(locus_id)
        assert locus is not None
        assert locus.type == "Locus"

    def test_locus_trail(self):
        engine = GeometryEngine()
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
    def test_roundtrip(self):
        engine = GeometryEngine()
        center_id = engine.add_point(0, 0, name="Center")
        engine.add_ellipse(center_id, a=3.0, b=2.0)
        engine.add_function_plot("x**2", x_range=(-5, 5))

        data = engine.serialize_all()
        engine2 = GeometryEngine()
        engine2.deserialize_all(data)

        assert len(engine2.objects) == len(data["objects"])
        names = [obj.name for obj in engine2.objects.values()]
        assert "Center" in names
