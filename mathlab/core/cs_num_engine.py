import sys
import os
import numpy as np
import time

# 确保能找到 DLL 路径
dll_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'MathLab.CSharpEngine', 'bin', 'Release', 'netstandard2.0'))
if dll_path not in sys.path:
    sys.path.append(dll_path)

import clr
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
    完全兼容 NumEngine 的接口，但核心使用 C# MathNet.Numerics 驱动。
    """
    def __init__(self):
        if FastMath is None:
            raise CsNumEngineError("C# Engine DLL is not loaded.")
        self._engine = FastMath()
        self.default_tolerance = 1e-8

    def _to_double_array_2d(self, mat: np.ndarray):
        import System
        rows, cols = mat.shape
        c_arr = System.Array.CreateInstance(System.Double, rows, cols)
        for i in range(rows):
            for j in range(cols):
                c_arr[i, j] = float(mat[i, j])
        return c_arr
        
    def _to_double_array_1d(self, vec: np.ndarray):
        import System
        length = vec.shape[0]
        c_arr = System.Array.CreateInstance(System.Double, length)
        for i in range(length):
            c_arr[i] = float(vec[i])
        return c_arr

    def eigenvalues(self, matrix):
        mat = np.asarray(matrix, dtype=float)
        if mat.ndim != 2 or mat.shape[0] != mat.shape[1]:
            raise CsNumEngineError("特征值计算需要输入方阵 (Square Matrix)。")
            
        c_arr = self._to_double_array_2d(mat)
        res_dict = self._engine.Eigenvalues(c_arr)
        
        # MathNet returns Complex numbers. pythonnet converts them to Python complex.
        values_csharp = res_dict["eigenvalues"]
        vectors_csharp = res_dict["eigenvectors"]
        
        # Convert C# Complex array to numpy array
        val_len = values_csharp.GetLength(0)
        values_np = np.zeros(val_len, dtype=complex)
        for i in range(val_len):
            values_np[i] = complex(values_csharp[i].Real, values_csharp[i].Imaginary)
            
        rows = vectors_csharp.GetLength(0)
        cols = vectors_csharp.GetLength(1)
        vectors_np = np.zeros((rows, cols), dtype=complex)
        for i in range(rows):
            for j in range(cols):
                c_val = vectors_csharp[i, j]
                vectors_np[i, j] = complex(c_val.Real, c_val.Imaginary)
        
        return {
            "eigenvalues": values_np,
            "eigenvectors": vectors_np,
        }

    def cholesky(self, matrix):
        mat = np.asarray(matrix, dtype=float)
        c_arr = self._to_double_array_2d(mat)
        
        try:
            res_dict = self._engine.Cholesky(c_arr)
            L_csharp = res_dict["L"]
            
            rows = L_csharp.GetLength(0)
            cols = L_csharp.GetLength(1)
            L_np = np.zeros((rows, cols), dtype=float)
            for i in range(rows):
                for j in range(cols):
                    L_np[i, j] = L_csharp[i, j]
                    
            return {"L": L_np}
        except Exception as e:
            raise CsNumEngineError(f"Cholesky 分解失败: {e}")

    def solve_linear_system(self, A, b):
        mat_A = np.asarray(A, dtype=float)
        vec_b = np.asarray(b, dtype=float)
        
        c_A = self._to_double_array_2d(mat_A)
        c_b = self._to_double_array_1d(vec_b)
        
        try:
            res_dict = self._engine.SolveLinearSystem(c_A, c_b)
            x_csharp = res_dict["x"]
            
            length = x_csharp.GetLength(0)
            x_np = np.zeros(length, dtype=float)
            for i in range(length):
                x_np[i] = x_csharp[i]
                
            return {
                "x": x_np,
                "residual_norm": float(res_dict["residual_norm"])
            }
        except Exception as e:
            raise CsNumEngineError(f"求解失败: {e}")
