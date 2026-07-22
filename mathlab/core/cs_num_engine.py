import sys
import os
import clr
import numpy as np

# 确保能找到 DLL 路径
dll_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'MathLab.CSharpEngine', 'bin', 'Release', 'netstandard2.0'))
if dll_path not in sys.path:
    sys.path.append(dll_path)

os.environ.setdefault('PYTHONNET_RUNTIME', 'coreclr')
try:
    clr.AddReference("MathLab.CSharpEngine")
    from MathLab.CSharpEngine import FastMath
except Exception as e:
    print(f"Warning: Failed to load MathLab.CSharpEngine DLL. Make sure it is built. Error: {e}")
    FastMath = None


class CsNumEngineError(Exception):
    pass


class CsNumEngine:
    """
    底层数值引擎 (C# Python.NET 版本)
    全面启用一维平铺 (Flat Array) 进行极速跨语言内存封送。
    """
    def __init__(self):
        if FastMath is None:
            raise CsNumEngineError("C# Engine DLL is not loaded.")
        self._engine = FastMath()
        self.default_tolerance = 1e-8

    def _to_double_array_flat(self, arr: np.ndarray):
        """
        核心优化：将 numpy 数组直接打平并转换为 C# 一维 System.Double 数组。
        避开 pythonnet 处理二维数组高昂的反射开销。
        """
        import System
        # .ravel() 返回连续视图，.tolist() 生成原生列表，pythonnet 转换极快
        return System.Array[System.Double](arr.ravel().tolist())

    def eigenvalues(self, matrix):
        mat = np.asarray(matrix, dtype=float)
        if mat.ndim != 2 or mat.shape[0] != mat.shape[1]:
            raise CsNumEngineError("特征值计算需要输入方阵 (Square Matrix)。")

        rows, cols = mat.shape
        c_arr_flat = self._to_double_array_flat(mat)

        # 调用 C# 新增的 Flat 接口
        res_dict = self._engine.EigenvaluesFlat(c_arr_flat, rows, cols)

        values_csharp = res_dict["eigenvalues"]
        vectors_csharp = res_dict["eigenvectors"]

        # 处理复数数组
        val_len = values_csharp.Length
        values_np = np.zeros(val_len, dtype=complex)
        for i in range(val_len):
            values_np[i] = complex(values_csharp[i].Real, values_csharp[i].Imaginary)

        # 提取一维打平的特征向量并还原为二维
        vectors_np = np.zeros((rows, cols), dtype=complex)
        idx = 0
        for i in range(rows):
            for j in range(cols):
                c_val = vectors_csharp[idx]
                vectors_np[i, j] = complex(c_val.Real, c_val.Imaginary)
                idx += 1

        return {
            "eigenvalues": values_np,
            "eigenvectors": vectors_np,
        }

    def cholesky(self, matrix):
        mat = np.asarray(matrix, dtype=float)
        rows, cols = mat.shape
        c_arr_flat = self._to_double_array_flat(mat)

        try:
            res_dict = self._engine.CholeskyFlat(c_arr_flat, rows, cols)

            # 极速提取：将 C# 返回的一维数组转为 list，交由 numpy 瞬间重塑二维
            L_flat = list(res_dict["L"])
            L_np = np.array(L_flat, dtype=float).reshape(rows, cols)

            return {"L": L_np}
        except Exception as e:
            raise CsNumEngineError(f"Cholesky 分解失败: {e}")

    def solve_linear_system(self, A, b):
        mat_A = np.asarray(A, dtype=float)
        vec_b = np.asarray(b, dtype=float)

        rows, cols = mat_A.shape
        c_A_flat = self._to_double_array_flat(mat_A)
        c_b_flat = self._to_double_array_flat(vec_b)

        try:
            res_dict = self._engine.SolveLinearSystemFlat(c_A_flat, rows, cols, c_b_flat)

            # 极速提取：利用 list() 一次性取出一维结果
            x_np = np.array(list(res_dict["x"]), dtype=float)

            return {
                "x": x_np,
                "residual_norm": float(res_dict["residual_norm"])
            }
        except Exception as e:
            raise CsNumEngineError(f"求解失败: {e}")
