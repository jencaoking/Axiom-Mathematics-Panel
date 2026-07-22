import sys
import os

# 确保能找到 DLL 路径
dll_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "MathLab.CSharpEngine",
        "bin",
        "Release",
        "netstandard2.0",
    )
)
if dll_path not in sys.path:
    sys.path.append(dll_path)

os.environ.setdefault("PYTHONNET_RUNTIME", "coreclr")

# 将 import clr 移入 try 块中，防止底层运行时缺失引发 RuntimeError 击穿
try:
    import clr

    clr.AddReference("MathLab.CSharpEngine")
    from MathLab.CSharpEngine import FastGeometry
except Exception as e:
    print(f"Warning: Failed to load MathLab.CSharpEngine DLL or .NET runtime. Error: {e}")
    FastGeometry = None


class CsGeometryEngine:
    """
    几何底层优化引擎 (C# Python.NET 版本)
    已开启内存池化 (Buffer Reuse) 机制，实现零 GC 开销的高频几何运算。
    """

    def __init__(self):
        if FastGeometry is None:
            self._engine = None
        else:
            self._engine = FastGeometry()

    @property
    def is_available(self):
        return self._engine is not None

    def _flat_array_to_points_fast(self, flat_array, point_count):
        """
        根据 C# 返回的有效点数量 (point_count) 截取数据。
        如果 point_count 为 0，说明没有交点，直接返回空列表。
        """
        if point_count == 0:
            return []

        points = []
        for i in range(point_count):
            idx = i * 2
            points.append((float(flat_array[idx]), float(flat_array[idx + 1])))
        return points

    def solve_line_line(self, a1, b1, c1, a2, b2, c2):
        if not self.is_available:
            return None
        # clr 会将返回的数组和 out 参数封装成元组: (double[] buffer, int pointCount)
        res_buffer, count = self._engine.SolveLineLineFast(
            float(a1), float(b1), float(c1), float(a2), float(b2), float(c2)
        )
        return self._flat_array_to_points_fast(res_buffer, count)

    def solve_line_circle(self, a, b, c, cx, cy, r):
        if not self.is_available:
            return None
        res_buffer, count = self._engine.SolveLineCircleFast(
            float(a), float(b), float(c), float(cx), float(cy), float(r)
        )
        return self._flat_array_to_points_fast(res_buffer, count)

    def solve_circle_circle(self, cx1, cy1, r1, cx2, cy2, r2):
        if not self.is_available:
            return None
        res_buffer, count = self._engine.SolveCircleCircleFast(
            float(cx1), float(cy1), float(r1), float(cx2), float(cy2), float(r2)
        )
        return self._flat_array_to_points_fast(res_buffer, count)

    def generate_conic_points(self, A, B, C, D, E, F, x_range, y_range, num_points):
        # 这个方法暂未做 Buffer 优化，保持原样
        if not self.is_available:
            return None
        res = self._engine.GenerateConicPoints(
            float(A),
            float(B),
            float(C),
            float(D),
            float(E),
            float(F),
            float(x_range[0]),
            float(x_range[1]),
            float(y_range[0]),
            float(y_range[1]),
            int(num_points),
        )
        # 因为没有 out count，复用老版的解析逻辑
        points = []
        for i in range(0, len(res), 2):
            points.append((float(res[i]), float(res[i + 1])))
        return points


# 全局单例
cs_geometry = CsGeometryEngine()
