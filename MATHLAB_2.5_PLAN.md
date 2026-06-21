# MathLab 2.5 开发计划 (代号: axiom)

> **核心理念**：博采众长，将 GeoGebra 的几何深度、SageMath 的多引擎 CAS、Manim 的动画品质、Octave 的数值成熟度、Maxima 的符号计算深度，融合进 MathLab 的统一平台。

---

## 总体架构升级

### 从 2.0 到 2.5 的演进路径

```
2.0 (已完成)                    2.5 (本计划)
─────────────────────────────────────────────────────
单线程 UI         ──→    全异步 + QThread
SymPy 单一 CAS    ──→    多引擎 CAS 总线 (SymPy + Maxima + Giac)
基础几何画板      ──→    完整约束求解系统 (GeoGebra 级)
简单算法动画      ──→    Manim 级数学动画引擎
基本数值计算      ──→    Octave 级矩阵运算 + LAPACK
无笔记本          ──→    SageMath 风格交互笔记本
本地单机          ──→    Web 同步 + 协作
```

### 2.5 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户界面层 (UI Layer)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ │
│  │ 几何画板 │ │ 交互笔记本│ │ 3D 渲染器│ │ 动画编辑器│ │ 命令面板  │ │
│  │ (Qt Canvas)│ │(Notebook)│ │(WebEngine)│ │(Timeline)│ │(CmdBar)  │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│                       业务逻辑层 (Core Layer)                        │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  Geometry Engine v2  │  CAS Bus  │  Animation Engine  │ NumEngine││
│  │  (DAG + Constraints) │(Multi-    │  (Manim-inspired)  │(BLAS/   ││
│  │                      │ Engine)   │                    │ LAPACK) ││
│  └─────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────┤
│                       安全隔离层 (Sandbox Layer)                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  Python REPL (subprocess)  │  WebEngine Sandbox  │  Plugin VM   ││
│  └─────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────┤
│                       数据与协作层 (Data Layer)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ 项目文件 │ │ 资源库   │ │ WebSocket│ │ 云端同步 │              │
│  │ (.mlproj)│ │(教学资源)│ │ 协作引擎 │ │(可选)    │              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 阶段 1 — 几何引擎 v2：GeoGebra 级约束系统

> **借鉴来源**：GeoGebra 的核心壁垒 — 完整的几何约束求解

### 目标
将现有基础几何引擎升级为支持丰富约束关系的专业级动态几何系统。

### 1.1 约束求解器 (Constraint Solver)

**现状**：当前 `GeometryEngine` 仅支持基本对象创建，无约束关系。

**目标**：实现基于数值迭代的约束求解器。

```python
# 新增约束类型 (借鉴 GeoGebra)
class ConstraintType(Enum):
    # 基础约束
    FIXED_POINT = "fixed"           # 固定点
    MIDPOINT = "midpoint"           # 中点
    # 距离约束
    DISTANCE = "distance"           # 固定距离
    RADIUS = "radius"               # 固定半径
    # 角度约束
    ANGLE = "angle"                 # 固定角度
    # 关系约束
    PARALLEL = "parallel"           # 平行
    PERPENDICULAR = "perpendicular" # 垂直
    COLLINEAR = "collinear"         # 共线
    CONCYCLIC = "concyclic"         # 共圆
    # 位置约束
    ON_LINE = "on_line"             # 在直线上
    ON_CIRCLE = "on_circle"         # 在圆上
    ON_CURVE = "on_curve"           # 在曲线上
    TANGENT = "tangent"             # 相切
    # 变换约束
    REFLECTION = "reflection"       # 反射
    ROTATION = "rotation"           # 旋转
    TRANSLATION = "translation"     # 平移
    DILATION = "dilation"           # 缩放

class ConstraintSolver:
    """基于 Newton-Raphson 迭代的约束求解器 (借鉴 GeoGebra 的 SolvingMethods)"""
    
    def __init__(self, tolerance=1e-8, max_iterations=100):
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        self.constraints: List[Constraint] = []
    
    def add_constraint(self, constraint_type, target_ids, params=None):
        """添加约束"""
        ...
    
    def solve(self):
        """
        求解所有约束
        算法: Newton-Raphson + 梯度下降混合策略
        - 约束少时用 Newton-Raphson (快速收敛)
        - 约束多/欠约束时用 Levenberg-Marquardt (稳定)
        """
        ...
    
    def get_free_variables(self) -> List[str]:
        """获取自由变量 (欠约束时用户可拖动的变量)"""
        ...
    
    def check_overconstrained(self) -> Tuple[bool, List[str]]:
        """检测过约束并返回冲突的约束列表"""
        ...
```

### 1.2 几何变换系统

```python
class GeometryTransformer:
    """几何变换 (借鉴 GeoGebra 的 Transformations)"""
    
    def reflect(self, obj_id, line_id) -> str:
        """关于直线反射"""
    
    def rotate(self, obj_id, center_id, angle_rad) -> str:
        """绕点旋转"""
    
    def translate(self, obj_id, vector) -> str:
        """平移"""
    
    def dilate(self, obj_id, center_id, ratio) -> str:
        """以点为中心缩放"""
    
    def compose(self, *transform_ids) -> str:
        """变换复合"""
```

### 1.3 轨迹与包络线

```python
class LocusEngine:
    """轨迹引擎 (借鉴 GeoGebra 的 Locus 命令)"""
    
    def create_locus(self, tracer_id, driver_id, samples=500) -> str:
        """创建参数轨迹"""
    
    def create_envelope(self, family_expr, param_var, param_range) -> str:
        """创建曲线族包络线"""
    
    def create_trace(self, obj_id, max_points=10000) -> str:
        """对象运动轨迹追踪"""
```

### 1.4 度量与计算

```python
class MeasurementTools:
    """度量工具 (借鉴 GeoGebra 的测量命令)"""
    
    def distance(self, p1_id, p2_id) -> float
    def angle(self, p1_id, vertex_id, p3_id) -> float
    def area(self, polygon_id) -> float
    def perimeter(self, polygon_id) -> float
    def slope(self, line_id) -> float
    def curvature(self, curve_id, param) -> float
    def arc_length(self, curve_id, t_start, t_end) -> float
```

### 里程碑

| # | 里程碑 | 交付物 | 成功标准 |
|---|--------|--------|----------|
| 1.1 | 约束求解器 v1 | `core/constraint_solver.py` | 10 种基础约束求解通过测试 |
| 1.2 | 几何变换 | `core/geometry_transformer.py` | 反射/旋转/平移/缩放正确渲染 |
| 1.3 | 轨迹引擎 | `core/locus_engine.py` | 拖动驱动点，轨迹实时更新 |
| 1.4 | 度量工具 | `core/measurement.py` | 距离/角度/面积实时显示 |

---

## 阶段 2 — 多引擎 CAS 总线：SageMath + Maxima 级符号计算

> **借鉴来源**：SageMath 的多引擎架构、Maxima 的符号计算深度

### 目标
构建统一的 CAS 总线，集成多个符号计算后端，按任务自动路由到最优引擎。

### 2.1 CAS 总线架构

```python
class CASBus:
    """
    多引擎 CAS 总线 (借鉴 SageMath 的多后端架构)
    
    SageMath 的核心理念: 不自己实现所有算法，而是集成各领域最强的引擎
    - SymPy: Python 原生，通用符号计算
    - Maxima: Lisp 实现，符号积分/极限极强
    - Giac: C++ 实现，多项式运算极快
    """
    
    ENGINES = {
        'sympy': SymPyProvider,      # 默认引擎
        'maxima': MaximaProvider,     # 符号积分/极限 (通过 subprocess)
        'giac': GiacProvider,         # 多项式/代数几何 (通过 bindings)
    }
    
    # 任务路由策略 (借鉴 SageMath 的算法选择逻辑)
    ROUTING_TABLE = {
        'integrate':    ['maxima', 'sympy'],      # 积分: Maxima 优先
        'limit':        ['maxima', 'sympy'],      # 极限: Maxima 优先
        'factor':       ['giac', 'sympy'],        # 因式分解: Giac 优先
        'groebner':     ['giac', 'sympy'],        # Gröbner 基: Giac 优先
        'solve':        ['sympy', 'maxima'],      # 方程求解: SymPy 优先
        'simplify':     ['sympy', 'maxima'],      # 化简: SymPy 优先
        'diff':         ['sympy'],                # 求导: SymPy 足够
        'series':       ['sympy'],                # 级数展开: SymPy 足够
        'matrix':       ['sympy', 'giac'],        # 矩阵运算
    }
    
    def compute(self, task_type, expression, **kwargs) -> CASResult:
        """
        自动路由到最优引擎计算
        - 尝试首选引擎
        - 失败时自动降级到备选引擎
        - 超时保护 (防止符号计算死循环)
        """
        engines = self.ROUTING_TABLE.get(task_type, ['sympy'])
        for engine_name in engines:
            engine = self.ENGINES[engine_name]
            try:
                result = engine.compute(task_type, expression, timeout=30, **kwargs)
                if result.success:
                    return CASResult(result, engine=engine_name)
            except (TimeoutError, EngineError):
                continue
        return CASResult(success=False, error="所有引擎均计算失败")
```

### 2.2 Maxima 集成层

```python
class MaximaProvider:
    """
    Maxima 符号计算引擎 (借鉴 Maxima 的核心优势)
    
    Maxima 的独特优势:
    1. 符号积分算法比 SymPy 更成熟 (特别是特殊函数积分)
    2. 极限计算更鲁棒
    3. 常微分方程求解更全面
    4. 模式匹配系统
    """
    
    def __init__(self, maxima_path='maxima'):
        self.process = None
        self.maxima_path = maxima_path
    
    def _ensure_running(self):
        """保持 Maxima 进程池 (复用启动开销)"""
        ...
    
    def integrate(self, expr_str, var) -> dict:
        """符号积分 - 调用 Maxima 的 integrate"""
        ...
    
    def limit(self, expr_str, var, point, direction='+') -> dict:
        """极限 - 调用 Maxima 的 limit"""
        ...
    
    def ode_solve(self, eq_str, func_str, var) -> dict:
        """常微分方程 - 调用 Maxima 的 ode2"""
        ...
    
    def laplace(self, expr_str, var, s) -> dict:
        """拉普拉斯变换"""
        ...
    
    def inverse_laplace(self, expr_str, s, var) -> dict:
        """拉普拉斯逆变换"""
        ...
    
    def taylor(self, expr_str, var, point, order) -> dict:
        """泰勒展开"""
        ...
```

### 2.3 增强的符号计算功能

```python
class EnhancedCAS:
    """增强 CAS 功能 (借鉴 Maxima/SageMath 的深度功能)"""
    
    # ── Maxima 级深度功能 ──
    def laplace_transform(self, expr, t, s) -> CASResult
    def inverse_laplace(self, expr, s, t) -> CASResult
    def fourier_transform(self, expr, x, w) -> CASResult
    def z_transform(self, expr, n, z) -> CASResult
    
    # ── SageMath 级代数功能 ──
    def groebner_basis(self, polynomials, vars, order='grevlex') -> CASResult
    def polynomial_factor(self, poly, modulus=None) -> CASResult
    def resultant(self, poly1, poly2, var) -> CASResult
    
    # ── 微分方程 (借鉴 Maxima 的 ode2) ──
    def ode_solve(self, equation, func, var, type='auto') -> CASResult
    def pde_solve(self, equation, func, vars) -> CASResult
    
    # ── 级数与渐近 (借鉴 Maxima 的 taylor/powerseries) ──
    def series_expansion(self, expr, var, point, order) -> CASResult
    def asymptotic_expansion(self, expr, var, point) -> CASResult
    def fourier_series(self, func, var, period, n_terms) -> CASResult
```

### 里程碑

| # | 里程碑 | 交付物 | 成功标准 |
|---|--------|--------|----------|
| 2.1 | CAS 总线 | `core/cas_bus.py` | 路由引擎 + 降级机制 |
| 2.2 | Maxima 集成 | `core/maxima_provider.py` | 积分/极限/ODE 测试通过 |
| 2.3 | 增强 CAS | `core/enhanced_cas.py` | 拉普拉斯/傅里叶/Gröbner 基 |
| 2.4 | 性能基准 | `tests/benchmark_cas.py` | 100 道积分题，Maxima 成功率 > SymPy |

---

## 阶段 3 — 数学动画引擎：Manim 级可视化

> **借鉴来源**：Manim 的数学动画理念与渲染品质

### 目标
构建内置的数学动画引擎，让用户能为几何构造、算法步骤、函数变换创建高质量教学动画。

### 3.1 动画引擎核心

```python
class MathAnimationEngine:
    """
    数学动画引擎 (借鉴 Manim 的核心理念)
    
    Manim 的设计哲学:
    1. 声明式动画 - 描述"是什么"而非"怎么做"
    2. 数学对象即动画对象 - Point/Line/Circle 都可以直接动画
    3. 组合性 - 简单动画可以组合成复杂动画
    4. 时间线控制 - 精确控制每个动画的时序
    """
    
    class Animation:
        """动画基类 (借鉴 Manim 的 Animation 体系)"""
        def __init__(self, target, duration=1.0, rate_func=None):
            self.target = target
            self.duration = duration
            self.rate_func = rate_func or ease_in_out_cubic
        
        def interpolate(self, alpha: float):
            """在 [0,1] 范围内插值"""
            raise NotImplementedError
    
    # ── 基础动画 (借鉴 Manim 的 Transform 系列) ──
    class Create(Animation):
        """创建动画 - 对象从无到有"""
    
    class FadeIn(Animation):
        """淡入"""
    
    class FadeOut(Animation):
        """淡出"""
    
    class Transform(Animation):
        """变形动画 - 一个对象变为另一个"""
    
    class MoveAlongPath(Animation):
        """沿路径移动"""
    
    class Write(Animation):
        """书写动画 - 模拟手写数学公式"""
    
    # ── 数学专用动画 ──
    class TracePath(Animation):
        """轨迹追踪 - 拖动点留下轨迹"""
    
    class GraphDraw(Animation):
        """函数绘制 - 从左到右逐步画出函数曲线"""
    
    class MorphShape(Animation):
        """形状渐变 - 圆变椭圆、直线变曲线"""
    
    class ConstraintDemo(Animation):
        """约束演示 - 展示几何约束如何工作"""
    
    # ── 时间线编排 ──
    class Timeline:
        """动画时间线 (借鉴 Manim 的 Scene 编排)"""
        
        def play(self, *animations, lag_ratio=0, run_time=None):
            """播放一组动画 (可并行或串行)"""
        
        def wait(self, duration):
            """等待/暂停"""
        
        def then(self, *animations):
            """在上一组动画完成后播放"""
        
        def parallel(self, *animations):
            """同时播放多个动画"""
        
        def sequence(self, *animations):
            """依次播放动画"""
        
        def loop(self, animation, count=-1):
            """循环播放 (-1 为无限)"""
        
        def export_gif(self, path, fps=30):
            """导出 GIF"""
        
        def export_video(self, path, fps=60, format='mp4'):
            """导出视频 (需要 ffmpeg)"""
        
        def export_svg_frames(self, dir_path):
            """导出 SVG 帧序列 (矢量，适合论文)"""
```

### 3.2 几何动画预设

```python
class GeometryAnimations:
    """几何动画预设 (借鉴 GeoGebra 的展示模式 + Manim 的品质)"""
    
    def demonstrate_construction(self, construction_steps):
        """
        逐步演示几何构造过程
        例如: 三角形外接圆
        Step 1: 创建三角形 (Create 动画)
        Step 2: 作两边中垂线 (Write 动画)
        Step 3: 标注交点 (FadeIn 动画)
        Step 4: 画外接圆 (Create 动画)
        Step 5: 高亮标注 (Flash 动画)
        """
    
    def demonstrate_transformation(self, obj, transform, repeat=1):
        """演示几何变换 (反射/旋转/缩放)"""
    
    def demonstrate_proof(self, proof_steps):
        """
        可视化证明过程
        每一步: 高亮相关对象 → 添加标注 → 过渡到下一步
        """
    
    def demonstrate_locus(self, tracer, driver, param_range):
        """轨迹生成动画 - 点移动时实时画出轨迹"""
```

### 3.3 算法动画增强

```python
class AlgorithmAnimationV2:
    """
    算法动画 v2 (借鉴 Manim 的精确控制)
    
    对比现有 AlgoAnimator:
    - 现有: 基于生成器的简单逐步展示
    - v2: Manim 级动画控制 + 高亮/标注/过渡
    """
    
    def sorting_demo(self, data, algorithm='quicksort'):
        """
        排序动画 (借鉴 Manim 的 SortingVisualizations)
        - 柱状图高度 = 数据值
        - 比较时高亮两个元素 (黄色)
        - 交换时有平滑移动动画
        - 已排序部分变绿
        - 复杂度实时显示
        """
    
    def graph_algorithm_demo(self, graph, algorithm='dijkstra'):
        """
        图论算法动画
        - 节点按拓扑布局
        - 已访问节点渐变色
        - 当前探索边高亮
        - 最短路径最终高亮为红色
        - 距离标签实时更新
        """
    
    def tree_traversal_demo(self, tree, order='inorder'):
        """
        树遍历动画
        - 当前节点脉冲高亮
        - 已访问节点变色
        - 遍历顺序箭头指示
        """
```

### 里程碑

| # | 里程碑 | 交付物 | 成功标准 |
|---|--------|--------|----------|
| 3.1 | 动画引擎核心 | `core/animation_engine.py` | 基础动画 (Create/Fade/Transform) |
| 3.2 | 几何动画 | `core/geometry_animations.py` | 构造演示 + 轨迹动画 |
| 3.3 | 算法动画 v2 | `core/algo_animator_v2.py` | 排序/图论动画，可导出 GIF |
| 3.4 | 导出系统 | `core/animation_export.py` | GIF/MP4/SVG 导出 |

---

## 阶段 4 — 数值计算引擎：Octave 级矩阵运算

> **借鉴来源**：GNU Octave 的数值计算成熟度与 MATLAB 兼容性

### 目标
构建高性能数值计算层，补齐 SymPy 在纯数值场景下的短板。

### 4.1 矩阵运算引擎

```python
class NumEngine:
    """
    数值计算引擎 (借鉴 Octave 的设计理念)
    
    Octave 的核心优势:
    1. 矩阵是一等公民 (所有运算基于矩阵)
    2. BLAS/LAPACK 后端 (极致性能)
    3. MATLAB 兼容语法 (降低学习成本)
    4. 丰富的线性代数函数
    """
    
    def __init__(self):
        # 后端: NumPy (BLAS/LAPACK) + SciPy (高级算法)
        pass
    
    # ── 线性代数 (Octave 级) ──
    def eigenvalues(self, matrix) -> dict
    def svd(self, matrix) -> dict
    def lu_decomposition(self, matrix) -> dict
    def qr_decomposition(self, matrix) -> dict
    def cholesky(self, matrix) -> dict
    def jordan_form(self, matrix) -> dict
    def matrix_exponential(self, matrix) -> dict
    
    # ── 数值微积分 ──
    def numerical_derivative(self, func, x, order=1) -> float
    def numerical_integral(self, func, a, b, method='adaptive') -> float
    def numerical_ode(self, func, y0, t_span, method='rk45') -> Solution
    def numerical_pde(self, ...) -> Solution
    
    # ── 优化 (SciPy 后端) ──
    def minimize(self, func, x0, method='BFGS') -> OptimizeResult
    def maximize(self, func, x0, method='BFGS') -> OptimizeResult
    def least_squares(self, func, x0, bounds=None) -> OptimizeResult
    def root_finding(self, func, bracket) -> float
    
    # ── 信号处理 ──
    def fft(self, signal) -> np.ndarray
    def ifft(self, spectrum) -> np.ndarray
    def convolve(self, signal1, signal2) -> np.ndarray
    def filter_design(self, ...) -> ...
    
    # ── 统计 ──
    def hypothesis_test(self, data1, data2, test='ttest') -> TestResult
    def anova(self, groups) -> ANOVAResult
    def regression(self, X, y, model='linear') -> RegressionResult
    def pca(self, data, n_components) -> PCAResult
```

### 4.2 MATLAB/Octave 语法桥接

```python
class OctaveBridge:
    """
    Octave 语法桥接 (降低迁移成本)
    
    让熟悉 MATLAB/Octave 的用户能直接用他们习惯的语法
    """
    
    SYNTAX_MAP = {
        # MATLAB 语法 → Python/NumPy
        'A\'':          'A.T',              # 转置
        'A.*B':         'A * B',            # 逐元素乘
        'A*B':          'A @ B',            # 矩阵乘
        'A.^2':         'A ** 2',           # 逐元素幂
        'zeros(n,m)':   'np.zeros((n,m))',  # 零矩阵
        'ones(n,m)':    'np.ones((n,m))',   # 全1矩阵
        'eye(n)':       'np.eye(n)',        # 单位矩阵
        'linspace(a,b,n)': 'np.linspace(a,b,n)',
        'size(A)':      'A.shape',
        'length(v)':    'len(v)',
        'find(x>0)':    'np.where(x>0)',
        'max(A)':       'A.max()',
        'min(A)':       'A.min()',
        'sum(A)':       'A.sum()',
        'sort(v)':      'np.sort(v)',
    }
    
    def translate(self, octave_code: str) -> str:
        """将 MATLAB/Octave 语法翻译为 Python"""
        ...
```

### 4.3 可视化数值面板

```python
class NumVisualizationPanel:
    """数值可视化面板 (借鉴 Octave 的绘图能力)"""
    
    def plot_matrix_heatmap(self, matrix, title=""):
        """矩阵热力图"""
    
    def plot_eigenvalue_spectrum(self, matrix):
        """特征值谱图 (复平面)"""
    
    def plot_phase_portrait(self, ode_system, xlim, ylim):
        """相图 (ODE 系统)"""
    
    def plot_vector_field(self, func2d, xlim, ylim):
        """向量场"""
    
    def plot_surface(self, func2d, xlim, ylim):
        """3D 曲面图"""
    
    def plot_contour(self, func2d, xlim, ylim):
        """等高线图"""
```

### 里程碑

| # | 里程碑 | 交付物 | 成功标准 |
|---|--------|--------|----------|
| 4.1 | NumEngine 核心 | `core/num_engine.py` | 线性代数 + ODE 求解 |
| 4.2 | Octave 桥接 | `core/octave_bridge.py` | MATLAB 语法翻译 + 执行 |
| 4.3 | 数值可视化 | `ui/num_vis_panel.py` | 热力图/相图/向量场 |

---

## 阶段 5 — 交互笔记本：SageMath 式计算环境

> **借鉴来源**：SageMath 的 Jupyter Notebook 体验 + GeoGebra 的交互式工作表

### 目标
在 MathLab 内嵌一个交互式计算笔记本，融合代码、公式、图形、动画于一体。

### 5.1 笔记本单元格系统

```python
class NotebookCell:
    """笔记本单元格"""
    
    class CellType(Enum):
        CODE = "code"           # Python/MathLab 代码
        MARKDOWN = "markdown"   # 富文本 (LaTeX 公式支持)
        MATH = "math"           # 数学公式 (自动渲染)
        GEO = "geometry"        # 几何画板 (嵌入式)
        PLOT = "plot"           # 几何/函数图形
        TABLE = "table"         # 数据表格
        ANIMATION = "animation" # 动画
        SLIDER = "slider"       # 交互滑块
    
    def __init__(self, cell_type, content):
        self.type = cell_type
        self.content = content
        self.outputs = []
        self.execution_count = None
    
    def execute(self, kernel) -> List[Output]:
        """执行单元格"""
        ...

class MathLabNotebook:
    """
    交互笔记本 (借鉴 SageMath 的 Sage Worksheet)
    
    特色:
    1. 混合单元格: 代码 + 公式 + 几何画板 + 动画可以在同一页面
    2. 交互滑块: 参数可以绑定滑块，拖动实时更新
    3. 即时预览: LaTeX 公式实时渲染
    4. 导出: 可导出为 HTML/PDF/独立可执行文件
    """
    
    def add_cell(self, cell_type, content, position=None):
        ...
    
    def execute_all(self):
        """从上到下执行所有单元格"""
        ...
    
    def execute_cell(self, cell_id):
        """执行单个单元格"""
        ...
    
    def export_html(self, path):
        """导出为独立 HTML (含交互)"""
        ...
    
    def export_pdf(self, path):
        """导出为 PDF"""
        ...
    
    def to_mathlab_project(self, path):
        """转换为 MathLab 项目文件"""
        ...
```

### 5.2 交互式参数控件

```python
class InteractiveWidgets:
    """
    交互控件 (借鉴 GeoGebra 的滑块 + SageMath 的 @interact)
    
    GeoGebra 的滑块是其最受欢迎的功能之一:
    - 拖动滑块 → 参数变化 → 图形实时更新
    - 用于探索数学概念 (如参数对方程曲线的影响)
    """
    
    class Slider:
        """滑块控件"""
        def __init__(self, name, min_val, max_val, step=0.1, default=None):
            ...
    
    class Dropdown:
        """下拉选择"""
        def __init__(self, name, options, default=None):
            ...
    
    class Checkbox:
        """复选框"""
        def __init__(self, name, default=False):
            ...
    
    class ColorPicker:
        """颜色选择器"""
        def __init__(self, name, default='#000000'):
            ...
    
    def interact(self, func, **widgets):
        """
        装饰器: 将函数参数绑定到交互控件
        
        @interact(angle=Slider("角度", 0, 360, 15))
        def rotate_shape(angle):
            # 每次拖动滑块，这个函数都会被重新调用
            engine.rotate(shape, center, radians(angle))
        """
        ...
```

### 里程碑

| # | 里程碑 | 交付物 | 成功标准 |
|---|--------|--------|----------|
| 5.1 | 笔记本核心 | `core/notebook.py` | 单元格系统 + 代码执行 |
| 5.2 | 交互控件 | `ui/interactive_widgets.py` | 滑块/下拉/复选框 |
| 5.3 | 笔记本 UI | `ui/notebook_panel.py` | 可视化笔记本界面 |
| 5.4 | 导出系统 | `core/notebook_export.py` | HTML/PDF 导出 |

---

## 阶段 6 — 协作与生态：Web 同步 + 教学资源库

> **借鉴来源**：GeoGebra 的社区生态 + SageMath 的在线服务

### 6.1 WebSocket 协作引擎

```python
class CollaborationEngine:
    """
    实时协作引擎
    
    借鉴 GeoGebra 的协作教室:
    - 多人同时编辑同一几何画板
    - 操作实时同步
    - 教师可锁定/广播
    """
    
    class Room:
        def __init__(self, room_id, host_user):
            self.participants = []
            self.document = None
            self.locked = False
        
        def broadcast(self, operation, exclude_user=None):
            """广播操作到所有参与者"""
            ...
        
        def apply_operation(self, operation):
            """应用远程操作 (OT/CRDT)"""
            ...
    
    def create_room(self) -> str
    def join_room(self, room_id, user_name) -> bool
    def leave_room(self, room_id) -> bool
    def sync_state(self, room_id) -> dict
```

### 6.2 教学资源库

```python
class ResourceLibrary:
    """
    教学资源库 (借鉴 GeoGebra 的 Materials 平台)
    
    GeoGebra 有 100 万+ 免费教学资源，这是其核心竞争力之一
    MathLab 需要建立自己的资源生态
    """
    
    class Resource:
        id: str
        title: str
        description: str
        author: str
        tags: List[str]          # 如: "三角函数", "高中", "可视化"
        difficulty: str           # "初中" / "高中" / "大学"
        type: str                 # "worksheet" / "notebook" / "animation"
        content: dict             # 项目数据
        preview_url: str          # 预览图
        license: str
    
    def search(self, query, filters=None) -> List[Resource]
    def get_resource(self, resource_id) -> Resource
    def publish(self, resource) -> str  # 返回分享链接
    def rate(self, resource_id, score, comment) -> bool
    
    # 内置资源包
    BUILTIN_CATEGORIES = [
        "平面几何基础",
        "解析几何",
        "函数与图像",
        "三角函数",
        "微积分入门",
        "线性代数",
        "概率统计",
        "算法可视化",
    ]
```

### 里程碑

| # | 里程碑 | 交付物 | 成功标准 |
|---|--------|--------|----------|
| 6.1 | 协作引擎 | `core/collaboration.py` | 2 人实时同步编辑 |
| 6.2 | 资源库 | `core/resource_library.py` | 50+ 内置教学资源 |
| 6.3 | 分享系统 | `core/sharing.py` | 一键生成分享链接 |

---

## 综合时间线

```
          M1    M2    M3    M4    M5    M6    M7    M8    M9    M10   M11   M12
          ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
阶段 1    ████████████▓
(几何v2)  约束求解器   几何变换  轨迹引擎

阶段 2              ████████████▓
(CAS总线)           CAS总线     Maxima集成  增强CAS

阶段 3                        ████████████▓
(动画引擎)                    动画核心    几何动画  算法动画v2

阶段 4                                  ████████████▓
(数值引擎)                              NumEngine   Octave桥接

阶段 5                                            ████████████▓
(交互笔记本)                                      笔记本核心  交互控件  导出

阶段 6                                                      ████████████▓
(协作生态)                                                  协作引擎  资源库  分享
```

---

## 核心设计原则

### 1. 从各项目吸取的设计理念

| 来源 | 吸取的理念 | 在 MathLab 中的体现 |
|------|-----------|-------------------|
| **GeoGebra** | 约束驱动的动态几何 | ConstraintSolver + 拖动实时更新 |
| **GeoGebra** | 教学资源生态 | ResourceLibrary + 内置资源包 |
| **SageMath** | 多引擎集成 | CASBus 自动路由到最优引擎 |
| **SageMath** | 交互式计算笔记本 | NotebookCell + 交互控件 |
| **Manim** | 声明式动画 | AnimationEngine + Timeline |
| **Manim** | 数学对象即动画对象 | 几何对象直接支持动画 |
| **Octave** | 矩阵是一等公民 | NumEngine 基于 NumPy/BLAS |
| **Octave** | MATLAB 语法兼容 | OctaveBridge 语法翻译 |
| **Maxima** | 符号计算深度 | MaximaProvider 集成 |
| **Maxima** | 特殊函数库 | 拉普拉斯/傅里叶/Z 变换 |

### 2. 架构原则

```
┌─────────────────────────────────────────────────────┐
│  原则 1: 多引擎后端，统一前端                          │
│  用户不需要知道计算在哪个引擎执行，                     │
│  系统自动选择最优引擎 (SageMath 理念)                  │
├─────────────────────────────────────────────────────┤
│  原则 2: 约束驱动，声明式交互                          │
│  用户定义"关系"而非"位置"，                            │
│  系统自动求解 (GeoGebra 理念)                         │
├─────────────────────────────────────────────────────┤
│  原则 3: 动画即一等公民                                │
│  所有数学对象都可动画化，                              │
│  动画可导出为多种格式 (Manim 理念)                     │
├─────────────────────────────────────────────────────┤
│  原则 4: 矩阵优先的数值层                              │
│  数值计算基于矩阵运算，                                │
│  底层 BLAS/LAPACK (Octave 理念)                       │
├─────────────────────────────────────────────────────┤
│  原则 5: 教学优先的交互设计                            │
│  滑块探索、逐步演示、资源分享，                        │
│  一切为教学服务 (GeoGebra 理念)                        │
└─────────────────────────────────────────────────────┘
```

---

## 依赖规划

### 新增依赖 (2.5)

```txt
# ── 阶段 2: CAS 总线 ──
maxima-bridge>=0.1.0        # Maxima Python 桥接 (或自行实现 subprocess 通信)
giacpy>=0.7.0               # Giac 符号计算 (可选)

# ── 阶段 3: 动画引擎 ──
manim>=0.18.0               # Manim 社区版 (可选，用于动画渲染)
Pillow>=10.0                # 图像处理 (GIF 导出)
imageio>=2.31.0             # 多格式图像/视频 IO

# ── 阶段 4: 数值引擎 ──
# (NumPy/SciPy 已在 requirements.txt 中，无需新增)

# ── 阶段 5: 笔记本 ──
nbformat>=5.9               # Notebook 格式支持 (可选)
weasyprint>=60.0            # HTML → PDF 导出 (可选)

# ── 阶段 6: 协作 ──
websockets>=12.0            # WebSocket 服务器
aiohttp>=3.9.0              # 异步 HTTP
```

---

## 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| **Maxima 安装复杂** | 用户需要额外安装 Maxima | 捆绑预编译 Maxima；或在 Docker 中运行；纯 SymPy 作为 fallback |
| **动画引擎性能** | 复杂动画卡顿 | 用 QThread 做后台渲染；复杂场景降级到低帧率 |
| **CAS 总线延迟** | 多引擎通信增加延迟 | 引擎进程池复用；超时机制；结果缓存 |
| **协作同步冲突** | 多人同时编辑冲突 | 采用 CRDT 算法 (如 Yjs)；优先单向广播模式 |
| **功能膨胀** | 2.5 计划过大 | 严格按阶段执行；每阶段独立可发布；核心功能优先 |
| **WebEngine 内存** | 3D/笔记本内存泄漏 | 严格的 deleteLater()；定期堆快照检查 |

---

## 立即可执行的行动 (第一个月)

1. **设计约束求解器数据结构** — 定义 `Constraint` 类和求解接口
2. **搭建 CAS 总线骨架** — 实现 `CASBus` 路由框架 + SymPy 适配器
3. **动画引擎原型** — 实现 `Create`/`FadeIn`/`Transform` 三个基础动画
4. **NumEngine 封装** — 封装 NumPy/SciPy 常用函数为统一接口
5. **笔记本单元格原型** — 实现 `CodeCell` + `MarkdownCell` 基本执行
