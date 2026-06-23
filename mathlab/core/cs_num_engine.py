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
    from System import Array, Double
except Exception as e:
    print(f"Warning: Failed to load MathLab.CSharpEngine DLL. Make sure it is built. Error: {e}")
    FastMath = None


class CsNumEngineError(Exception):
    pass


class CsNumEngine:
    """
    底层数值引擎 (C# Python.NET 版本)
    完全兼容 NumEngine 的接口，但核心使用 C# MathNet.Numerics 驱动。
    已重构为 FFI 扁平化数据封送，大幅提升性能。
    """
    def __init__(self):
        if FastMath is None:
            raise CsNumEngineError("C# Engine DLL is not loaded.")
        self._engine = FastMath()
        self.default_tolerance = 1e-8
        
        # 缓存 .NET 类型引用以加速封送
        from System import Array, Double
        self.DotNetArray = Array
        self.DotNetDouble = Double

    def _to_double_array_flat(self, mat: np.ndarray):
        """将 numpy 数组展平为一维，并极速转换为 .NET Array"""
        flat_list = mat.ravel().tolist()
        return self.DotNetArray[self.DotNetDouble](flat_list)

    def eigenvalues(self, matrix):
        mat = np.asarray(matrix, dtype=float)
        if mat.ndim != 2 or mat.shape[0] != mat.shape[1]:
            raise CsNumEngineError("特征值计算需要输入方阵 (Square Matrix)。")
            
        rows, cols = mat.shape
        c_arr = self._to_double_array_flat(mat)
        
        success, er, ei, evec_flat, err = self._engine.Eigenvalues(c_arr, rows, cols)
        if not success:
            raise CsNumEngineError(f"特征值计算失败: {err}")
        
        # 极速将 C# 返回的一维数组重建为 NumPy 数组并组合复数
        values_np = np.array(list(er)) + 1j * np.array(list(ei))
        
        # MathNet's Evd<double>.EigenVectors is a real matrix (packed)
        vectors_np = np.array(list(evec_flat)).reshape(rows, cols)
        
        return {
            "eigenvalues": values_np,
            "eigenvectors": vectors_np,
        }

    def cholesky(self, matrix):
        mat = np.asarray(matrix, dtype=float)
        rows, cols = mat.shape
        c_arr = self._to_double_array_flat(mat)
        
        success, L_flat, err = self._engine.Cholesky(c_arr, rows, cols)
        if not success:
            raise CsNumEngineError(f"Cholesky 分解失败: {err}")
            
        L_np = np.array(list(L_flat)).reshape(rows, cols)
        return {"L": L_np}

    def solve_linear_system(self, A, b):
        mat_A = np.asarray(A, dtype=float)
        vec_b = np.asarray(b, dtype=float)
        
        rows, cols = mat_A.shape
        c_A = self._to_double_array_flat(mat_A)
        c_b = self._to_double_array_flat(vec_b)
        
        success, x_flat, residual_norm, err = self._engine.SolveLinearSystem(c_A, rows, cols, c_b)
        if not success:
            raise CsNumEngineError(f"求解失败: {err}")
            
        x_np = np.array(list(x_flat))
        return {
            "x": x_np,
            "residual_norm": float(residual_norm)
        }

