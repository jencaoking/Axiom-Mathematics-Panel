"""
OctaveBridge 单元测试套件

运行方式:
    pytest mathlab/tests/test_octave_bridge.py -v
"""

import math
import numpy as np
import pytest

from mathlab.core.octave_bridge import OctaveBridge, OctaveBridgeError


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def bridge():
    """每个测试用例获得一个全新的 OctaveBridge 实例（隔离工作区）"""
    return OctaveBridge()


# ─────────────────────────────────────────────────────────────
# 矩阵字面量翻译 (Matrix Literal Translation)
# ─────────────────────────────────────────────────────────────

class TestMatrixLiterals:
    def test_1d_row_vector_spaces(self, bridge):
        """[1 2 3] → np.array([1, 2, 3])"""
        assert bridge.translate("[1 2 3]") == "np.array([1, 2, 3])"

    def test_1d_row_vector_commas(self, bridge):
        """[1, 2, 3] → np.array([1, 2, 3])"""
        assert bridge.translate("[1, 2, 3]") == "np.array([1, 2, 3])"

    def test_2d_matrix(self, bridge):
        """[1 2; 3 4] → np.array([[1, 2], [3, 4]])"""
        assert bridge.translate("[1 2; 3 4]") == "np.array([[1, 2], [3, 4]])"

    def test_2d_matrix_with_commas(self, bridge):
        """[1, 2; 3, 4] → np.array([[1, 2], [3, 4]])"""
        assert bridge.translate("[1, 2; 3, 4]") == "np.array([[1, 2], [3, 4]])"

    def test_column_vector(self, bridge):
        """[1; 2; 3] → np.array([[1], [2], [3]])"""
        assert bridge.translate("[1; 2; 3]") == "np.array([[1], [2], [3]])"

    def test_empty_matrix(self, bridge):
        """[] → np.array([])"""
        assert bridge.translate("[]") == "np.array([])"

    def test_evaluate_matrix(self, bridge):
        """矩阵字面量求值应返回正确的 ndarray"""
        result = bridge.evaluate("[1 2; 3 4]")
        np.testing.assert_array_equal(result, np.array([[1, 2], [3, 4]]))

    def test_evaluate_row_vector(self, bridge):
        result = bridge.evaluate("[1 2 3]")
        np.testing.assert_array_equal(result, np.array([1, 2, 3]))


# ─────────────────────────────────────────────────────────────
# 运算符翻译 (Operator Translation)
# ─────────────────────────────────────────────────────────────

class TestOperatorTranslation:
    def test_matrix_multiply_translated(self, bridge):
        """* 应翻译为 @（矩阵乘法）"""
        assert "@" in bridge.translate("A * B")

    def test_elementwise_mul_preserved(self, bridge):
        """.*（逐元素乘）应翻译为 *"""
        translated = bridge.translate("A .* B")
        assert "*" in translated
        assert "@" not in translated

    def test_elementwise_div(self, bridge):
        """./（逐元素除）应翻译为 /"""
        translated = bridge.translate("A ./ B")
        assert "/" in translated

    def test_elementwise_pow(self, bridge):
        """.^（逐元素幂）应翻译为 **"""
        translated = bridge.translate("A .^ 2")
        assert "**" in translated

    def test_matrix_pow(self, bridge):
        """^（矩阵幂）应翻译为 **"""
        translated = bridge.translate("x ^ 2")
        assert "**" in translated

    def test_transpose(self, bridge):
        """A' 应翻译为 A.T"""
        assert bridge.translate("A'") == "A.T"

    def test_not_equal(self, bridge):
        """~= 应翻译为 !="""
        assert "!=" in bridge.translate("a ~= b")

    def test_comment(self, bridge):
        """% 应翻译为 #（注释符）"""
        assert "#" in bridge.translate("x = 1 % comment")


# ─────────────────────────────────────────────────────────────
# 矩阵运算求值 (Matrix Operations Evaluation)
# ─────────────────────────────────────────────────────────────

class TestMatrixOperations:
    def test_matrix_multiplication(self, bridge):
        """A * B → 矩阵乘法结果正确"""
        bridge.evaluate("A = [1 2; 3 4]")
        bridge.evaluate("B = [2 0; 0 2]")
        result = bridge.evaluate("A * B")
        expected = np.array([[1, 2], [3, 4]]) @ np.array([[2, 0], [0, 2]])
        np.testing.assert_array_equal(result, expected)

    def test_elementwise_multiplication(self, bridge):
        """A .* B → 逐元素乘法结果正确"""
        bridge.evaluate("A = [1 2; 3 4]")
        bridge.evaluate("B = [2 0; 0 2]")
        result = bridge.evaluate("A .* B")
        expected = np.array([[2, 0], [0, 8]])
        np.testing.assert_array_equal(result, expected)

    def test_transpose(self, bridge):
        """A' → 转置结果正确"""
        bridge.evaluate("A = [1 2; 3 4]")
        result = bridge.evaluate("A'")
        np.testing.assert_array_equal(result, np.array([[1, 3], [2, 4]]))

    def test_scalar_operations(self, bridge):
        """标量运算：x ^ 2 → x**2"""
        bridge.evaluate("x = 3")
        result = bridge.evaluate("x ^ 2")
        assert result == 9

    def test_elementwise_power(self, bridge):
        """v .^ 2 → 逐元素平方"""
        bridge.evaluate("v = [1 2 3]")
        result = bridge.evaluate("v .^ 2")
        np.testing.assert_array_equal(result, np.array([1, 4, 9]))

    def test_addition(self, bridge):
        """矩阵加法保持不变"""
        result = bridge.evaluate("[1 2] + [3 4]")
        np.testing.assert_array_equal(result, np.array([4, 6]))


# ─────────────────────────────────────────────────────────────
# 状态保持 (Stateful Environment)
# ─────────────────────────────────────────────────────────────

class TestStatefulEnvironment:
    def test_variable_persists_across_calls(self, bridge):
        """赋值后，变量在后续 evaluate 中可见"""
        bridge.evaluate("x = 42")
        result = bridge.evaluate("x")
        assert result == 42

    def test_multiple_assignments(self, bridge):
        """多次赋值后，所有变量均可访问"""
        bridge.evaluate("A = [1 2; 3 4]")
        bridge.evaluate("B = [5 6; 7 8]")
        bridge.evaluate("C = A + B")
        result = bridge.evaluate("C")
        expected = np.array([[6, 8], [10, 12]])
        np.testing.assert_array_equal(result, expected)

    def test_assignment_returns_value(self, bridge):
        """赋值语句应返回被赋值的变量值"""
        result = bridge.evaluate("M = [1 2; 3 4]")
        assert result is not None
        np.testing.assert_array_equal(result, np.array([[1, 2], [3, 4]]))

    def test_workspace(self, bridge):
        """workspace() 应列出用户变量"""
        bridge.evaluate("alpha = 3.14")
        ws = bridge.workspace()
        assert "alpha" in ws
        assert pytest.approx(ws["alpha"]) == 3.14

    def test_reset_clears_user_vars(self, bridge):
        """reset() 应清除用户变量，保留内置常量"""
        bridge.evaluate("myvar = 99")
        bridge.reset()
        ws = bridge.workspace()
        assert "myvar" not in ws
        # pi 仍然存在
        result = bridge.evaluate("pi")
        assert pytest.approx(result) == math.pi


# ─────────────────────────────────────────────────────────────
# 内置函数映射 (Built-in Function Mapping)
# ─────────────────────────────────────────────────────────────

class TestBuiltinFunctions:
    def test_zeros(self, bridge):
        result = bridge.evaluate("zeros(2, 3)")
        np.testing.assert_array_equal(result, np.zeros((2, 3)))

    def test_ones(self, bridge):
        result = bridge.evaluate("ones(2, 2)")
        np.testing.assert_array_equal(result, np.ones((2, 2)))

    def test_eye(self, bridge):
        result = bridge.evaluate("eye(3)")
        np.testing.assert_array_equal(result, np.eye(3))

    def test_linspace(self, bridge):
        """linspace(0, 10, 5) → [0, 2.5, 5, 7.5, 10]"""
        bridge.evaluate("v = linspace(0, 10, 5)")
        result = bridge.evaluate("sum(v)")
        assert pytest.approx(result) == 25.0

    def test_sum(self, bridge):
        result = bridge.evaluate("sum([1 2 3 4 5])")
        assert result == 15

    def test_max(self, bridge):
        result = bridge.evaluate("max([3 1 4 1 5 9])")
        assert result == 9

    def test_min(self, bridge):
        result = bridge.evaluate("min([3 1 4 1 5 9])")
        assert result == 1

    def test_abs(self, bridge):
        result = bridge.evaluate("abs(-5)")
        assert result == 5

    def test_sqrt(self, bridge):
        result = bridge.evaluate("sqrt(16)")
        assert pytest.approx(result) == 4.0

    def test_sin_cos(self, bridge):
        result = bridge.evaluate("sin(pi)")
        assert pytest.approx(result, abs=1e-10) == 0.0

    def test_pi_constant(self, bridge):
        result = bridge.evaluate("pi")
        assert pytest.approx(result) == math.pi

    def test_mean(self, bridge):
        result = bridge.evaluate("mean([1 2 3 4 5])")
        assert pytest.approx(result) == 3.0


# ─────────────────────────────────────────────────────────────
# NumEngine 高级路由 (NumEngine Integration)
# ─────────────────────────────────────────────────────────────

class TestNumEngineIntegration:
    def test_eig(self, bridge):
        """eig() 应路由到 NumEngine.eigenvalues，返回字典"""
        bridge.evaluate("M = [2 0; 0 3]")
        result = bridge.evaluate("eig(M)")
        assert "eigenvalues" in result
        evals = np.sort(np.real(result["eigenvalues"]))
        assert pytest.approx(evals[0], abs=1e-10) == 2.0
        assert pytest.approx(evals[1], abs=1e-10) == 3.0

    def test_svd(self, bridge):
        """svd() 应路由到 NumEngine.svd，奇异值非负"""
        bridge.evaluate("M = [1 2; 3 4; 5 6]")
        result = bridge.evaluate("svd(M)")
        assert "S" in result
        assert np.all(result["S"] >= 0)

    def test_fft(self, bridge):
        """fft() 应返回频谱数组"""
        result = bridge.evaluate("fft([1 0 -1 0])")
        assert result is not None
        assert len(result) == 4

    def test_ifft(self, bridge):
        """fft → ifft 应可逆"""
        bridge.evaluate("sig = [1.0 2.0 3.0 4.0]")
        bridge.evaluate("S = fft(sig)")
        recovered = bridge.evaluate("ifft(S)")
        np.testing.assert_array_almost_equal(
            np.array([1.0, 2.0, 3.0, 4.0]),
            recovered.real,
            decimal=10,
        )

    def test_polyfit(self, bridge):
        """polyfit 应路由到 NumEngine.polynomial_fit，返回系数数组"""
        bridge.evaluate("x = [1 2 3 4]")
        bridge.evaluate("y = [1 4 9 16]")
        coeffs = bridge.evaluate("polyfit(x, y, 2)")
        # y = x² → 系数应约为 [1, 0, 0]
        assert pytest.approx(coeffs[0], abs=1e-6) == 1.0

    def test_inv(self, bridge):
        """inv() 应通过 np.linalg.inv 返回正确逆矩阵"""
        bridge.evaluate("A = [2 0; 0 4]")
        result = bridge.evaluate("inv(A)")
        expected = np.array([[0.5, 0.0], [0.0, 0.25]])
        np.testing.assert_array_almost_equal(result, expected)


# ─────────────────────────────────────────────────────────────
# 错误处理 (Error Handling)
# ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_invalid_code_raises(self, bridge):
        """无法执行的代码应抛出 OctaveBridgeError"""
        with pytest.raises(OctaveBridgeError):
            bridge.evaluate("this is not valid code !!!")

    def test_undefined_variable_raises(self, bridge):
        """访问未定义变量应抛出 OctaveBridgeError"""
        with pytest.raises(OctaveBridgeError):
            bridge.evaluate("undefined_var_xyz + 1")
