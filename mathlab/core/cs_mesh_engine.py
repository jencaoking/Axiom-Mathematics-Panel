import sys
import os
import clr

dll_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'MathLab.CSharpEngine', 'bin', 'Release', 'netstandard2.0'))
if dll_path not in sys.path:
    sys.path.append(dll_path)
try:
    clr.AddReference("MathLab.CSharpEngine")
    from MathLab.CSharpEngine import FastMesh3D
except Exception as e:
    print(f"Failed to load C# 3D Mesh Engine: {e}")
    FastMesh3D = None


class CsMeshEngine:
    """3D 空间曲面网格计算引擎"""
    def __init__(self):
        if FastMesh3D is None:
            raise RuntimeError("C# Engine DLL is not loaded.")
        self._engine = FastMesh3D()

    def get_ripple_mesh_data(self, x_range, y_range, x_seg=150, y_seg=150, time_val=0.0, freq=2.0):
        """
        生成一维展平的顶点列表，供前端 WebGL 消费
        """
        # 调用 C# 进行密集空间点并行矩阵计算
        res_flat = self._engine.GenerateRippleMesh(
            float(x_range[0]), float(x_range[1]),
            float(y_range[0]), float(y_range[1]),
            int(x_seg), int(y_seg),
            float(time_val), float(freq)
        )

        # 极速将非托管的 C# float[] 转换为 python 基础的 list (WebGL 传输所需)
        return list(res_flat)


# 全局单例
cs_mesh_3d = CsMeshEngine()
