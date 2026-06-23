import sys
import os

# 确保能找到 DLL 路径
dll_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'MathLab.CSharpEngine', 'bin', 'Release', 'netstandard2.0'))
if dll_path not in sys.path:
    sys.path.append(dll_path)

import clr
try:
    clr.AddReference("MathLab.CSharpEngine")
    from MathLab.CSharpEngine import FastGeometry
except Exception as e:
    print(f"Warning: Failed to load MathLab.CSharpEngine DLL. Make sure it is built. Error: {e}")
    FastGeometry = None


class CsGeometryEngine:
    """
    几何底层优化引擎 (C# Python.NET 版本)
    用于接管求交、点集生成等高频热点计算。
    """
    def __init__(self):
        if FastGeometry is None:
            self._engine = None
        else:
            self._engine = FastGeometry()

    @property
    def is_available(self):
        return self._engine is not None

    def _flat_array_to_points(self, flat_array):
        """将 C# 返回的一维平铺数组 [x1, y1, x2, y2] 转换为 [(x1, y1), (x2, y2)]"""
        points = []
        for i in range(0, len(flat_array), 2):
            points.append((float(flat_array[i]), float(flat_array[i+1])))
        return points

    def solve_line_line(self, a1, b1, c1, a2, b2, c2):
        if not self.is_available:
            return None
        res = self._engine.SolveLineLine(float(a1), float(b1), float(c1), float(a2), float(b2), float(c2))
        return self._flat_array_to_points(res)

    def solve_line_circle(self, a, b, c, cx, cy, r):
        if not self.is_available:
            return None
        res = self._engine.SolveLineCircle(float(a), float(b), float(c), float(cx), float(cy), float(r))
        return self._flat_array_to_points(res)

    def solve_circle_circle(self, cx1, cy1, r1, cx2, cy2, r2):
        if not self.is_available:
            return None
        res = self._engine.SolveCircleCircle(float(cx1), float(cy1), float(r1), float(cx2), float(cy2), float(r2))
        return self._flat_array_to_points(res)

    def generate_conic_points(self, A, B, C, D, E, F, x_range, y_range, num_points):
        if not self.is_available:
            return None
        res = self._engine.GenerateConicPoints(
            float(A), float(B), float(C), float(D), float(E), float(F),
            float(x_range[0]), float(x_range[1]), float(y_range[0]), float(y_range[1]),
            int(num_points)
        )
        return self._flat_array_to_points(res)

# 全局单例
cs_geometry = CsGeometryEngine()
