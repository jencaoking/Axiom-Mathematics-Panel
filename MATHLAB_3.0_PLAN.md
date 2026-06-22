# MathLab 3.0 开发计划 (代号: GeoGebra-Infinity)

> **核心理念**：深度集成 GeoGebra 开源技术栈，实现从"Mini GeoGebra"到"完整 GeoGebra 级"的功能跨越，引入 Giac CAS 内核、GeoGebra 命令兼容、步进式求解器，打造真正的一体化数学实验室。

---

## 1. 总体架构升级

### 从 2.6 到 3.0 的演进路径

```
2.6 (已完成)                          3.0 (本计划)
───────────────────────────────────────────────────────────────────
Mini GeoGebra 几何引擎    ──→    完整 GeoGebra 约束求解器
SymPy 单一 CAS           ──→    Giac + SymPy 双引擎 CAS 总线
独立步进式求解器          ──→    GeoGebra Solver-Engine 集成
3D 仅可视化               ──→    GeoGebra 3D 内核集成
无 GeoGebra 命令兼容     ──→    GeoGebra 命令解析器
离线单机                 ──→    Web 同步 + 多人协作
```

### 3.0 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         用户界面层 (UI Layer)                            │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────┐│
│  │ GeoGebra   │ │ Giac CAS    │ │ Step-by-Step│ │ 3D GeoGebra│ │协作  ││
│  │ 画板 Pro   │ │ 终端        │ │ 求解面板   │ │ 内核       │ │面板  ││
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └──────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                        业务逻辑层 (Core Layer)                            │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │ GeoGebraEngine Pro │ Giac CAS Bus │ Solver-Engine │ 协作 Engine   ││
│  │ (完整约束求解)      │ (Giac+SymPy) │ (步进求解)   │ (WebSocket)  ││
│  └────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                        GeoGebra 开源集成层                               │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │ giac-wasm (CAS) │ solver-engine (步进) │ GeoGebra Commands       ││
│  │ (编译为 WASM)   │ (Kotlin → Python)    │ (命令解析器)            ││
│  └────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                         安全隔离层 (Sandbox Layer)                       │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │  Python REPL  │  Giac WASM  │  GeoGebra Engine  │  Plugin VM      ││
│  └────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                         数据与协作层 (Data Layer)                        │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │ 项目文件 (.ggb 兼容) │ 资源库 │ WebSocket 协作 │ 云端同步       ││
│  └────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. GeoGebra 开源代码研究总结

### 2.1 可用的开源仓库

| 仓库 | 语言 | Stars | 功能 | 集成价值 |
|------|------|-------|------|----------|
| [geogebra/geogebra](https://github.com/geogebra/geogebra) | Java 95% | 2.2k | 主应用程序 | 高 (架构参考) |
| [geogebra/giac](https://github.com/geogebra/giac) | C++ 78% | 69 | CAS 内核 | **极高 (直接集成)** |
| [geogebra/solver-engine](https://github.com/geogebra/solver-engine) | Kotlin | 18 | 步进求解器 | **高 (教育功能)** |
| [geogebra/manual](https://github.com/geogebra/manual) | JS | 14 | 命令文档 | 中 (参考实现) |

### 2.2 Giac CAS 内核详解

**Giac** 是 GeoGebra 内置的符号计算引擎，特性包括：

- **高性能多项式运算**: Gröbner 基、多项式因式分解
- **符号积分**: 比 SymPy 更成熟 (尤其特殊函数)
- **几何代数**: 几何定理证明
- **WebAssembly 支持**: 可在浏览器中运行
- **NodeJS 绑定**: nodegiac 可用于 Python 桥接

**集成方案**:

```python
# 方案 A: Giac WASM (推荐)
# 编译 giac 为 WebAssembly，在 Pyodide 或 PyScript 环境中运行
import subprocess
result = subprocess.run(['node', 'nodegiac.js', '-c', 'factor(x^10-1)'], capture_output=True)

# 方案 B: Giac Python 绑定
# Bernard Parisse 的 giacpy (需编译 C++ 源码)
# 方案 C: HTTP 服务
# Giac 作为独立服务，通过 HTTP API 调用
```

### 2.3 Solver-Engine 详解

**Solver-Engine** 是 GeoGebra 的步进式求解器 (Kotlin)，功能包括：

- 方程的逐步求解过程展示
- 每一步的数学推导说明
- 支持代数、微积分等多种题型

**集成方案**:

```python
# 将 Kotlin 代码转译为 Python，或通过 PyJNIus 调用
# 也可直接用 Python 重写其算法逻辑 (BSD 许可证允许)
class StepByStepSolver:
    def solve_equation(self, equation: str, variable: str):
        """模仿 Solver-Engine 的逐步求解"""
        steps = []
        # Step 1: 移项
        steps.append(Step("移项", f"{equation} → ..."))
        # Step 2: 合并同类项
        steps.append(Step("合并", "..."))
        # Step 3: 求根
        steps.append(Step("求根", "..."))
        return Solution(steps=steps)
```

---

## 3. 阶段 1 — GeoGebraEngine Pro：完整约束求解器

> **目标**: 将现有基础约束求解器升级为 GeoGebra 级的完整约束系统

### 3.1 约束类型扩展

**参考**: GeoGebra 50+ 种约束 → 当前 MathLab ~10 种

```python
class ConstraintType(Enum):
    """扩展约束类型 (借鉴 GeoGebra)"""

    # ── 基础位置约束 ──
    FIXED = "fixed"               # 固定点 (坐标锁定)
    MIDPOINT = "midpoint"         # 中点
    CENTROID = "centroid"         # 重心
    CIRCUMCENTER = "circumcenter" # 外心
    INCENTER = "incenter"         # 内心

    # ── 距离/半径约束 ──
    DISTANCE = "distance"         # 固定距离
    RADIUS = "radius"            # 固定半径
    EQUAL_LENGTH = "equal_length" # 等长

    # ── 角度约束 ──
    ANGLE = "angle"              # 固定角度
    EQUAL_ANGLE = "equal_angle"  # 等角
    ANGLE_BISECTOR = "angle_bisector" # 角平分线

    # ── 关系约束 ──
    PARALLEL = "parallel"        # 平行
    PERPENDICULAR = "perpendicular" # 垂直
    COLLINEAR = "collinear"      # 共线
    CONCYCLIC = "concyclic"      # 共圆
    CONGRUENT = "congruent"      # 全等

    # ── 位置约束 ──
    ON_LINE = "on_line"          # 在直线上
    ON_CIRCLE = "on_circle"      # 在圆上
    ON_CURVE = "on_curve"        # 在曲线上
    ON_BISECTOR = "on_bisector"  # 在角平分线上

    # ── 相切约束 ──
    TANGENT = "tangent"          # 相切
    INCIRCLE = "incircle"        # 内切圆
    EXCIRCLE = "excircle"        # 外切圆

    # ── 高级约束 ──
    SYMMETRIC = "symmetric"      # 对称
    SIMILAR = "similar"          # 相似
    HARMONIC = "harmonic"        # 调和分割

    # ── 变换约束 ──
    REFLECTION = "reflection"    # 反射
    ROTATION = "rotation"        # 旋转
    TRANSLATION = "translation"  # 平移
    DILATION = "dilation"       # 缩放
    HOMOTHETY = "homothety"      # 位似
```

### 3.2 增强的求解器架构

```python
class GeoGebraConstraintSolver:
    """
    GeoGebra 级约束求解器

    借鉴内容:
    1. GeoGebra 的数值迭代策略 (Newton-Raphson + Levenberg-Marquardt)
    2. GeoGebra 的欠约束/过约束检测
    3. GeoGebra 的自由度计算
    """

    def __init__(self, tolerance=1e-9, max_iterations=200):
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        self.constraints: List[Constraint] = []
        self.variables: List[GeoVariable] = []
        self.jacobian = None

    def add_constraint(self, ctype: ConstraintType, *args, **kwargs) -> str:
        """添加约束，返回约束 ID"""
        ...

    def remove_constraint(self, constraint_id: str) -> bool:
        """移除约束"""
        ...

    def solve(self) -> SolveResult:
        """
        求解所有约束
        算法: 自适应 Newton-Raphson
        - 约束少时用纯 Newton-Raphson (快速收敛)
        - 约束多/病态时用 Levenberg-Marquardt (稳定)
        """
        # 构造 Jacobian 矩阵
        # 迭代求解
        # 检测收敛/发散/过约束
        ...

    def analyze_degrees_of_freedom(self) -> DoFAnalysis:
        """
        分析自由度 (借鉴 GeoGebra 的 DoF 算法)
        - 自由: 用户可拖动
        - 半自由: 沿路径约束
        - 固定: 完全约束
        """
        ...

    def check_consistency(self) -> ConsistencyResult:
        """检测约束一致性 (过约束/欠约束/冲突)"""
        ...
```

### 3.3 轨迹与包络线增强

```python
class LocusSystem:
    """
    轨迹系统 (借鉴 GeoGebra 的 Locus 命令)

    GeoGebra 支持:
    1. 参数轨迹 (tracer along path)
    2. 包络线 (envelope of family)
    3. 轨迹显示 (trace)
    """

    def create_locus(self, tracer_id: str, driver_id: str,
                     samples: int = 500) -> str:
        """创建参数轨迹"""

    def create_envelope(self, family_expr: str, param_var: str,
                        param_range: Tuple[float, float]) -> str:
        """创建曲线族包络线"""

    def create_implicit_curve(self, implicit_eq: str,
                              x_range: Tuple, y_range: Tuple) -> str:
        """创建隐函数轨迹 (由方程 F(x,y)=0 定义)"""
```

### 3.4 度量工具

```python
class MeasurementTools:
    """度量工具 (借鉴 GeoGebra 的测量功能)"""

    # ── 基本度量 ──
    def distance(self, p1_id: str, p2_id: str) -> float
    def length(self, segment_id: str) -> float
    def angle(self, p1_id: str, vertex_id: str, p3_id: str) -> float
    def area(self, polygon_id: str) -> float
    def perimeter(self, polygon_id: str) -> float

    # ── 高级度量 ──
    def slope(self, line_id: str) -> float
    def curvature(self, curve_id: str, param: float) -> float
    def arc_length(self, arc_id: str) -> float
    def arc_area(self, arc_id: str) -> float

    # ── 坐标变换 ──
    def cartesian_to_polar(self, x: float, y: float) -> Tuple[float, float]
    def polar_to_cartesian(self, r: float, theta: float) -> Tuple[float, float]

    # ── 几何不变量 ──
    def directed_angle(self, p1: str, vertex: str, p2: str) -> float
    def cross_ratio(self, p1: str, p2: str, p3: str, p4: str) -> float
```

### 里程碑

| # | 里程碑 | 交付物 | 成功标准 |
|---|--------|--------|----------|
| 1.1 | 约束类型扩展 | `core/geogebra_engine.py` | 30+ 约束类型 |
| 1.2 | 增强求解器 | `core/constraint_solver.py` | Newton-Raphson + LM 混合 |
| 1.3 | 轨迹系统 | `core/locus_system.py` | 参数轨迹 + 包络线 |
| 1.4 | 度量工具 | `core/measurement.py` | 距离/角度/面积/弧长 |

---

## 4. 阶段 2 — Giac CAS 集成：双引擎符号计算

> **目标**: 集成 GeoGebra 的 Giac CAS 内核，实现高性能符号计算

### 4.1 Giac WASM 集成

**方案**: 将 Giac 编译为 WebAssembly，在 Python 中通过 Pyodide 或直接调用

```python
class GiacProvider:
    """
    Giac CAS 提供者 (集成 GeoGebra 的 giac)

    Giac 核心优势:
    1. 高性能多项式运算 (比 SymPy 快 10-100x)
    2. 成熟的符号积分算法
    3. 几何定理证明能力
    4. Giac/XCAS 语法兼容
    """

    def __init__(self):
        self.wasm_module = None
        self._initialize_giac()

    def _initialize_giac(self):
        """初始化 Giac WASM 模块"""
        # 方案 A: 使用预编译的 giac.js
        # from pyodide import loadPyodide
        # self.pyodide = loadPyodide()
        # self.pyodide.runPythonAsync("from giac import *")

        # 方案 B: HTTP 服务 (推荐用于桌面端)
        # self.client = GiacHttpClient('http://localhost:5173/giac')

        # 方案 C: subprocess 调用本地 giac
        self.giac_path = find_giac_executable()

    def _call_giac(self, cmd: str) -> str:
        """调用 Giac 执行命令"""
        result = subprocess.run(
            [self.giac_path, '-q', '-c', cmd],
            capture_output=True, text=True
        )
        return result.stdout.strip()

    # ── 核心 CAS 功能 ──
    def evaluate(self, expr: str) -> CASResult:
        """通用求值"""
        output = self._call_giac(expr)
        return CASResult(success=True, result=output, engine='giac')

    def simplify(self, expr: str) -> CASResult:
        """化简"""
        return self.evaluate(f'simplify({expr})')

    def factor(self, expr: str) -> CASResult:
        """因式分解"""
        return self.evaluate(f'factor({expr})')

    def expand(self, expr: str) -> CASResult:
        """展开"""
        return self.evaluate(f'expand({expr})')

    def solve(self, equation: str, variable: str) -> CASResult:
        """方程求解"""
        result = self._call_giac(f'solve({equation},{variable})')
        return CASResult(success=True, result=result)

    def integrate(self, expr: str, variable: str) -> CASResult:
        """符号积分 (Giac 优势项目)"""
        result = self._call_giac(f'integrate({expr},{variable})')
        return CASResult(success=True, result=result)

    def differentiate(self, expr: str, variable: str) -> CASResult:
        """求导"""
        return self.evaluate(f'diff({expr},{variable})')

    # ── 高级 CAS 功能 ──
    def groebner_basis(self, polynomials: List[str],
                       vars: List[str]) -> CASResult:
        """Gröbner 基 (Giac 优势项目)"""
        poly_str = ','.join(polynomials)
        var_str = ','.join(vars)
        result = self._call_giac(f'gbasis([{poly_str}],[{var_str}])')
        return CASResult(success=True, result=result)

    def factorize_polynomial(self, poly: str) -> CASResult:
        """多项式因式分解"""
        return self.evaluate(f'factor({poly})')

    def partial_fraction(self, expr: str, variable: str) -> CASResult:
        """部分分式分解"""
        return self.evaluate(f'partfrac({expr},{variable})')

    def series_expansion(self, expr: str, variable: str,
                         point: float, order: int) -> CASResult:
        """级数展开"""
        return self.evaluate(f'series({expr},{variable}={point}),{order})')

    def limit(self, expr: str, variable: str,
              direction: str = '+') -> CASResult:
        """极限"""
        direction_str = '+' if direction == '+' else '-'
        return self.evaluate(f'limit({expr},{variable},{point},{direction_str})')
```

### 4.2 CAS 总线双引擎架构

```python
class CASBusV2:
    """
    CAS 总线 v2 (Giac + SymPy 双引擎)

    引擎选择策略:
    - Giac 优先: 因式分解、Gröbner 基、特殊函数积分
    - SymPy 优先: 矩阵运算、简单化简、级数
    - 自动降级: Giac 失败时用 SymPy
    """

    ENGINES = {
        'giac': GiacProvider,      # 主引擎 (高性能)
        'sympy': SymPyProvider,     # 备用引擎 (通用)
    }

    ROUTING_TABLE = {
        # 符号计算: Giac 优先
        'integrate':       ['giac', 'sympy'],    # 积分
        'factor':          ['giac', 'sympy'],     # 因式分解
        'groebner':        ['giac', 'sympy'],    # Gröbner 基
        'factor_polynomial': ['giac'],           # 多项式因式分解
        'partial_fraction': ['giac', 'sympy'],   # 部分分式

        # 简单计算: SymPy 优先
        'simplify':        ['sympy', 'giac'],     # 化简
        'expand':          ['sympy', 'giac'],     # 展开
        'solve':           ['sympy', 'giac'],     # 求解
        'differentiate':   ['sympy'],            # 求导
        'limit':           ['sympy', 'giac'],     # 极限

        # 线性代数: SymPy
        'matrix_multiply': ['sympy'],
        'matrix_inverse':  ['sympy'],
        'eigenvalues':     ['sympy'],
        'svd':             ['sympy'],
    }

    def compute(self, task_type: str, expression: str,
                **kwargs) -> CASResult:
        """自动路由到最优引擎"""
        engines = self.ROUTING_TABLE.get(task_type, ['sympy'])

        for engine_name in engines:
            engine = self.ENGINES[engine_name]()
            try:
                result = engine.compute(task_type, expression, **kwargs)
                if result.success:
                    result.engine = engine_name
                    return result
            except Exception as e:
                continue

        return CASResult(success=False, error=f"所有引擎均失败")
```

### 4.3 Giac 命令兼容层

```python
class GiacCommandCompat:
    """
    Giac/XCAS 命令兼容层

    让用户可以用 Giac 语法在 MathLab 中计算
    """

    # ── 常用命令映射 ──
    COMMAND_MAP = {
        # 代数
        'factor': 'factor',
        'expand': 'expand',
        'simplify': 'simplify',
        'normal': 'normal',          # 有理函数化简
        'partfrac': 'partfrac',      # 部分分式
        'divide': 'quo',             # 多项式除法
        'gcd': 'gcd',                # 最大公因式

        # 求解
        'solve': 'solve',
        'desolve': 'desolve',        # 微分方程求解
        'rsolve': 'rsolve',          # 递推关系求解

        # 分析
        'integrate': 'integrate',
        'diff': 'diff',
        'limit': 'limit',
        'series': 'series',
        'taylor': 'taylor',

        # 线性代数
        'inv': 'inv',
        'transpose': 'transpose',
        'det': 'det',
        'ker': 'ker',
        'rank': 'rank',
        'eigenvalues': 'eigenvalues',
        'jordan': 'jordan',
    }

    def execute(self, command: str) -> CASResult:
        """执行 Giac 命令"""
        parsed = self._parse_command(command)
        func = self.COMMAND_MAP.get(parsed['cmd'])
        if func:
            return getattr(self.giac, func)(*parsed['args'])
        return self.giac.evaluate(command)
```

### 里程碑

| # | 里程碑 | 交付物 | 成功标准 |
|---|--------|--------|----------|
| 2.1 | Giac 集成 | `core/giac_provider.py` | 基本 CAS 功能 |
| 2.2 | CAS 总线 v2 | `core/cas_bus_v2.py` | 双引擎自动路由 |
| 2.3 | Giac 命令兼容 | `core/giac_compat.py` | 20+ Giac 命令 |
| 2.4 | 性能基准 | `tests/benchmark_cas.py` | Giac vs SymPy 对比 |

---

## 5. 阶段 3 — Solver-Engine 集成：步进式求解器

> **目标**: 集成 GeoGebra 的 Solver-Engine，实现教育友好的步进式求解

### 5.1 步进式求解器核心

```python
class StepByStepSolver:
    """
    步进式求解器 (集成 GeoGebra Solver-Engine)

    功能:
    1. 方程/方程组的逐步求解
    2. 每一步的数学推导说明
    3. 支持多种解题策略
    """

    class Step:
        """求解步骤"""
        def __init__(self, title: str, expression: str, explanation: str):
            self.title = title
            self.expression = expression
            self.explanation = explanation

    class Solution:
        """完整解答"""
        def __init__(self, steps: List[Step], result: str):
            self.steps = steps
            self.result = result

    # ── 方程求解 ──
    def solve_linear(self, equation: str, variable: str) -> Solution:
        """一元一次方程"""
        steps = [
            Step("去分母", "方程两边乘以分母的最小公倍数", "..."),
            Step("去括号", "分配律展开", "..."),
            Step("移项", "将含变量项移到左边，常数项移到右边", "..."),
            Step("合并同类项", "合并左边变量项，合并右边常数项", "..."),
            Step("系数化为1", "方程两边除以变量系数", "..."),
        ]
        return Solution(steps=steps, result="...")

    def solve_quadratic(self, equation: str, variable: str) -> Solution:
        """一元二次方程"""
        steps = [
            Step("化为标准形式", "ax² + bx + c = 0", "..."),
            Step("判断是否有解", "Δ = b² - 4ac", "..."),
            Step("计算判别式", "Δ = ...", "..."),
            Step("应用求根公式", "x = (-b ± √Δ) / 2a", "..."),
        ]
        return Solution(steps=steps, result="...")

    def solve_system_linear(self, equations: List[str],
                            variables: List[str]) -> Solution:
        """线性方程组 (高斯消元)"""
        ...

    # ── 因式分解 ──
    def factor_difference_of_squares(self, expr: str) -> Solution:
        """平方差公式因式分解"""
        ...

    def factor_trinomial(self, expr: str) -> Solution:
        """完全平方/十字相乘法因式分解"""
        ...

    # ── 分式化简 ──
    def simplify_rational(self, expr: str) -> Solution:
        """分式化简"""
        ...
```

### 5.2 微积分步进求解

```python
class CalculusStepByStep:
    """微积分步进求解"""

    def differentiate(self, expr: str, variable: str) -> Solution:
        """求导 (链式法则每步展示)"""
        steps = [
            Step("识别外函数和内函数", "y = f(g(x))", "..."),
            Step("求外函数导数", "f'(u) = ...", "..."),
            Step("求内函数导数", "g'(x) = ...", "..."),
            Step("应用链式法则", "f'(g(x))·g'(x)", "..."),
        ]
        return Solution(steps=steps, result="...")

    def integrate_polynomial(self, expr: str, variable: str) -> Solution:
        """多项式积分"""
        steps = [
            Step("识别各项", "分离各单项式", "..."),
            Step("应用幂法则", "∫ xⁿ dx = xⁿ⁺¹/(n+1)", "..."),
            Step("逐项积分", "对每项应用法则", "..."),
            Step("加常数项", "+ C", "..."),
        ]
        return Solution(steps=steps, result="...")

    def integrate_rational(self, expr: str, variable: str) -> Solution:
        """有理函数积分"""
        steps = [
            Step("检查是否为真分式", "分子次数 < 分母次数", "..."),
            Step("如有假分式先做多项式除法", "...", "..."),
            Step("分解部分分式", "...", "..."),
            Step("逐项积分", "...", "..."),
        ]
        return Solution(steps=steps, result="...")
```

### 5.3 求解策略引擎

```python
class SolverStrategy:
    """
    求解策略引擎

    根据问题类型自动选择最优求解策略
    """

    STRATEGIES = {
        'linear_equation': solve_linear,
        'quadratic_equation': solve_quadratic,
        'system_linear': solve_system_linear,
        'polynomial_factor': factor_polynomial,
        'rational_simplify': simplify_rational,
        'polynomial_divide': polynomial_division,
        'derivative': differentiate,
        'integral_polynomial': integrate_polynomial,
        'integral_rational': integrate_rational,
    }

    def auto_solve(self, problem: str) -> Solution:
        """自动识别问题类型并求解"""
        problem_type = self._classify_problem(problem)
        strategy = self.STRATEGIES.get(problem_type)
        if strategy:
            return strategy(problem)
        return Solution(steps=[], result="无法识别问题类型")
```

### 里程碑

| # | 里程碑 | 交付物 | 成功标准 |
|---|--------|--------|----------|
| 3.1 | 基础步进求解 | `core/step_solver.py` | 方程/因式分解/分式 |
| 3.2 | 微积分步进 | `core/calculus_steps.py` | 求导/积分逐步展示 |
| 3.3 | 策略引擎 | `core/solver_strategy.py` | 自动问题识别 |
| 3.4 | UI 集成 | `ui/step_by_step_panel.py` | 面板展示每步推导 |

---

## 6. 阶段 4 — GeoGebra 命令兼容层

> **目标**: 支持 GeoGebra 命令语法，实现与 GeoGebra 的命令兼容

### 6.1 命令解析器

```python
class GeoGebraCommandParser:
    """
    GeoGebra 命令解析器

    支持 GeoGebra 官方命令语法
    参考: https://github.com/geogebra/manual
    """

    # ── 几何命令 ──
    GEOMETRY_COMMANDS = {
        'Point': 'create_point',
        'Line': 'create_line',
        'Segment': 'create_segment',
        'Circle': 'create_circle',
        'Midpoint': 'create_midpoint',
        'Intersection': 'create_intersection',
        'PerpendicularLine': 'create_perpendicular',
        'ParallelLine': 'create_parallel',
        'AngleBisector': 'create_angle_bisector',
        'PerpendicularBisector': 'create_perpendicular_bisector',
        'Tangent': 'create_tangent',
        'Reflection': 'reflect_object',
        'Rotation': 'rotate_object',
        'Translation': 'translate_object',
        'Dilation': 'dilate_object',
    }

    # ── 度量命令 ──
    MEASUREMENT_COMMANDS = {
        'Distance': 'measure_distance',
        'Length': 'measure_length',
        'Angle': 'measure_angle',
        'Area': 'measure_area',
        'Perimeter': 'measure_perimeter',
        'Slope': 'measure_slope',
        'Curvature': 'measure_curvature',
        'ArcLength': 'measure_arc_length',
    }

    # ── 代数命令 ──
    ALGEBRA_COMMANDS = {
        'Solve': 'cas_solve',
        'NSolve': 'numeric_solve',
        'Factor': 'cas_factor',
        'Expand': 'cas_expand',
        'Simplify': 'cas_simplify',
        'Derivative': 'cas_differentiate',
        'Integral': 'cas_integrate',
    }

    # ── 作图命令 ──
    PLOT_COMMANDS = {
        'Function': 'plot_function',
        'Curve': 'plot_parametric',
        'ImplicitCurve': 'plot_implicit',
        'Polar': 'plot_polar',
        'Sequence': 'generate_sequence',
    }

    def parse(self, command: str) -> ParseResult:
        """
        解析 GeoGebra 命令
        例如: Point((1,2)) → ParseResult('create_point', [(1,2)])
        """
        import re

        # 提取命令名和参数
        pattern = r'(\w+)\((.*)\)$'
        match = re.match(pattern, command.strip())

        if not match:
            return ParseResult(error="无法解析命令")

        cmd_name = match.group(1)
        args_str = match.group(2)

        # 解析参数
        args = self._parse_args(args_str)

        # 查找命令映射
        for cmd_map in [self.GEOMETRY_COMMANDS,
                       self.MEASUREMENT_COMMANDS,
                       self.ALGEBRA_COMMANDS,
                       self.PLOT_COMMANDS]:
            if cmd_name in cmd_map:
                internal_func = cmd_map[cmd_name]
                return ParseResult(function=internal_func, args=args)

        return ParseResult(error=f"未知命令: {cmd_name}")

    def _parse_args(self, args_str: str) -> list:
        """解析参数列表"""
        # 递归下降解析，处理嵌套括号
        ...
```

### 6.2 命令执行环境

```python
class GeoGebraCommandEnvironment:
    """
    GeoGebra 命令执行环境

    在 MathLab 中执行 GeoGebra 语法命令
    """

    def __init__(self, engine, cas_bus):
        self.engine = engine
        self.cas_bus = cas_bus
        self.parser = GeoGebraCommandParser()
        self.namespace = {}

    def execute(self, command: str) -> CommandResult:
        """执行 GeoGebra 命令"""
        parsed = self.parser.parse(command)

        if parsed.error:
            return CommandResult(error=parsed.error)

        # 获取对应的内部函数并执行
        func = getattr(self, parsed.function, None)
        if func:
            try:
                result = func(*parsed.args)
                return CommandResult(success=True, result=result)
            except Exception as e:
                return CommandResult(error=str(e))

        return CommandResult(error=f"命令执行失败: {parsed.function}")

    # ── 命令实现 ──
    def create_point(self, coords):
        return self.engine.add_point(coords[0], coords[1])

    def create_segment(self, p1, p2):
        return self.engine.add_segment(p1, p2)

    def measure_distance(self, obj1, obj2):
        return self.engine.distance(obj1, obj2)

    def cas_solve(self, equation, variable):
        return self.cas_bus.compute('solve', equation, variable)
```

### 6.3 常用命令速查表

| GeoGebra 命令 | MathLab 实现 | 示例 |
|---------------|-------------|------|
| `Point((1,2))` | `create_point(1, 2)` | `Point((1,2))` |
| `Line(A,B)` | `create_line(A, B)` | `Line(A,B)` |
| `Circle(A,B)` | `create_circle(A, B)` | `Circle(A,B)` |
| `Midpoint(A,B)` | `create_midpoint(A, B)` | `Midpoint(A,B)` |
| `Distance(A,B)` | `measure_distance(A, B)` | `Distance(A,B)` |
| `Angle(A,B,C)` | `measure_angle(A, B, C)` | `Angle(A,B,C)` |
| `Solve(x^2-4=0,x)` | `cas_solve(x**2-4,x)` | `Solve(x^2-4=0,x)` |
| `Factor(x^2-1)` | `cas_factor(x**2-1)` | `Factor(x^2-1)` |
| `Derivative(sin(x))` | `cas_differentiate(sin(x))` | `Derivative(sin(x))` |

### 里程碑

| # | 里程碑 | 交付物 | 成功标准 |
|---|--------|--------|----------|
| 4.1 | 命令解析器 | `core/ggb_parser.py` | 50+ 命令支持 |
| 4.2 | 执行环境 | `core/ggb_env.py` | 命令执行 + 错误处理 |
| 4.3 | UI 集成 | `ui/ggb_command_input.py` | 命令输入 + 提示 |
| 4.4 | 文档生成 | `docs/ggb_commands.md` | 命令速查表 |

---

## 7. 阶段 5 — GeoGebra 3D 内核集成

> **目标**: 引入 GeoGebra 的 3D 几何内核，实现真正的 3D 约束求解

### 7.1 3D 几何对象

```python
from dataclasses import dataclass

@dataclass
class Point3D:
    """3D 点"""
    x: float
    y: float
    z: float
    name: str = None

@dataclass
class Vector3D:
    """3D 向量"""
    x: float
    y: float
    z: float

@dataclass
class Line3D:
    """3D 直线 (由两点定义)"""
    point1: Point3D
    point2: Point3D

@dataclass
class Plane3D:
    """3D 平面"""
    point: Point3D
    normal: Vector3D

@dataclass
class Sphere3D:
    """3D 球面"""
    center: Point3D
    radius: float

@dataclass
class Circle3D:
    """3D 圆 (在平面上)"""
    center: Point3D
    radius: float
    plane: Plane3D
```

### 7.2 3D 约束求解器

```python
class GeoGebra3DEngine:
    """
    GeoGebra 级 3D 几何引擎

    目标:
    1. 支持 3D 几何对象的创建和约束
    2. 实现 3D 约束求解
    3. 与现有 2D 引擎协同工作
    """

    def __init__(self):
        self.objects_3d: Dict[str, Geo3DObject] = {}
        self.constraints_3d: List[Constraint3D] = []

    # ── 3D 对象创建 ──
    def add_point3d(self, x: float, y: float, z: float,
                    name: str = None) -> str:
        """创建 3D 点"""

    def add_line3d(self, p1_id: str, p2_id: str) -> str:
        """创建 3D 直线"""

    def add_plane3d(self, point_id: str, normal_id: str = None,
                    v1_id: str = None, v2_id: str = None) -> str:
        """创建 3D 平面"""

    def add_sphere3d(self, center_id: str, radius: float) -> str:
        """创建球面"""

    def add_circle3d(self, center_id: str, radius: float,
                     plane_id: str) -> str:
        """创建 3D 圆"""

    # ── 3D 约束 ──
    def add_parallel(self, obj1_id: str, obj2_id: str) -> str:
        """平行约束 (线-线, 平面-平面)"""

    def add_perpendicular(self, obj1_id: str, obj2_id: str) -> str:
        """垂直约束"""

    def add_on_plane(self, point_id: str, plane_id: str) -> str:
        """点在平面上"""

    def add_on_line(self, point_id: str, line_id: str) -> str:
        """点在线上"""

    # ── 3D 求解 ──
    def solve_3d(self) -> bool:
        """
        求解 3D 约束
        使用梯度下降 + 投影混合算法
        """
        ...

    # ── 渲染接口 ──
    def get_render_data(self) -> RenderData3D:
        """获取渲染所需数据 (供 Three.js 使用)"""
        ...
```

### 7.3 3D 可视化集成

```python
class ThreeDViewerPro:
    """
    增强型 3D 查看器 (基于现有 plugin_3d_viewer)

    改进:
    1. 与 GeoGebra 3D 内核对接
    2. 支持约束求解结果可视化
    3. 更好的交互体验
    """

    def __init__(self):
        self.engine_3d = GeoGebra3DEngine()
        self.web_channel = None  # Qt WebChannel

    def sync_from_engine(self):
        """从 3D 引擎同步数据到 Three.js 渲染"""
        render_data = self.engine_3d.get_render_data()
        self.web_channel.emit('update_3d', render_data)

    def on_user_interaction(self, object_id: str, new_coords: dict):
        """处理用户交互，更新引擎并求解"""
        self.engine_3d.update_point(object_id, new_coords)
        self.engine_3d.solve_3d()
        self.sync_from_engine()
```

### 里程碑

| # | 里程碑 | 交付物 | 成功标准 |
|---|--------|--------|----------|
| 5.1 | 3D 对象模型 | `core/geo3d_objects.py` | 点/线/平面/球/圆 |
| 5.2 | 3D 约束求解 | `core/geo3d_solver.py` | 平行/垂直/点在面上 |
| 5.3 | 渲染集成 | `plugins/plugin_3d_viewer/` | 3D 渲染 + 约束联动 |
| 5.4 | 交互增强 | `ui/geo3d_canvas.py` | 拖拽 + 约束更新 |

---

## 8. 阶段 6 — 协作与 Web 同步

> **目标**: 实现实时多人协作，参考 GeoGebra 的协作教室功能

### 8.1 协作架构

```python
class CollaborationServer:
    """
    协作服务器 (WebSocket)

    借鉴 GeoGebra 协作教室:
    1. 房间管理
    2. 操作同步
    3. 教师控制
    """

    class Room:
        def __init__(self, room_id: str, host_id: str):
            self.room_id = room_id
            self.host_id = host_id
            self.participants: Dict[str, Participant] = {}
            self.document_state = {}
            self.is_locked = False

        def broadcast(self, event: dict, exclude: str = None):
            """广播事件到所有参与者"""
            ...

        def apply_operation(self, op: Operation, user_id: str):
            """应用远程操作 (OT 算法)"""
            ...

    class Participant:
        def __init__(self, user_id: str, name: str, role: str):
            self.user_id = user_id
            self.name = name
            self.role = role  # 'teacher', 'student'
            self.cursor_position = None
            self.selection = []

    # ── 房间操作 ──
    def create_room(self, host_id: str) -> str:
        """创建房间，返回 room_id"""

    def join_room(self, room_id: str, user: Participant) -> bool:
        """加入房间"""

    def leave_room(self, room_id: str, user_id: str):
        """离开房间"""

    def lock_room(self, room_id: str, teacher_id: str):
        """教师锁定房间 (禁止学生编辑)"""

    def broadcast_cursor(self, room_id: str, user_id: str, position: dict):
        """广播光标位置"""
```

### 8.2 操作同步协议

```python
class OperationSync:
    """
    操作同步协议

    支持的操作类型:
    1. 创建对象
    2. 删除对象
    3. 更新对象属性
    4. 添加约束
    5. 鼠标拖拽
    """

    class Operation:
        def __init__(self, op_type: str, object_id: str,
                     data: dict, user_id: str, timestamp: float):
            self.type = op_type
            self.object_id = object_id
            self.data = data
            self.user_id = user_id
            self.timestamp = timestamp

    OPERATION_TYPES = [
        'create_object',
        'delete_object',
        'update_object',
        'add_constraint',
        'remove_constraint',
        'cursor_move',
        'selection_change',
    ]

    def serialize(self, op: Operation) -> str:
        """序列化为 JSON"""

    def deserialize(self, data: str) -> Operation:
        """从 JSON 反序列化"""

    def transform(self, op1: Operation, op2: Operation) -> Operation:
        """
        OT 转换算法
        处理两个并发操作的冲突
        """
        ...
```

### 里程碑

| # | 里程碑 | 交付物 | 成功标准 |
|---|--------|--------|----------|
| 6.1 | 协作服务器 | `core/collaboration.py` | 房间管理 + 广播 |
| 6.2 | 操作同步 | `core/op_sync.py` | OT 算法 + 冲突处理 |
| 6.3 | 协作 UI | `ui/collab_panel.py` | 实时光标 + 锁控制 |
| 6.4 | 云端同步 | `core/cloud_sync.py` | 项目云端备份 |

---

## 9. 综合时间线

```
                Q1         Q2         Q3         Q4
                ├──────────┼──────────┼──────────┼──────────┤
阶段 1          ████████████████████
(GeoGebra约束)   约束扩展   求解器     轨迹       度量

阶段 2                        ████████████████████
(Giac CAS)                    Giac集成   CAS总线   命令兼容

阶段 3                                     ████████████████████
(步进求解)                                 方程步进   微积分    策略引擎

阶段 4                                                ████████████████████
(GGB命令)                                              命令解析   执行环境  UI集成

阶段 5          ████████████████████████████████████████
(3D内核)         3D对象      约束求解   渲染集成   交互增强

阶段 6                                                       ███████
(协作)                                                           协作

并行工作流:
- 阶段 1 和阶段 5 可并行 (不同模块)
- 阶段 2 和阶段 3 可并行 (不同 CAS 功能)
- 阶段 4 在阶段 1 完成后开始 (依赖约束系统)
- 阶段 6 在所有功能完成后开始 (协作集成)
```

---

## 10. 技术选型总结

### 10.1 新增依赖

```txt
# ── 阶段 2: Giac CAS ──
giac>=1.9.0              # Giac CAS (编译为可执行文件)
# 或
pyodide>=0.24.0         # 如使用 WASM 方案

# ── 阶段 3: 步进求解 ──
# (纯 Python 实现，无需额外依赖)

# ── 阶段 6: 协作 ──
websockets>=12.0        # WebSocket 服务器
aiortc>=1.9.0          # WebRTC (可选，用于 P2P 协作)
```

### 10.2 许可证考虑

| 组件 | 许可证 | 注意事项 |
|------|--------|----------|
| GeoGebra 主应用 | GPLv3 | 可参考架构，不可直接复制代码 |
| Giac | GPLv3 | 同上 |
| Solver-Engine | ? | 需确认许可证 |
| MathLab 本身 | Apache 2.0 | 保持独立 |

**重要**: GeoGebra 代码采用 GPLv3，若直接引用其代码，则衍生作品必须开源。建议:
1. 参考其架构设计，用 Python 重新实现
2. 仅使用其算法思想，不复制代码
3. Giac 可作为独立工具调用，不嵌入 MathLab 代码

---

## 11. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| **Giac 集成复杂度** | Giac 编译困难或性能不佳 | 优先用 HTTP 服务方案；SymPy 作为 fallback |
| **3D 约束求解性能** | 3D 求解比 2D 慢很多 | 降采样；仅在必要时求解 |
| **GPL 许可证传染** | 不能直接使用 GeoGebra 代码 | 参考架构重新实现；保持代码独立 |
| **步进求解覆盖度** | 部分题型无法步进 | 分阶段实现；优先高频题型 |
| **协作同步延迟** | 多人编辑操作延迟 | 乐观锁 + 本地优先渲染 |
| **功能膨胀** | 3.0 范围过大 | 严格按里程碑交付；核心功能优先 |

---

## 12. 立即可执行的行动 (第一个月)

1. **搭建 Giac 环境** - 安装 Giac 并测试基本 CAS 功能
2. **设计 GeoGebraEngine Pro 接口** - 定义约束类型和求解器 API
3. **实现 GiacProvider 原型** - 连接 Giac 并测试 factor/solve/integrate
4. **创建 StepByStepSolver 骨架** - 实现一元一次方程的步进求解
5. **调研 GeoGebra 命令文档** - 整理 50+ 常用命令及参数格式

---

## 13. 参考资源

### GeoGebra 开源代码

- [GeoGebra 主仓库](https://github.com/geogebra/geogebra)
- [Giac CAS](https://github.com/geogebra/giac)
- [Solver Engine](https://github.com/geogebra/solver-engine)
- [GeoGebra 手册](https://github.com/geogebra/manual)

### 集成参考

- [nodegiac - NodeJS Giac 绑定](https://www.npmjs.com/package/giac)
- [Giac WebAssembly](https://github.com/geogebra/giac/tree/master/giac-wasm)
- [GeoGebra 命令文档](https://wiki.geogebra.org/en/Reference:Commands)

---

**文档版本**: 3.0-draft
**创建日期**: 2026-06-22
**基于**: MathLab 2.6 + GeoGebra 开源代码研究
