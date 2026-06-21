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


# ─────────────────────────────────────────────────────────────
# 优化模块 — minimize & root_finding & minimize_scalar
# ─────────────────────────────────────────────────────────────

class TestMinimize:
    def test_parabola_minimum(self, engine):
        """f(x) = x² + x + 2 的极小值在 x=-0.5, f=-0.25+2=1.75"""
        result = engine.minimize(lambda x: x[0]**2 + x[0] + 2, [0.0])
        assert result["success"] is True
        assert pytest.approx(result["x"][0], abs=1e-4) == -0.5
        assert pytest.approx(result["fun"],  abs=1e-4) == 1.75

    def test_rosenbrock(self, engine):
        """Rosenbrock 函数全局最小值在 (1, 1)，值为 0"""
        rosenbrock = lambda x: (1 - x[0])**2 + 100 * (x[1] - x[0]**2)**2
        result = engine.minimize(rosenbrock, [0.0, 0.0], method="BFGS")
        assert result["success"] is True
        assert pytest.approx(result["x"], abs=1e-3) == [1.0, 1.0]

    def test_returns_required_keys(self, engine):
        result = engine.minimize(lambda x: x[0]**2, [1.0])
        assert {"success", "x", "fun", "message"} <= result.keys()


class TestRootFinding:
    def test_quadratic_root(self, engine):
        """x² - 4 在 [0, 5] 内的根为 2"""
        root = engine.root_finding(lambda x: x**2 - 4, [0, 5])
        assert pytest.approx(root, abs=1e-8) == 2.0

    def test_trig_root(self, engine):
        """sin(x) 在 [2, 4] 内的根为 π"""
        root = engine.root_finding(np.sin, [2, 4])
        assert pytest.approx(root, abs=1e-8) == np.pi

    def test_invalid_bracket_raises(self, engine):
        """bracket 长度不为 2 时应抛出 NumEngineError"""
        with pytest.raises(NumEngineError, match="bracket"):
            engine.root_finding(lambda x: x, [0, 1, 2])


class TestMinimizeScalar:
    def test_bounded_minimum(self, engine):
        """f(x)=x² 在 [-1, 2] 内最小值为 0"""
        result = engine.minimize_scalar(lambda x: x**2, bounds=(-1.0, 2.0))
        assert pytest.approx(result["x"],   abs=1e-6) == 0.0
        assert pytest.approx(result["fun"], abs=1e-12) == 0.0

    def test_unbounded_minimum(self, engine):
        """f(x)=(x-3)² 无界搜索最小值在 x=3"""
        result = engine.minimize_scalar(lambda x: (x - 3)**2)
        assert pytest.approx(result["x"], abs=1e-5) == 3.0


# ─────────────────────────────────────────────────────────────
# 信号处理模块 — FFT / IFFT / convolve / find_peaks
# ─────────────────────────────────────────────────────────────

class TestFFT:
    def test_fft_returns_keys(self, engine):
        result = engine.fft_transform([1, 0, -1, 0])
        assert "spectrum" in result and "frequencies" in result

    def test_fft_ifft_roundtrip(self, engine):
        """FFT → IFFT 应还原原信号"""
        original = [1.0, 2.0, 1.0, -1.0, 1.5]
        spectrum = engine.fft_transform(original)["spectrum"]
        recovered = engine.ifft_transform(spectrum).real
        np.testing.assert_array_almost_equal(original, recovered, decimal=10)

    def test_pure_sine_dominant_frequency(self, engine):
        """纯正弦信号的主频应对应其频率"""
        sample_rate = 100.0        # 100 Hz
        freq = 10.0                # 10 Hz 正弦波
        t = np.arange(0, 1, 1 / sample_rate)
        signal = np.sin(2 * np.pi * freq * t)

        result = engine.fft_transform(signal, sample_rate=sample_rate)
        magnitudes = np.abs(result["spectrum"])
        dominant_freq = np.abs(result["frequencies"][np.argmax(magnitudes)])
        assert pytest.approx(dominant_freq, abs=1.0) == freq


class TestConvolve:
    def test_identity_kernel(self, engine):
        """与 delta 函数卷积（'same' 模式）应还原原信号"""
        signal = [1.0, 2.0, 3.0, 4.0, 5.0]
        kernel = [0.0, 1.0, 0.0]
        result = engine.convolve(signal, kernel, mode="same")
        np.testing.assert_array_almost_equal(result, signal)

    def test_convolution_length_full(self, engine):
        """full 卷积长度应为 len(a) + len(b) - 1"""
        a, b = [1, 2, 3], [4, 5]
        result = engine.convolve(a, b, mode="full")
        assert len(result) == len(a) + len(b) - 1


class TestFindPeaks:
    def test_detects_peaks(self, engine):
        """简单峰值信号应能正确检测"""
        signal = [0, 1, 0, 2, 0, 1.5, 0]
        result = engine.find_peaks(signal)
        assert set(result["peak_indices"]) == {1, 3, 5}

    def test_height_threshold(self, engine):
        """设置高度阈值后应只返回超过阈值的峰"""
        signal = [0, 1, 0, 3, 0, 1.5, 0]
        result = engine.find_peaks(signal, height=2.0)
        assert 3 in result["peak_indices"]
        assert 1 not in result["peak_indices"]


# ─────────────────────────────────────────────────────────────
# 统计回归模块 — linear_regression / polynomial_fit / descriptive_stats
# ─────────────────────────────────────────────────────────────

class TestLinearRegression:
    def test_perfect_linear(self, engine):
        """完美线性关系 y=2x 应有 slope=2, intercept=0, r=1"""
        result = engine.linear_regression([1, 2, 3, 4], [2, 4, 6, 8])
        assert pytest.approx(result["slope"],     abs=1e-10) == 2.0
        assert pytest.approx(result["intercept"], abs=1e-10) == 0.0
        assert pytest.approx(result["r_value"],   abs=1e-10) == 1.0

    def test_returns_all_keys(self, engine):
        result = engine.linear_regression([1, 2, 3], [1, 2, 3])
        assert {"slope", "intercept", "r_value", "p_value", "std_err"} <= result.keys()


class TestPolynomialFit:
    def test_quadratic_fit(self, engine):
        """拟合 y = x² 的二次多项式系数应为 [1, 0, 0]"""
        x = np.linspace(-3, 3, 50)
        y = x**2
        result = engine.polynomial_fit(x, y, deg=2)
        coeffs = result["coefficients"]
        assert pytest.approx(coeffs[0], abs=1e-6) == 1.0   # x² 系数
        assert pytest.approx(coeffs[1], abs=1e-6) == 0.0   # x  系数
        assert pytest.approx(coeffs[2], abs=1e-6) == 0.0   # 常数项

    def test_returns_rank(self, engine):
        result = engine.polynomial_fit([1, 2, 3, 4], [1, 4, 9, 16], deg=2)
        assert "rank" in result


class TestDescriptiveStats:
    def test_known_values(self, engine):
        """对已知数据验证均值、中位数和标准差
        
        数据: [2, 4, 4, 4, 5, 5, 7, 9]
        - 均值   = 5.0
        - 中位数 = (4+5)/2 = 4.5
        - 样本标准差 (ddof=1) = sqrt(32/7) ≈ 2.1381  ← 注意：非总体标准差 2.0
        """
        import math
        data = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        result = engine.descriptive_stats(data)
        assert pytest.approx(result["mean"],   abs=1e-10) == 5.0
        assert pytest.approx(result["median"], abs=1e-10) == 4.5
        assert pytest.approx(result["std"],    rel=1e-8)  == math.sqrt(32 / 7)


    def test_returns_all_keys(self, engine):
        result = engine.descriptive_stats([1, 2, 3, 4, 5])
        expected = {"mean", "median", "std", "variance",
                    "skewness", "kurtosis", "min", "max"}
        assert expected <= result.keys()

    def test_min_max(self, engine):
        result = engine.descriptive_stats([3, 1, 4, 1, 5, 9, 2, 6])
        assert result["min"] == 1.0
        assert result["max"] == 9.0
