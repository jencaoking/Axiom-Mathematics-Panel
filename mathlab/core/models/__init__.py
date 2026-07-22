"""几何对象模型子包。

将原本位于 geometry_engine.py 中的几何对象类拆分到独立模块，
通过本 __init__.py 统一重新导出，保持向后兼容。
"""

from mathlab.core.models.base import GeometricObject
from mathlab.core.models.point import Point, Sphere, Plane3D
from mathlab.core.models.line import Segment, Line
from mathlab.core.models.circle import Circle
from mathlab.core.models.polygon import Polygon
from mathlab.core.models.conic import (
    Ellipse,
    Hyperbola,
    Parabola,
    ConicSection,
    _build_general_quadratic_latex,
)
from mathlab.core.models.function import FunctionPlot, ImplicitPlot, PolarPlot
from mathlab.core.models.locus import Locus, Intersection
from mathlab.core.models.dag import DAG

__all__ = [
    "GeometricObject",
    "Point",
    "Sphere",
    "Plane3D",
    "Segment",
    "Line",
    "Circle",
    "Polygon",
    "Ellipse",
    "Hyperbola",
    "Parabola",
    "ConicSection",
    "FunctionPlot",
    "ImplicitPlot",
    "PolarPlot",
    "Locus",
    "Intersection",
    "DAG",
    "_build_general_quadratic_latex",
]
