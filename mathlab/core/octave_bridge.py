import re
import numpy as np
from typing import Any, Dict, Optional

from mathlab.core.num_engine import NumEngine


class OctaveBridgeError(Exception):
    """Octave 语法桥接器专属异常"""
    pass


class OctaveBridge:
    """
    MATLAB/Octave 语法桥接器

    将 Octave 代码字符串动态翻译为基于 NumPy 和 NumEngine 的 Python
    代码并在有状态的执行环境（self.env）中运行。

    核心机制：
        拦截 MATLAB 语法 → 词法替换 → 注入 NumEngine 环境执行

    设计原则：
        - 轻量渐进式正则替换，无需引入完整 AST 解析器
        - 通过 self.env 字典充当"工作区内存"，跨语句保持变量状态
        - 所有高级线性代数路由到 NumEngine，保持防腐层的一致性
    """

    def __init__(self, engine: Optional[NumEngine] = None):
        self.engine = engine or NumEngine()

        # ── 执行上下文 (用户工作区) ──────────────────────────────────────
        # 注意: eval/exec 共享此同一字典，确保赋值后变量对后续表达式可见。
        self.env: Dict[str, Any] = {
            "__builtins__": {},          # 沙箱：屏蔽内置危险函数
            "np": np,

            # ── 矩阵构建 ──────────────────────────────────────────────
            # MATLAB: zeros(m, n) / ones(m, n) 传入两个独立整数
            # NumPy:  np.zeros((m, n))          期望一个元组形状
            # 用 lambda 包装兼容两种调用约定
            "zeros":    lambda *a: np.zeros(a[0] if len(a) == 1 else a),
            "ones":     lambda *a: np.ones(a[0] if len(a) == 1 else a),
            "eye":      np.eye,
            "linspace": np.linspace,
            "arange":   np.arange,
            "rand":     lambda *a: np.random.rand(*a),
            "randn":    lambda *a: np.random.randn(*a),
            "diag":     np.diag,
            "reshape":  np.reshape,

            # ── 基础运算 ──────────────────────────────────────────────
            "abs":    np.abs,
            "sqrt":   np.sqrt,
            "exp":    np.exp,
            "log":    np.log,
            "log2":   np.log2,
            "log10":  np.log10,
            "floor":  np.floor,
            "ceil":   np.ceil,
            "round":  np.round,
            "mod":    np.mod,

            # ── 三角函数 ──────────────────────────────────────────────
            "sin":    np.sin,
            "cos":    np.cos,
            "tan":    np.tan,
            "asin":   np.arcsin,
            "acos":   np.arccos,
            "atan":   np.arctan,
            "atan2":  np.arctan2,

            # ── 矩阵属性 ──────────────────────────────────────────────
            "size":   lambda x, *a: np.shape(x) if not a else np.shape(x)[a[0] - 1],
            "numel":  np.size,
            "length": lambda x: max(np.shape(x)),
            "ndims":  np.ndim,
            "find":   lambda x: np.where(np.asarray(x).ravel())[0],

            # ── 聚合函数 ──────────────────────────────────────────────
            "max":    np.max,
            "min":    np.min,
            "sum":    np.sum,
            "prod":   np.prod,
            "cumsum": np.cumsum,
            "mean":   np.mean,
            "std":    np.std,
            "var":    np.var,
            "norm":   np.linalg.norm,
            "sort":   np.sort,
            "fliplr": np.fliplr,
            "flipud": np.flipud,

            # ── 常数 ──────────────────────────────────────────────────
            "pi": np.pi,
            "e":  np.e,
            "Inf": np.inf,
            "inf": np.inf,
            "NaN": np.nan,
            "nan": np.nan,
            "true":  True,
            "false": False,

            # ── 高级线性代数 (路由到 NumEngine) ──────────────────────
            "inv":  np.linalg.inv,
            "det":  np.linalg.det,
            "rank": self.engine.matrix_rank,
            "cond": self.engine.condition_number,
            "eig":  self.engine.eigenvalues,
            "svd":  self.engine.svd,
            "lu":   self.engine.lu_decomposition,
            "chol": self.engine.cholesky,

            # ── 优化 (路由到 NumEngine) ───────────────────────────────
            "fminsearch": lambda f, x0: self.engine.minimize(f, [x0]),
            "fzero":      lambda f, x0: self.engine.root_finding(f, x0),

            # ── 信号处理 (路由到 NumEngine) ───────────────────────────
            "fft":  lambda x: self.engine.fft_transform(x)["spectrum"],
            "ifft": lambda x: self.engine.ifft_transform(x),
            "conv": self.engine.convolve,

            # ── 统计回归 (路由到 NumEngine) ───────────────────────────
            "polyfit": lambda x, y, n: self.engine.polynomial_fit(x, y, deg=n)["coefficients"],
            "polyval": np.polyval,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 词法翻译器 (Lexical Translator)
    # ──────────────────────────────────────────────────────────────────────────

    def _translate_matrix_literals(self, code: str) -> str:
        """
        将 MATLAB 矩阵字面量翻译为 np.array(...)。

        规则：
          [1 2 3]        → np.array([1, 2, 3])      (一维行向量)
          [1; 2; 3]      → np.array([[1], [2], [3]]) (列向量)
          [1 2; 3 4]     → np.array([[1, 2], [3, 4]])
          [1, 2; 3, 4]   → np.array([[1, 2], [3, 4]])
          []             → np.array([])
        """
        def replacer(match):
            inner = match.group(1).strip()
            if not inner:
                return "np.array([])"

            has_semicolon = ";" in inner
            rows = inner.split(";")
            formatted_rows = []
            for row in rows:
                elements = [e.strip() for e in row.replace(",", " ").split() if e.strip()]
                formatted_rows.append("[" + ", ".join(elements) + "]")

            if not has_semicolon and len(formatted_rows) == 1:
                # 一维数组
                return "np.array(" + formatted_rows[0] + ")"

            # 二维数组（含列向量）
            return "np.array([" + ", ".join(formatted_rows) + "])"

        # 使用非贪婪匹配，但要避免匹配已被翻译的 np.array([...])
        # 策略：先做占位保护再替换
        protected: Dict[str, str] = {}
        counter = [0]

        def protect(m):
            key = f"__NPARRAY{counter[0]}__"
            protected[key] = m.group(0)
            counter[0] += 1
            return key

        # 保护已有的 np.array(...) 不被二次替换
        code = re.sub(r"np\.array\([^)]*\)", protect, code)
        # 替换 MATLAB 矩阵字面量
        code = re.sub(r"\[([^\[\]]*)\]", replacer, code)
        # 还原保护内容
        for key, val in protected.items():
            code = code.replace(key, val)

        return code

    def _translate_operators(self, code: str) -> str:
        """
        翻译 MATLAB 运算符到 Python/NumPy 等价形式。

        映射表：
          A'    → A.T          (共轭转置，此处近似为普通转置)
          .*    → *            (逐元素乘，NumPy 默认行为)
          ./    → /            (逐元素除)
          .^    → **           (逐元素幂)
          *     → @            (矩阵乘法)
          ^     → **           (标量/矩阵幂，标量场景与 Python 一致)
          ~=    → !=           (不等于)
          ~     → not          (逻辑非，仅处理简单场景)
          %...  → #...         (注释符)
        """
        # 1. 转置：变量名/右括号/右方括号后紧跟单引号
        code = re.sub(r"([A-Za-z0-9_\]\)]+)'", r"\1.T", code)

        # 2. 保护逐元素运算符（避免被后续步骤污染）
        code = code.replace(".*", "__DOT_MUL__")
        code = code.replace("./", "__DOT_DIV__")
        code = code.replace(".^", "__DOT_POW__")

        # 3. 矩阵乘法：* → @（MATLAB 默认 * 为矩阵乘）
        code = code.replace("*", "@")

        # 4. 幂运算：^ → **
        code = code.replace("^", "**")

        # 5. 还原逐元素运算符
        code = code.replace("__DOT_MUL__", "*")
        code = code.replace("__DOT_DIV__", "/")
        code = code.replace("__DOT_POW__", "**")

        # 6. 比较运算符
        code = code.replace("~=", "!=")
        code = re.sub(r"~(?!=)", "not ", code)

        # 7. 注释符：% → #
        code = re.sub(r"%", "#", code)

        return code

    def translate(self, code: str) -> str:
        """
        将一行 Octave/MATLAB 代码翻译为等价的 Python 代码字符串。

        翻译顺序（顺序敏感）：
            1. 矩阵字面量
            2. 运算符映射

        :param code: MATLAB/Octave 源代码字符串
        :returns: 等价的 Python 代码字符串
        """
        code = code.strip()
        code = self._translate_matrix_literals(code)
        code = self._translate_operators(code)
        return code

    # ──────────────────────────────────────────────────────────────────────────
    # 执行器 (Executor)
    # ──────────────────────────────────────────────────────────────────────────

    def evaluate(self, code: str) -> Any:
        """
        执行一条 Octave 语句并返回结果。

        支持：
          - 表达式：   ``A + B``  → 返回计算结果
          - 赋值语句：  ``A = [1 2; 3 4]`` → 更新 env，返回变量值
          - 多语句块：  用分号或换行分隔（目前仅支持单行）

        状态持久化：env 字典在每次调用间保持，变量跨语句可见。

        :param code: Octave 源代码
        :returns: 表达式求值结果，赋值语句返回被赋值的变量值，无结果返回 None
        :raises OctaveBridgeError: 翻译或执行失败时抛出
        """
        python_code = self.translate(code)

        try:
            # 尝试作为表达式 eval（eval/exec 共享 self.env，变量跨调用可见）
            result = eval(python_code, self.env, self.env)
            return result
        except SyntaxError:
            # 可能是赋值语句或含有多行的代码块，改用 exec
            try:
                exec(python_code, self.env, self.env)
                # 启发式：如果是简单赋值 "VAR = ..."，返回该变量
                stripped = python_code.strip()
                if "=" in stripped and not any(
                    op in stripped.split("=")[0]
                    for op in ["<", ">", "!", "="]
                ):
                    var_name = stripped.split("=")[0].strip()
                    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", var_name):
                        return self.env.get(var_name)
                return None
            except Exception as exc:
                raise OctaveBridgeError(
                    f"执行失败。\n"
                    f"  原始代码:   {code!r}\n"
                    f"  翻译后代码: {python_code!r}\n"
                    f"  错误信息:   {exc}"
                )
        except Exception as exc:
            raise OctaveBridgeError(
                f"执行失败。\n"
                f"  原始代码:   {code!r}\n"
                f"  翻译后代码: {python_code!r}\n"
                f"  错误信息:   {exc}"
            )

    def reset(self) -> None:
        """清空工作区（保留内置函数和常量，仅清除用户变量）"""
        user_vars = [k for k in self.env if not callable(self.env[k])
                     and k not in ("pi", "e", "Inf", "inf", "NaN", "nan",
                                   "true", "false", "np", "__builtins__")]
        for k in user_vars:
            del self.env[k]

    def workspace(self) -> Dict[str, Any]:
        """返回当前工作区中所有用户变量（过滤掉内置函数）"""
        return {
            k: v for k, v in self.env.items()
            if not k.startswith("__") and not callable(v)
            and k not in ("np",)
        }
