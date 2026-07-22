"""NumEngine 单元测试套件。

Uses the shared ``num_engine`` fixture from the root conftest.py instead
of a local fixture definition. All test functions are marked with
``@pytest.mark.unit``.

运行方式:
    pytest mathlab/tests/unit/test_num_engine.py -v
"""

import numpy as np
import pytest

from mathlab.core.num_engine import NumEngineError


# ─────────────────────────────────────────────────────────────
# 线性代数 — 特征值
# ─────────────────────────────────────────────────────────────

class TestEigenvalues:
    @pytest.mark.unit
    def test_diagonal_matrix(self, num_engine):
        """对角矩阵的特征值应为对角元素"""
        result = num_engine.eigenvalues([[2, 0], [0, 3]])
        evals = np.sort(np.real(result["eigenvalues"]))
        assert pytest.approx(evals, abs=1e-10) == [2.0, 3.0]

    @pytest.mark.unit
    def test_eigenvectors_shape(self, num_engine):
        """特征向量矩阵应为 n×n"""
        matrix = [[1, 2], [3, 4]]
        result = num_engine.eigenvalues(matrix)
        assert result["eigenvectors"].shape == (2, 2)

    @pytest.mark.unit
    def test_non_square_raises(self, num_engine):
        """非方阵应抛出 NumEngineError"""
        with pytest.raises(NumEngineError, match="方阵"):
            num_engine.eigenvalues([[1, 2, 3], [4, 5, 6]])

    @pytest.mark.unit
    def test_identity_eigenvalues(self, num_engine):
        """单位矩阵特征值均为 1"""
        identity_2x2 = [[1, 0], [0, 1]]
        result = num_engine.eigenvalues(identity_2x2)
        evals = np.sort(np.real(result["eigenvalues"]))
        assert pytest.approx(evals, abs=1e-10) == [1.0, 1.0]


# ─────────────────────────────────────────────────────────────
# 线性代数 — SVD
# ─────────────────────────────────────────────────────────────

class TestSVD:
    @pytest.mark.unit
    def test_singular_values_non_negative(self, num_engine):
        """奇异值应为非负数"""
        result = num_engine.svd([[1, 2], [3, 4], [5, 6]])
        assert np.all(result["S"] >= 0)

    @pytest.mark.unit
    def test_svd_reconstruction(self, num_engine):
        """通过 U @ diag(S) @ Vh 应能还原原矩阵"""
        matrix = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        result = num_engine.svd(matrix)
        U, S, Vh = result["U"], result["S"], result["Vh"]
        S_mat = np.zeros_like(matrix)
        np.fill_diagonal(S_mat, S)
        reconstructed = U @ S_mat @ Vh
        assert pytest.approx(reconstructed, abs=1e-10) == matrix

    @pytest.mark.unit
    def test_svd_shapes(self, num_engine):
        """验证 SVD 各分量的形状"""
        matrix = np.random.rand(4, 3)
        result = num_engine.svd(matrix)
        assert result["U"].shape == (4, 4)
        assert result["S"].shape == (3,)
        assert result["Vh"].shape == (3, 3)


# ─────────────────────────────────────────────────────────────
# 线性代数 — LU 分解
# ─────────────────────────────────────────────────────────────

class TestLUDecomposition:
    @pytest.mark.unit
    def test_lu_reconstruction(self, num_engine):
        """P @ A 应等于 L @ U"""
        matrix = [[3.0, 1.0], [6.0, 3.0]]
        result = num_engine.lu_decomposition(matrix)
        P, L, U = result["P"], result["L"], result["U"]
        mat = np.array(matrix)
        assert pytest.approx(P @ mat, abs=1e-10) == L @ U

    @pytest.mark.unit
    def test_l_lower_triangular(self, num_engine):
        """L 矩阵应为下三角"""
        result = num_engine.lu_decomposition([[2, 1], [4, 3]])
        L = result["L"]
        assert np.allclose(L, np.tril(L))

    @pytest.mark.unit
    def test_u_upper_triangular(self, num_engine):
        """U 矩阵应为上三角"""
        result = num_engine.lu_decomposition([[2, 1], [4, 3]])
        U = result["U"]
        assert np.allclose(U, np.triu(U))


# ─────────────────────────────────────────────────────────────
# 线性代数 — Cholesky 分解
# ─────────────────────────────────────────────────────────────

class TestCholesky:
    @pytest.mark.unit
    def test_cholesky_reconstruction(self, num_engine):
        """L @ L.T 应还原原矩阵"""
        pos_def_3x3 = [[4, 2, 2],
                       [2, 3, 1],
                       [2, 1, 3]]
        result = num_engine.cholesky(pos_def_3x3)
        L = result["L"]
        reconstructed = L @ L.T
        assert pytest.approx(reconstructed, abs=1e-10) == np.array(pos_def_3x3)

    @pytest.mark.unit
    def test_cholesky_non_positive_definite_raises(self, num_engine):
        """非正定矩阵应抛出 NumEngineError"""
        with pytest.raises(NumEngineError, match="Cholesky"):
            num_engine.cholesky([[-1, 0], [0, 1]])


# ─────────────────────────────────────────────────────────────
# 线性代数 — 线性方程组求解
# ─────────────────────────────────────────────────────────────

class TestSolveLinearSystem:
    @pytest.mark.unit
    def test_simple_2x2(self, num_engine):
        """2x + y = 5, x + 3y = 10  →  x=1, y=3"""
        A = [[2, 1], [1, 3]]
        b = [5, 10]
        result = num_engine.solve_linear_system(A, b)
        assert pytest.approx(result["x"], abs=1e-10) == [1.0, 3.0]

    @pytest.mark.unit
    def test_residual_near_zero(self, num_engine):
        """残差范数应接近机器精度"""
        A = [[4, 1], [2, 3]]
        b = [9, 8]
        result = num_engine.solve_linear_system(A, b)
        assert result["residual_norm"] < 1e-10


# ─────────────────────────────────────────────────────────────
# 线性代数 — 秩与条件数
# ─────────────────────────────────────────────────────────────

class TestRankAndCondition:
    @pytest.mark.unit
    def test_full_rank_matrix(self, num_engine):
        assert num_engine.matrix_rank([[1, 0], [0, 1]]) == 2

    @pytest.mark.unit
    def test_rank_deficient_matrix(self, num_engine):
        """行向量线性相关，秩为 1"""
        assert num_engine.matrix_rank([[1, 2], [2, 4]]) == 1

    @pytest.mark.unit
    def test_identity_condition_number(self, num_engine):
        """单位矩阵条件数应为 1"""
        identity_2x2 = [[1, 0], [0, 1]]
        assert pytest.approx(num_engine.condition_number(identity_2x2), abs=1e-10) == 1.0


# ─────────────────────────────────────────────────────────────
# 数值微积分 — 导数
# ─────────────────────────────────────────────────────────────

class TestNumericalDerivative:
    @pytest.mark.unit
    def test_polynomial_first_order(self, num_engine):
        """f(x)=x² 在 x=3 处一阶导 = 6"""
        result = num_engine.numerical_derivative(lambda x: x**2, 3.0)
        assert pytest.approx(result, rel=1e-4) == 6.0

    @pytest.mark.unit
    def test_polynomial_second_order(self, num_engine):
        """f(x)=x³ 在 x=2 处二阶导 = 12"""
        result = num_engine.numerical_derivative(lambda x: x**3, 2.0, order=2)
        assert pytest.approx(result, rel=1e-3) == 12.0

    @pytest.mark.unit
    def test_trig_derivative(self, num_engine):
        """sin'(π/4) ≈ cos(π/4) ≈ 0.7071"""
        result = num_engine.numerical_derivative(np.sin, np.pi / 4)
        assert pytest.approx(result, rel=1e-5) == np.cos(np.pi / 4)

    @pytest.mark.unit
    def test_invalid_order_raises(self, num_engine):
        """order < 1 应抛出 NumEngineError"""
        with pytest.raises(NumEngineError, match="正整数"):
            num_engine.numerical_derivative(lambda x: x, 1.0, order=0)


# ─────────────────────────────────────────────────────────────
# 数值微积分 — 定积分
# ─────────────────────────────────────────────────────────────

class TestNumericalIntegral:
    @pytest.mark.unit
    def test_linear_function(self, num_engine):
        """∫₀² x dx = 2"""
        result = num_engine.numerical_integral(lambda x: x, 0, 2)
        assert pytest.approx(result["integral"], rel=1e-8) == 2.0

    @pytest.mark.unit
    def test_constant_function(self, num_engine):
        """∫₁⁵ 1 dx = 4"""
        result = num_engine.numerical_integral(lambda x: 1, 1, 5)
        assert pytest.approx(result["integral"], rel=1e-8) == 4.0

    @pytest.mark.unit
    def test_trig_function(self, num_engine):
        """∫₀^π sin(x) dx = 2"""
        result = num_engine.numerical_integral(np.sin, 0, np.pi)
        assert pytest.approx(result["integral"], rel=1e-8) == 2.0

    @pytest.mark.unit
    def test_error_estimate_present(self, num_engine):
        """返回值应包含 error_estimate 字段"""
        result = num_engine.numerical_integral(lambda x: x**2, 0, 1)
        assert "error_estimate" in result
        assert result["error_estimate"] >= 0

    @pytest.mark.unit
    def test_improper_integral(self, num_engine):
        """∫₀^∞ e^{-x} dx = 1（广义积分）"""
        result = num_engine.numerical_integral(lambda x: np.exp(-x), 0, np.inf)
        assert pytest.approx(result["integral"], rel=1e-6) == 1.0


# ─────────────────────────────────────────────────────────────
# 数值微积分 — 二重积分
# ─────────────────────────────────────────────────────────────

class TestNumericalDoubleIntegral:
    @pytest.mark.unit
    def test_unit_square_area(self, num_engine):
        """∫₀¹∫₀¹ 1 dy dx = 1 (单位正方形面积)"""
        result = num_engine.numerical_double_integral(
            lambda y, x: 1.0, 0, 1, lambda x: 0, lambda x: 1
        )
        assert pytest.approx(result["integral"], rel=1e-8) == 1.0

    @pytest.mark.unit
    def test_bilinear_function(self, num_engine):
        """∫₀¹∫₀¹ (x + y) dy dx = 1"""
        result = num_engine.numerical_double_integral(
            lambda y, x: x + y, 0, 1, lambda x: 0, lambda x: 1
        )
        assert pytest.approx(result["integral"], rel=1e-8) == 1.0


# ─────────────────────────────────────────────────────────────
# 优化模块 — minimize & root_finding & minimize_scalar
# ─────────────────────────────────────────────────────────────

class TestMinimize:
    @pytest.mark.unit
    def test_parabola_minimum(self, num_engine):
        """f(x) = x² + x + 2 的极小值在 x=-0.5, f=-0.25+2=1.75"""
        result = num_engine.minimize(lambda x: x[0]**2 + x[0] + 2, [0.0])
        assert result["success"] is True
        assert pytest.approx(result["x"][0], abs=1e-4) == -0.5
        assert pytest.approx(result["fun"], abs=1e-4) == 1.75

    @pytest.mark.unit
    def test_rosenbrock(self, num_engine):
        """Rosenbrock 函数全局最小值在 (1, 1)，值为 0"""
        def rosenbrock(x):
            return (1 - x[0])**2 + 100 * (x[1] - x[0]**2)**2
        result = num_engine.minimize(rosenbrock, [0.0, 0.0], method="BFGS")
        assert result["success"] is True
        assert pytest.approx(result["x"], abs=1e-3) == [1.0, 1.0]

    @pytest.mark.unit
    def test_returns_required_keys(self, num_engine):
        result = num_engine.minimize(lambda x: x[0]**2, [1.0])
        assert {"success", "x", "fun", "message"} <= result.keys()


class TestRootFinding:
    @pytest.mark.unit
    def test_quadratic_root(self, num_engine):
        """x² - 4 在 [0, 5] 内的根为 2"""
        root = num_engine.root_finding(lambda x: x**2 - 4, [0, 5])
        assert pytest.approx(root, abs=1e-8) == 2.0

    @pytest.mark.unit
    def test_trig_root(self, num_engine):
        """sin(x) 在 [2, 4] 内的根为 π"""
        root = num_engine.root_finding(np.sin, [2, 4])
        assert pytest.approx(root, abs=1e-8) == np.pi

    @pytest.mark.unit
    def test_invalid_bracket_raises(self, num_engine):
        """bracket 长度不为 2 时应抛出 NumEngineError"""
        with pytest.raises(NumEngineError, match="bracket"):
            num_engine.root_finding(lambda x: x, [0, 1, 2])


class TestMinimizeScalar:
    @pytest.mark.unit
    def test_bounded_minimum(self, num_engine):
        """f(x)=x² 在 [-1, 2] 内最小值为 0"""
        result = num_engine.minimize_scalar(lambda x: x**2, bounds=(-1.0, 2.0))
        assert pytest.approx(result["x"], abs=1e-6) == 0.0
        assert pytest.approx(result["fun"], abs=1e-12) == 0.0

    @pytest.mark.unit
    def test_unbounded_minimum(self, num_engine):
        """f(x)=(x-3)² 无界搜索最小值在 x=3"""
        result = num_engine.minimize_scalar(lambda x: (x - 3)**2)
        assert pytest.approx(result["x"], abs=1e-5) == 3.0


# ─────────────────────────────────────────────────────────────
# 信号处理模块 — FFT / IFFT / convolve / find_peaks
# ─────────────────────────────────────────────────────────────

class TestFFT:
    @pytest.mark.unit
    def test_fft_returns_keys(self, num_engine):
        result = num_engine.fft_transform([1, 0, -1, 0])
        assert "spectrum" in result and "frequencies" in result

    @pytest.mark.unit
    def test_fft_ifft_roundtrip(self, num_engine):
        """FFT → IFFT 应还原原信号"""
        original = [1.0, 2.0, 1.0, -1.0, 1.5]
        spectrum = num_engine.fft_transform(original)["spectrum"]
        recovered = num_engine.ifft_transform(spectrum).real
        np.testing.assert_array_almost_equal(original, recovered, decimal=10)

    @pytest.mark.unit
    def test_pure_sine_dominant_frequency(self, num_engine):
        """纯正弦信号的主频应对应其频率"""
        sample_rate = 100.0        # 100 Hz
        freq = 10.0                # 10 Hz 正弦波
        t = np.arange(0, 1, 1 / sample_rate)
        signal = np.sin(2 * np.pi * freq * t)

        result = num_engine.fft_transform(signal, sample_rate=sample_rate)
        magnitudes = np.abs(result["spectrum"])
        dominant_freq = np.abs(result["frequencies"][np.argmax(magnitudes)])
        assert pytest.approx(dominant_freq, abs=1.0) == freq


class TestConvolve:
    @pytest.mark.unit
    def test_identity_kernel(self, num_engine):
        """与 delta 函数卷积（'same' 模式）应还原原信号"""
        signal = [1.0, 2.0, 3.0, 4.0, 5.0]
        kernel = [0.0, 1.0, 0.0]
        result = num_engine.convolve(signal, kernel, mode="same")
        np.testing.assert_array_almost_equal(result, signal)

    @pytest.mark.unit
    def test_convolution_length_full(self, num_engine):
        """full 卷积长度应为 len(a) + len(b) - 1"""
        a, b = [1, 2, 3], [4, 5]
        result = num_engine.convolve(a, b, mode="full")
        assert len(result) == len(a) + len(b) - 1


class TestFindPeaks:
    @pytest.mark.unit
    def test_detects_peaks(self, num_engine):
        """简单峰值信号应能正确检测"""
        signal = [0, 1, 0, 2, 0, 1.5, 0]
        result = num_engine.find_peaks(signal)
        assert set(result["peak_indices"]) == {1, 3, 5}

    @pytest.mark.unit
    def test_height_threshold(self, num_engine):
        """设置高度阈值后应只返回超过阈值的峰"""
        signal = [0, 1, 0, 3, 0, 1.5, 0]
        result = num_engine.find_peaks(signal, height=2.0)
        assert 3 in result["peak_indices"]
        assert 1 not in result["peak_indices"]


# ─────────────────────────────────────────────────────────────
# 统计回归模块 — linear_regression / polynomial_fit / descriptive_stats
# ─────────────────────────────────────────────────────────────

class TestLinearRegression:
    @pytest.mark.unit
    def test_perfect_linear(self, num_engine):
        """完美线性关系 y=2x 应有 slope=2, intercept=0, r=1"""
        result = num_engine.linear_regression([1, 2, 3, 4], [2, 4, 6, 8])
        assert pytest.approx(result["slope"], abs=1e-10) == 2.0
        assert pytest.approx(result["intercept"], abs=1e-10) == 0.0
        assert pytest.approx(result["r_value"], abs=1e-10) == 1.0

    @pytest.mark.unit
    def test_returns_all_keys(self, num_engine):
        result = num_engine.linear_regression([1, 2, 3], [1, 2, 3])
        assert {"slope", "intercept", "r_value", "p_value", "std_err"} <= result.keys()


class TestPolynomialFit:
    @pytest.mark.unit
    def test_quadratic_fit(self, num_engine):
        """拟合 y = x² 的二次多项式系数应为 [1, 0, 0]"""
        x = np.linspace(-3, 3, 50)
        y = x**2
        result = num_engine.polynomial_fit(x, y, deg=2)
        coeffs = result["coefficients"]
        assert pytest.approx(coeffs[0], abs=1e-6) == 1.0   # x² 系数
        assert pytest.approx(coeffs[1], abs=1e-6) == 0.0   # x  系数
        assert pytest.approx(coeffs[2], abs=1e-6) == 0.0   # 常数项

    @pytest.mark.unit
    def test_returns_rank(self, num_engine):
        result = num_engine.polynomial_fit([1, 2, 3, 4], [1, 4, 9, 16], deg=2)
        assert "rank" in result


class TestDescriptiveStats:
    @pytest.mark.unit
    def test_known_values(self, num_engine):
        """对已知数据验证均值、中位数和标准差

        数据: [2, 4, 4, 4, 5, 5, 7, 9]
        - 均值 = 5.0
        - 中位数 = (4+5)/2 = 4.5
        - 样本标准差 (ddof=1) = sqrt(32/7) ≈ 2.1381  ← 注意：非总体标准差 2.0
        """
        import math
        data = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        result = num_engine.descriptive_stats(data)
        assert pytest.approx(result["mean"], abs=1e-10) == 5.0
        assert pytest.approx(result["median"], abs=1e-10) == 4.5
        assert pytest.approx(result["std"], rel=1e-8) == math.sqrt(32 / 7)

    @pytest.mark.unit
    def test_returns_all_keys(self, num_engine):
        result = num_engine.descriptive_stats([1, 2, 3, 4, 5])
        expected = {"mean", "median", "std", "variance",
                    "skewness", "kurtosis", "min", "max"}
        assert expected <= result.keys()

    @pytest.mark.unit
    def test_min_max(self, num_engine):
        result = num_engine.descriptive_stats([3, 1, 4, 1, 5, 9, 2, 6])
        assert result["min"] == 1.0
        assert result["max"] == 9.0
