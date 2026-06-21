"""
NumEngine 单元测试套件

运行方式:
    pytest mathlab/tests/test_num_engine.py -v
"""

import numpy as np
import pytest

from mathlab.core.num_engine import NumEngine, NumEngineError


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def engine() -> NumEngine:
    return NumEngine()


@pytest.fixture
def identity_2x2() -> list:
    return [[1, 0], [0, 1]]


@pytest.fixture
def pos_def_3x3() -> list:
    """一个 3×3 对称正定矩阵"""
    return [[4, 2, 2],
            [2, 3, 1],
            [2, 1, 3]]


# ─────────────────────────────────────────────────────────────
# 线性代数 — 特征值
# ─────────────────────────────────────────────────────────────

class TestEigenvalues:
    def test_diagonal_matrix(self, engine):
        """对角矩阵的特征值应为对角元素"""
        result = engine.eigenvalues([[2, 0], [0, 3]])
        evals = np.sort(np.real(result["eigenvalues"]))
        assert pytest.approx(evals, abs=1e-10) == [2.0, 3.0]

    def test_eigenvectors_shape(self, engine):
        """特征向量矩阵应为 n×n"""
        matrix = [[1, 2], [3, 4]]
        result = engine.eigenvalues(matrix)
        assert result["eigenvectors"].shape == (2, 2)

    def test_non_square_raises(self, engine):
        """非方阵应抛出 NumEngineError"""
        with pytest.raises(NumEngineError, match="方阵"):
            engine.eigenvalues([[1, 2, 3], [4, 5, 6]])

    def test_identity_eigenvalues(self, engine, identity_2x2):
        """单位矩阵特征值均为 1"""
        result = engine.eigenvalues(identity_2x2)
        evals = np.sort(np.real(result["eigenvalues"]))
        assert pytest.approx(evals, abs=1e-10) == [1.0, 1.0]


# ─────────────────────────────────────────────────────────────
# 线性代数 — SVD
# ─────────────────────────────────────────────────────────────

class TestSVD:
    def test_singular_values_non_negative(self, engine):
        """奇异值应为非负数"""
        result = engine.svd([[1, 2], [3, 4], [5, 6]])
        assert np.all(result["S"] >= 0)

    def test_svd_reconstruction(self, engine):
        """通过 U @ diag(S) @ Vh 应能还原原矩阵"""
        matrix = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        result = engine.svd(matrix)
        U, S, Vh = result["U"], result["S"], result["Vh"]
        S_mat = np.zeros_like(matrix)
        np.fill_diagonal(S_mat, S)
        reconstructed = U @ S_mat @ Vh
        assert pytest.approx(reconstructed, abs=1e-10) == matrix

    def test_svd_shapes(self, engine):
        """验证 SVD 各分量的形状"""
        matrix = np.random.rand(4, 3)
        result = engine.svd(matrix)
        assert result["U"].shape == (4, 4)
        assert result["S"].shape == (3,)
        assert result["Vh"].shape == (3, 3)


# ─────────────────────────────────────────────────────────────
# 线性代数 — LU 分解
# ─────────────────────────────────────────────────────────────

class TestLUDecomposition:
    def test_lu_reconstruction(self, engine):
        """P @ A 应等于 L @ U"""
        matrix = [[3.0, 1.0], [6.0, 3.0]]
        result = engine.lu_decomposition(matrix)
        P, L, U = result["P"], result["L"], result["U"]
        mat = np.array(matrix)
        assert pytest.approx(P @ mat, abs=1e-10) == L @ U

    def test_l_lower_triangular(self, engine):
        """L 矩阵应为下三角"""
        result = engine.lu_decomposition([[2, 1], [4, 3]])
        L = result["L"]
        assert np.allclose(L, np.tril(L))

    def test_u_upper_triangular(self, engine):
        """U 矩阵应为上三角"""
        result = engine.lu_decomposition([[2, 1], [4, 3]])
        U = result["U"]
        assert np.allclose(U, np.triu(U))


# ─────────────────────────────────────────────────────────────
# 线性代数 — Cholesky 分解
# ─────────────────────────────────────────────────────────────

class TestCholesky:
    def test_cholesky_reconstruction(self, engine, pos_def_3x3):
        """L @ L.T 应还原原矩阵"""
        result = engine.cholesky(pos_def_3x3)
        L = result["L"]
        reconstructed = L @ L.T
        assert pytest.approx(reconstructed, abs=1e-10) == np.array(pos_def_3x3)

    def test_cholesky_non_positive_definite_raises(self, engine):
        """非正定矩阵应抛出 NumEngineError"""
        with pytest.raises(NumEngineError, match="Cholesky"):
            engine.cholesky([[-1, 0], [0, 1]])


# ─────────────────────────────────────────────────────────────
# 线性代数 — 线性方程组求解
# ─────────────────────────────────────────────────────────────

class TestSolveLinearSystem:
    def test_simple_2x2(self, engine):
        """2x + y = 5, x + 3y = 10  →  x=1, y=3"""
        A = [[2, 1], [1, 3]]
        b = [5, 10]
        result = engine.solve_linear_system(A, b)
        assert pytest.approx(result["x"], abs=1e-10) == [1.0, 3.0]

    def test_residual_near_zero(self, engine):
        """残差范数应接近机器精度"""
        A = [[4, 1], [2, 3]]
        b = [9, 8]
        result = engine.solve_linear_system(A, b)
        assert result["residual_norm"] < 1e-10


# ─────────────────────────────────────────────────────────────
# 线性代数 — 秩与条件数
# ─────────────────────────────────────────────────────────────

class TestRankAndCondition:
    def test_full_rank_matrix(self, engine):
        assert engine.matrix_rank([[1, 0], [0, 1]]) == 2

    def test_rank_deficient_matrix(self, engine):
        """行向量线性相关，秩为 1"""
        assert engine.matrix_rank([[1, 2], [2, 4]]) == 1

    def test_identity_condition_number(self, engine, identity_2x2):
        """单位矩阵条件数应为 1"""
        assert pytest.approx(engine.condition_number(identity_2x2), abs=1e-10) == 1.0


# ─────────────────────────────────────────────────────────────
# 数值微积分 — 导数
# ─────────────────────────────────────────────────────────────

class TestNumericalDerivative:
    def test_polynomial_first_order(self, engine):
        """f(x)=x² 在 x=3 处一阶导 = 6"""
        result = engine.numerical_derivative(lambda x: x**2, 3.0)
        assert pytest.approx(result, rel=1e-4) == 6.0

    def test_polynomial_second_order(self, engine):
        """f(x)=x³ 在 x=2 处二阶导 = 12"""
        result = engine.numerical_derivative(lambda x: x**3, 2.0, order=2)
        assert pytest.approx(result, rel=1e-3) == 12.0

    def test_trig_derivative(self, engine):
        """sin'(π/4) ≈ cos(π/4) ≈ 0.7071"""
        result = engine.numerical_derivative(np.sin, np.pi / 4)
        assert pytest.approx(result, rel=1e-5) == np.cos(np.pi / 4)

    def test_invalid_order_raises(self, engine):
        """order < 1 应抛出 NumEngineError"""
        with pytest.raises(NumEngineError, match="正整数"):
            engine.numerical_derivative(lambda x: x, 1.0, order=0)


# ─────────────────────────────────────────────────────────────
# 数值微积分 — 定积分
# ─────────────────────────────────────────────────────────────

class TestNumericalIntegral:
    def test_linear_function(self, engine):
        """∫₀² x dx = 2"""
        result = engine.numerical_integral(lambda x: x, 0, 2)
        assert pytest.approx(result["integral"], rel=1e-8) == 2.0

    def test_constant_function(self, engine):
        """∫₁⁵ 1 dx = 4"""
        result = engine.numerical_integral(lambda x: 1, 1, 5)
        assert pytest.approx(result["integral"], rel=1e-8) == 4.0

    def test_trig_function(self, engine):
        """∫₀^π sin(x) dx = 2"""
        result = engine.numerical_integral(np.sin, 0, np.pi)
        assert pytest.approx(result["integral"], rel=1e-8) == 2.0

    def test_error_estimate_present(self, engine):
        """返回值应包含 error_estimate 字段"""
        result = engine.numerical_integral(lambda x: x**2, 0, 1)
        assert "error_estimate" in result
        assert result["error_estimate"] >= 0

    def test_improper_integral(self, engine):
        """∫₀^∞ e^{-x} dx = 1（广义积分）"""
        result = engine.numerical_integral(lambda x: np.exp(-x), 0, np.inf)
        assert pytest.approx(result["integral"], rel=1e-6) == 1.0


# ─────────────────────────────────────────────────────────────
# 数值微积分 — 二重积分
# ─────────────────────────────────────────────────────────────

class TestNumericalDoubleIntegral:
    def test_unit_square_area(self, engine):
        """∫₀¹∫₀¹ 1 dy dx = 1 (单位正方形面积)"""
        result = engine.numerical_double_integral(
            lambda y, x: 1.0, 0, 1, lambda x: 0, lambda x: 1
        )
        assert pytest.approx(result["integral"], rel=1e-8) == 1.0

    def test_bilinear_function(self, engine):
        """∫₀¹∫₀¹ (x + y) dy dx = 1"""
        result = engine.numerical_double_integral(
            lambda y, x: x + y, 0, 1, lambda x: 0, lambda x: 1
        )
        assert pytest.approx(result["integral"], rel=1e-8) == 1.0
