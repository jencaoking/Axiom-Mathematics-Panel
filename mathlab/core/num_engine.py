import numpy as np
import scipy.linalg as la
import scipy.integrate as integrate
from scipy.misc import derivative
from typing import Dict, Any, Callable, Union


class NumEngineError(Exception):
    """数值计算引擎专属异常"""
    pass


class NumEngine:
    """
    数值计算引擎核心 (基于 NumPy/SciPy)

    提供 Octave 级别的矩阵运算与数值分析接口。
    作为防腐层 (Anti-corruption Layer)，上层业务逻辑只需面向本类编程，
    底层 NumPy/SciPy 依赖的迭代不会污染核心业务逻辑。
    """

    def __init__(self):
        # 预留配置项，例如设置默认的浮点数精度、随机数种子等
        self.default_tolerance = 1e-8

    # ──────────────────────────────────────────────────────────────────────────
    # 线性代数模块 (Linear Algebra)
    # ──────────────────────────────────────────────────────────────────────────

    def eigenvalues(self, matrix: Union[list, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        计算方阵的特征值和特征向量。

        :param matrix: 输入方阵 (list 或 np.ndarray)
        :returns: 包含 'eigenvalues' 和 'eigenvectors' 的字典
        :raises NumEngineError: 输入非方阵时抛出
        """
        mat = np.asarray(matrix, dtype=complex)
        if mat.ndim != 2 or mat.shape[0] != mat.shape[1]:
            raise NumEngineError("特征值计算需要输入方阵 (Square Matrix)。")

        vals, vecs = la.eig(mat)
        return {
            "eigenvalues": vals,
            "eigenvectors": vecs,
        }

    def svd(self, matrix: Union[list, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        奇异值分解 (Singular Value Decomposition)。

        :param matrix: 任意形状的矩阵
        :returns: 包含 'U'、'S'、'Vh' 的字典
                  - U  : 左奇异向量 (m×m 酉矩阵)
                  - S  : 奇异值一维数组 (降序排列)
                  - Vh : 右奇异向量的共轭转置 (n×n 酉矩阵)
        """
        mat = np.asarray(matrix, dtype=float)
        U, S, Vh = la.svd(mat, full_matrices=True)
        return {"U": U, "S": S, "Vh": Vh}

    def lu_decomposition(self, matrix: Union[list, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        LU 分解 (PA = LU)。

        :param matrix: 输入方阵或矩形矩阵
        :returns: 包含 'P'、'L'、'U' 的字典
                  - P : 置换矩阵
                  - L : 下三角矩阵 (对角线元素为 1)
                  - U : 上三角矩阵
        """
        mat = np.asarray(matrix, dtype=float)
        P, L, U = la.lu(mat)
        return {"P": P, "L": L, "U": U}

    def cholesky(self, matrix: Union[list, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Cholesky 分解 (适用于埃尔米特正定矩阵)。

        :param matrix: 埃尔米特正定方阵
        :returns: 包含 'L' 的字典，满足 A = L @ L.T.conj()
        :raises NumEngineError: 矩阵非正定时抛出
        """
        mat = np.asarray(matrix, dtype=float)
        try:
            L = la.cholesky(mat, lower=True)
            return {"L": L}
        except la.LinAlgError as e:
            raise NumEngineError(
                f"Cholesky 分解失败: {e}。请确保矩阵是埃尔米特正定的。"
            )

    def solve_linear_system(
        self,
        A: Union[list, np.ndarray],
        b: Union[list, np.ndarray],
    ) -> Dict[str, Any]:
        """
        求解线性方程组 Ax = b。

        :param A: 系数矩阵 (方阵)
        :param b: 右端向量或矩阵
        :returns: 包含 'x' (解向量/矩阵) 和 'residual_norm' 的字典
        :raises NumEngineError: 矩阵奇异或维度不匹配时抛出
        """
        mat_A = np.asarray(A, dtype=float)
        vec_b = np.asarray(b, dtype=float)
        try:
            x = la.solve(mat_A, vec_b)
            residual_norm = float(np.linalg.norm(mat_A @ x - vec_b))
            return {"x": x, "residual_norm": residual_norm}
        except la.LinAlgError as e:
            raise NumEngineError(f"线性方程组求解失败: {e}。")

    def matrix_rank(self, matrix: Union[list, np.ndarray]) -> int:
        """
        计算矩阵的秩。

        :param matrix: 输入矩阵
        :returns: 矩阵的秩 (整数)
        """
        mat = np.asarray(matrix, dtype=float)
        return int(np.linalg.matrix_rank(mat, tol=self.default_tolerance))

    def condition_number(self, matrix: Union[list, np.ndarray]) -> float:
        """
        计算矩阵的条件数（使用 2-范数）。

        :param matrix: 输入矩阵
        :returns: 条件数 (浮点数)；若矩阵奇异则返回 inf
        """
        mat = np.asarray(matrix, dtype=float)
        return float(np.linalg.cond(mat))

    # ──────────────────────────────────────────────────────────────────────────
    # 数值微积分模块 (Numerical Calculus)
    # ──────────────────────────────────────────────────────────────────────────

    def numerical_derivative(
        self,
        func: Callable[[float], float],
        x: float,
        dx: float = 1e-6,
        order: int = 1,
    ) -> float:
        """
        数值求导（基于中心差分的高阶有限差分）。

        :param func:  目标函数 f: R → R
        :param x:     求导点
        :param dx:    步长，默认 1e-6
        :param order: 导数阶数 (1 = 一阶导，2 = 二阶导，…)
        :returns: 指定阶数的导数值 (浮点数)
        :raises NumEngineError: 计算失败时抛出
        """
        if order < 1:
            raise NumEngineError("导数阶数 order 必须为正整数。")
        try:
            return float(derivative(func, x, dx=dx, n=order))
        except Exception as e:
            raise NumEngineError(f"数值求导失败: {e}")

    def numerical_integral(
        self,
        func: Callable[[float], float],
        a: float,
        b: float,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        数值积分（自适应 Gauss-Kronrod 求积法，QUADPACK 实现）。

        :param func:  被积函数 f: R → R
        :param a:     积分下限（支持 ±np.inf）
        :param b:     积分上限（支持 ±np.inf）
        :param limit: 自适应子区间最大划分数，默认 100
        :returns: 包含 'integral' 和 'error_estimate' 的字典
        :raises NumEngineError: 计算失败时抛出
        """
        try:
            result, error_estimate = integrate.quad(func, a, b, limit=limit)
            return {
                "integral": float(result),
                "error_estimate": float(error_estimate),
            }
        except Exception as e:
            raise NumEngineError(f"数值积分计算失败: {e}")

    def numerical_double_integral(
        self,
        func: Callable[[float, float], float],
        a: float,
        b: float,
        gfun: Callable[[float], float],
        hfun: Callable[[float], float],
    ) -> Dict[str, Any]:
        """
        二重数值积分（DBLQUAD）。

        :param func:  被积函数 f(y, x)
        :param a:     x 积分下限
        :param b:     x 积分上限
        :param gfun:  y 积分下限函数 g(x)
        :param hfun:  y 积分上限函数 h(x)
        :returns: 包含 'integral' 和 'error_estimate' 的字典
        """
        try:
            result, error_estimate = integrate.dblquad(func, a, b, gfun, hfun)
            return {
                "integral": float(result),
                "error_estimate": float(error_estimate),
            }
        except Exception as e:
            raise NumEngineError(f"二重数值积分计算失败: {e}")
