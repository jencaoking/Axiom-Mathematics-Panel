# MathLab (代号: Axiom)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)]()
[![Version](https://img.shields.io/badge/Version-2.7.0-orange.svg)]()

> **MathLab 2.7 (代号: Axiom)** 是一款交互式数学、AI 与 3D 教学桌面软件，集动态几何画板（2D 与 3D）、Python 编程学习环境、符号/数值计算、算法可视化、AI 具身学习、交互笔记本与插件扩展于一体。本版本在 2.6 基础上迎来了**工业级体验打磨**：引入全局异常守护与秒级崩溃恢复（AutoSaver）、丝滑的物理级动效引擎（包含惯性平移与平滑缩放）、智能磁吸辅助线以及丰富的数学彩蛋，朝着"工业级一体化数学实验室"的目标持续演进。

## 目录

- [特性](#特性)
- [快速开始](#快速开始)
- [功能演示](#功能演示)
- [目录结构](#目录结构)
- [技术架构](#技术架构)
- [核心模块](#核心模块)
- [插件系统](#插件系统)
- [开发指南](#开发指南)
- [测试](#测试)
- [许可证](#许可证)
- [联系方式](#联系方式)

---

## 特性

### 🎯 核心功能

| 功能 | 描述 |
|------|------|
| **动态几何画板 (2D)** | 基于依赖 DAG 的实时联动几何对象：点、线段、圆、多边形等 |
| **GeoGebra 级几何引擎** | 全新约束求解器，支持平行/垂直/共线/共圆/中点/相切等丰富约束 |
| **实时 3D 动态几何画板** | 基于 Three.js + Qt WebChannel，支持点/线/球的实时交互与约束求解 |
| **Python 编程环境** | 内置安全沙箱的交互式 Python REPL，支持代码补全、历史记录与子进程隔离 |
| **符号计算系统 (CAS)** | 基于 SymPy 的 CAS，并预留多引擎 CAS 总线 (SymPy / Maxima / Giac) 接入能力 |
| **数值计算引擎** | 面向 Octave 级矩阵运算与 BLAS/LAPACK 数值计算的 `NumEngine` + `OctaveBridge` |
| **交互笔记本** | SageMath 风格的多 Cell 笔记本（代码、Markdown、几何对象混合编排） |
| **JupyterLab 深度集成** | 嵌有原生 JupyterLab 单元，剥离冗余 UI 控件，支持与 Qt 宿主的跨进程双向 UDP 数据绑定与变量同步 |
| **算法可视化** | 排序、搜索、图论、凸包、K-Means 等算法的逐步动画演示 |
| **动画引擎** | 借鉴 Manim 的数学动画时间轴与缓动，支持关键帧与过渡曲线 |
| **AI 辅助学习** | 线性/多项式回归、K-Means/DBSCAN 聚类、ONNX 推理、可选 PyTorch 神经网络 |
| **全局命令面板** | VS Code 风格的全局命令控制台，支持模糊搜索、快捷执行 |
| **界面交互与丝滑微动画** | 自适应前景色 Feather Icons；侧边栏 200ms 柔和淡入淡出转场；几何画布的 **物理级惯性平移与平滑缩放** |
| **智能作图与彩蛋** | 支持 10像素 物理防抖的几何控制点磁吸、临时距离辅助线，以及“欧拉彩虹”等隐藏数学彩蛋 |
| **工业级容错与恢复** | **全局异常守护引擎 (Error Guardian)**，解析底层报错为人类语言；**30秒极速快照 AutoSaver**，崩溃重启一键恢复工作区 |
| **主题设置持久化** | 用户主题选择自动写入 `settings.json`，启动时秒级恢复 |
| **插件系统** | 统一 `Plugin` 基类 + 插件管理器，支持生命周期、热加载与扩展 API |

### 🔒 安全特性

- **进程隔离**: 用户代码在独立子进程中执行
- **超时控制**: 防止无限循环和死锁
- **资源限制**: 内存与执行时间双重保护
- **命名空间隔离**: 用户代码与系统环境分离
- **WebEngine 沙箱**: 浏览器侧渲染进程可显式释放，避免内存泄漏

### 🛠️ 技术栈

```
GUI框架:        PySide6 (Qt for Python) + Qt WebEngine (嵌入原生 JupyterLab)
跨进程通信:     UDP Socket 极速双向数据绑定 (Tx: 45678, Rx: 45679)
符号计算:       SymPy (预留 Maxima / Giac 多引擎总线)
数值计算:       NumPy / SciPy / OctaveBridge
机器学习:       scikit-learn / PyTorch (可选) / ONNX Runtime (可选)
可视化:         matplotlib / pyqtgraph / Three.js (3D) / ECharts (2D 插件)
动画:           自研 Animation Engine (Manim 风格关键帧)
笔记本:         自研 Notebook (SageMath 风格 Cell) & JupyterLab 混合沙箱
打包工具:       PyInstaller / Nuitka
```

---

## 快速开始

### 环境要求

- Python 3.10 或更高版本
- Windows 10+ / macOS 10.14+ / Ubuntu 20.04+
- 推荐至少 8 GB 内存（启用 3D 渲染与 AI 功能时建议 16 GB）

### 安装

#### 方式一：从源码运行（推荐）

```bash
# 克隆项目
git clone https://github.com/jencaoking/Axiom-Mathematics-Panel.git
cd Axiom-Mathematics-Panel

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate              # Linux/macOS
.\venv\Scripts\Activate.ps1           # Windows

# 安装核心依赖
pip install -r mathlab/requirements.txt

# 按需启用可选功能
pip install scikit-learn matplotlib pyqtgraph onnxruntime   # 轻量 AI + 可视化
# pip install torch --index-url https://download.pytorch.org/whl/cpu   # 神经网络

# 启动 MathLab
cd mathlab
python main.py
```

#### 方式二：使用 pip 安装（含可选扩展）

```bash
# 仅核心
pip install mathlab

# 选择性扩展
pip install "mathlab[ai]"            # scikit-learn + ONNX Runtime
pip install "mathlab[neural]"        # PyTorch
pip install "mathlab[visualization]" # matplotlib + pyqtgraph
pip install "mathlab[full]"          # 上述全部

# 启动
mathlab
```

### 开发模式运行

```bash
cd mathlab
python main.py
```

---

## 功能演示

### 几何作图（控制台 REPL）

```python
>>> draw_point(0, 0)            # 绘制点
>>> draw_point(3, 4)
>>> draw_segment(p1, p2)        # 绘制线段
>>> draw_circle(p1, 5)          # 绘制圆
```

### 符号计算

```python
>>> solve('x**2 - 4 = 0', 'x')    # 方程求解
>>> simplify('x**2 + 2*x**2')      # 表达式化简
>>> integrate('x**2', 'x')         # 不定积分
>>> differentiate('sin(x)', 'x')   # 求导
```

### 算法可视化

支持的可视化算法：

- **排序算法**: 冒泡排序、快速排序、归并排序
- **搜索算法**: 二分搜索、线性搜索
- **图论算法**: BFS、DFS、Dijkstra 最短路径
- **几何算法**: Graham 扫描凸包
- **机器学习**: K-Means 聚类

### AI / 机器学习

```python
>>> fit_linear(points)              # 线性回归
>>> fit_polynomial(points, 3)       # 多项式回归
>>> cluster_kmeans(data, n=3)       # K-Means 聚类
>>> generate_random_points(n=100)   # 生成随机数据
```

### 交互笔记本（Notebook）

```python
# 在 .mlnb 笔记本中混合编排代码、Markdown 与几何对象
nb = Notebook()
nb.add_markdown_cell("## 勾股定理演示")
nb.add_code_cell("draw_triangle(0, 0, 3, 0, 0, 4)")
nb.add_code_cell("simplify('a**2 + b**2 - c**2')")
nb.run_all()
```

### JupyterLab 双向交互与通信

MathLab v2.7 引入了原生 JupyterLab 嵌入及跨进程双向 UDP 通信。你可以直接在 Jupyter 单元格中使用 `mlab` 客户端：

```python
from mathlab_api import mlab

# 1. 往 Qt 画布绘制几何对象
mlab.draw_point('A', 2.0, 3.0)  # 在画布上绘制点 A(2.0, 3.0)，并在 Jupyter 空间同步注册 A_x=2.0, A_y=3.0
mlab.draw_point('B', 6.0, 3.0)
mlab.draw_line('L1', 'A', 'B')  # 绘制线段 AB

# 2. 当你在 Qt 端拖动几何点 A 时，Jupyter 内核中的 Python 变量 A_x 和 A_y 也会实时被修改！
# 你可以直接在单元格中访问这些变量：
print(A_x, A_y)
```

---

## 目录结构

```
Axiom-Mathematics-Panel/
├── main.py                       # 程序入口
├── setup.py                      # 安装配置（含 extras_require）
├── requirements.txt              # 核心依赖
├── requirements-optional.txt     # 可选依赖说明
├── mathlab_api.py                # Jupyter 侧 API 客户端 (跨进程双向通信核心)
│
├── mathlab/
│   ├── ui/                       # 前端界面模块
│   │   ├── main_window.py        # 主窗口布局
│   │   ├── canvas.py             # 几何画布 (QGraphicsView)
│   │   ├── geogebra_canvas.py    # GeoGebra 级几何画布
│   │   ├── code_editor.py        # 代码编辑器 (Monaco)
│   │   ├── jupyter_panel.py      # JupyterLab 面板 (动态 CSS 视觉融合)
│   │   ├── function_explorer_panel.py   # 函数 explorer 面板
│   │   ├── algebra_panel.py      # 代数侧边栏
│   │   ├── geogebra_algebra_panel.py    # GeoGebra 代数面板
│   │   ├── notebook_panel.py     # 笔记本面板
│   │   ├── markdown_cell.py      # Markdown 单元格
│   │   ├── console.py            # Python 控制台
│   │   ├── math_console.py       # 数学控制台
│   │   ├── properties_panel.py   # 属性面板
│   │   ├── command_bar.py        # 命令输入栏
│   │   ├── algo_vis_panel.py     # 算法可视化面板
│   │   ├── ai_tools_panel.py     # AI 工具面板
│   │   ├── interactive_widgets.py # 交互控件
│   │   ├── preferences_dialog.py # 设置对话框
│   │   ├── animations.py         # 动画辅助驱动
│   │   └── styles.qss            # 样式表
│   │
│   ├── core/                     # 后端内核模块
│   │   ├── geometry_engine.py        # 几何引擎 (DAG)
│   │   ├── geometry_engine_v1.py     # 几何引擎 v1 兼容层
│   │   ├── geogebra_engine.py        # GeoGebra 级约束求解引擎
│   │   ├── ipc_server.py             # UDP Socket 后台监听服务 (IPython -> Qt)
│   │   ├── ipc_client.py             # UDP Socket 发送客户端 (Qt -> IPython)
│   │   ├── jupyter_manager.py        # JupyterLab 子进程管理器 (URL 注入与端口管理)
│   │   ├── cas_provider.py           # 符号计算服务 (SymPy 封装)
│   │   ├── algo_animator.py          # 算法动画框架
│   │   ├── animation.py              # 通用动画引擎
│   │   ├── ai_manager.py             # AI 管理器
│   │   ├── python_repl.py            # Python REPL 内核
│   │   ├── sandbox.py                # 沙箱子进程
│   │   ├── sandbox_script.py         # 沙箱脚本
│   │   ├── async_workers.py          # 异步工作线程
│   │   ├── notebook.py               # 笔记本核心
│   │   ├── num_engine.py             # 数值计算引擎
│   │   ├── octave_bridge.py          # Octave 桥接
│   │   ├── plugin_base.py            # 插件基类
│   │   ├── plugin_manager.py         # 插件管理器
│   │   ├── command_manager.py        # 命令管理器
│   │   ├── extension_api.py          # 扩展 API
│   │   └── signals.py                # 信号定义
│   │
│   ├── data/                     # 数据存储
│   │   ├── project.py            # 项目文件管理
│   │   └── file_manager.py       # 文件分类与检索
│   │
│   ├── utils/                    # 工具函数
│   │   ├── latex_renderer.py     # LaTeX 渲染
│   │   ├── theme_manager.py      # 主题切换
│   │   ├── i18n_manager.py       # 国际化
│   │   ├── helpers.py            # 通用辅助函数
│   │   └── logger.py             # 全局日志
│   │
│   ├── plugins/                  # 内置插件
│   │   ├── plugin_3d_viewer/     # Three.js 3D 查看器
│   │   ├── echarts_viewer/       # ECharts 2D 图表
│   │   └── matrix_tools/         # 矩阵工具
│   │
│   ├── tests/                    # 单元测试
│   │   ├── test_core.py
│   │   ├── test_utils.py
│   │   ├── test_num_engine.py
│   │   ├── test_octave_bridge.py
│   │   ├── test_function_explorer.py
│   │   ├── test_analytic_geometry.py
│   │   ├── test_sandbox_security.py
│   │   └── test_session_context.py
│   │
│   ├── docs/                     # 项目文档
│   │   ├── api.md                # API 文档
│   │   ├── user_guide.md         # 用户指南
│   │   ├── analytic_geometry_guide.md
│   │   ├── function_explorer_guide.md
│   │   ├── function_explorer_implementation.md
│   │   ├── function_explorer_quickstart.md
│   │   ├── session_mode_guide.md
│   │   └── sandbox_security_refactor.md
│   │
│   ├── locale/                   # 国际化资源
│   │   ├── en.json
│   │   └── zh.json
│   │
│   └── resources/                # 资源文件
│       ├── icons/
│       ├── monaco-editor/
│       ├── markdown.html
│       └── monaco.html
│
├── LICENSE                       # Apache 2.0
├── DEVELOPMENT_PLAN.md           # 2.0 路线图
├── MATHLAB_2.5_PLAN.md           # 2.5 (Axiom) 路线图
└── README.md
```

---

## 技术架构

### 2.5 系统架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                        用户界面层 (UI Layer)                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │
│  │2D 画板 │ │3D 画板 │ │笔记本  │ │动画编辑│ │命令面板│ │AI 面板 │ │
│  │Canvas  │ │WebGL   │ │Notebook│ │Timeline│ │CmdBar  │ │AI Tools│ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│                       业务逻辑层 (Core Layer)                         │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Geometry Engine v2 │ CAS Bus   │ Animation  │  NumEngine      │  │
│  │ (DAG + Constraints)│ (SymPy +) │ (Manim 风格)│ (BLAS/Octave)  │  │
│  └────────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────┤
│                       扩展能力层 (Extension Layer)                    │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Plugin Manager │ Command Manager │ Extension API              │  │
│  └────────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────┤
│                       安全隔离层 (Sandbox Layer)                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Python REPL (subprocess)  │  WebEngine Sandbox  │  Plugin VM  │  │
│  └────────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────┤
│                       数据与协作层 (Data Layer)                       │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                       │
│  │ 项目   │ │ 资源库 │ │ 日志   │ │ i18n   │                       │
│  │(.mlnb) │ │        │ │系统    │ │        │                       │
│  └────────┘ └────────┘ └────────┘ └────────┘                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 核心类设计

#### GeometryEngine / GeoGebraEngine

```python
class GeometryEngine:
    def add_point(self, x, y, name=None) -> str
    def add_segment(self, point1_id, point2_id, name=None) -> str
    def add_circle(self, center_id, radius, name=None) -> str
    def add_polygon(self, point_ids, name=None) -> str
    def remove_object(self, obj_id) -> None
    def update_point(self, obj_id, x=None, y=None) -> None
    def get_objects_by_type(self, obj_type) -> list
    def solve_constraints(self) -> None
    def serialize_all(self) -> dict
    def deserialize_all(self, data) -> None

class GeoGebraEngine(GeometryEngine):
    """GeoGebra 级约束求解引擎：parallel / perpendicular / collinear /
    concyclic / midpoint / tangent / on_line / on_circle 等。"""
    def add_constraint(self, ctype, *args) -> str
    def remove_constraint(self, constraint_id) -> None
    def solve(self, tolerance=1e-8, max_iter=100) -> dict
```

#### CASProvider

```python
class CASProvider:
    def parse_expression(self, expr_str) -> Any
    def simplify(self, expr_str) -> dict
    def solve_equation(self, equation_str, variable) -> dict
    def differentiate(self, expr_str, variable) -> dict
    def integrate(self, expr_str, variable) -> dict
    def limit(self, expr_str, variable, point) -> dict
```

#### AlgoAnimator / Animation

```python
class AlgoAnimator:
    def load_algorithm(self, name, **params) -> bool
    def step(self) -> dict
    def reset(self) -> None
    def get_state(self) -> dict

class AnimationEngine:
    """Manim 风格关键帧动画：缓动函数 + 时间轴 + 多目标并行。"""
    def play(self, keyframes, easing="ease_in_out") -> None
    def pause(self) -> None
    def seek(self, t: float) -> None
```

#### NumEngine / OctaveBridge

```python
class NumEngine:
    """面向矩阵/数值计算的高层封装，底层走 NumPy / SciPy / LAPACK。"""
    def matmul(self, a, b)
    def eig(self, a)
    def svd(self, a)
    def solve_linear(self, A, b)

class OctaveBridge:
    """当系统已安装 Octave 时，可委托更重的数值任务执行。"""
    def call(self, script: str) -> dict
```

#### Notebook / PluginManager

```python
class Notebook:
    def add_markdown_cell(self, source) -> str
    def add_code_cell(self, source) -> str
    def run_cell(self, cell_id) -> Any
    def run_all(self) -> None
    def save(self, path) -> None
    def load(self, path) -> None

class PluginManager:
    def register(self, plugin: Plugin) -> None
    def activate(self, name) -> None
    def deactivate(self, name) -> None
    def list_plugins(self) -> list[dict]

class MathLabEngine:
    """Jupyter 端的 API 客户端与反向 IPC 控制器"""
    def __init__(self, send_port=45678, recv_port=45679)
    def draw_point(self, name: str, x: float, y: float) -> str
    def draw_line(self, name: str, p1_name: str, p2_name: str) -> str
    def clear(self) -> str
```

---

## 核心模块

### 几何引擎 (GeometryEngine)

基于有向无环图 (DAG) 的依赖管理，支持：
- 点、线段、圆、多边形等几何对象
- 约束求解和实时联动
- 对象序列化与反序列化

### GeoGebra 级几何引擎 (GeoGebraEngine)

继承自 `GeometryEngine`，提供：
- 平行、垂直、共线、共圆、中点、相切等约束
- 数值迭代求解器 (Newton-Raphson)
- 与代数面板双向同步

### 符号计算 (CASProvider)

封装 SymPy 提供：
- 表达式化简与展开
- 方程 (组) 求解
- 微积分运算
- LaTeX 输出
- 预留多引擎总线 (Maxima / Giac) 接入点

### 数值计算 (NumEngine / OctaveBridge)

- `NumEngine`：基于 NumPy / SciPy 的高性能矩阵运算
- `OctaveBridge`：可调用本地 Octave 处理更复杂的数值任务

### 笔记本 (Notebook)

SageMath 风格多 Cell 笔记本：
- Markdown 单元格（实时渲染）
- 代码单元格（沙箱执行）
- 几何对象嵌入与回放
- `.mlnb` 格式持久化

### 动画引擎 (AnimationEngine)

Manim 风格关键帧动画：
- 缓动函数 (linear, ease_in, ease_out, ease_in_out)
- 时间轴与并行/串行播放
- 与几何对象、UI 控件统一驱动

### 算法动画 (AlgoAnimator)

基于 Python 生成器的算法可视化框架：
- 排序算法：冒泡、快速、归并
- 搜索算法：二分、线性
- 图论算法：BFS、DFS、Dijkstra
- 几何算法：Graham 扫描凸包
- 机器学习：K-Means

### Python REPL

安全的交互式 Python 解释器：
- 命名空间隔离
- 超时控制
- 魔法命令 (`%clear`, `%history`, `%vars`)
- 代码补全（Jedi）

### AI 管理器 (AIManager)

集成多种机器学习功能：
- 线性 / 多项式回归
- K-Means / DBSCAN 聚类
- ONNX 模型推理
- PyTorch 神经网络（可选）

---

## 插件系统

MathLab 2.5 提供统一的插件体系，所有插件均位于 `mathlab/plugins/`：

| 插件 | 功能 |
|------|------|
| `plugin_3d_viewer` | 基于 Three.js + Qt WebChannel 的 3D 几何/曲面查看器 |
| `echarts_viewer` | 基于 ECharts 的 2D 交互图表 |
| `matrix_tools` | 矩阵运算辅助工具集 |

### 开发自定义插件

```python
# mathlab/plugins/my_plugin/main.py
from mathlab.core.plugin_base import Plugin

class MyPlugin(Plugin):
    name = "my_plugin"
    version = "0.1.0"

    def activate(self, ctx):
        # 注册面板、命令、菜单项等
        ctx.register_command("hello", self.say_hello)

    def deactivate(self, ctx):
        # 释放 WebEngine 等资源
        pass

    def say_hello(self, ctx):
        ctx.notify("Hello from MyPlugin!")
```

插件规范与扩展 API 详见 [docs/api.md](mathlab/docs/api.md)。

---

## 开发指南

### 开发环境搭建

```bash
# 1. 克隆仓库
git clone https://github.com/jencaoking/Axiom-Mathematics-Panel.git
cd Axiom-Mathematics-Panel

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate              # Linux/macOS
.\venv\Scripts\Activate.ps1           # Windows

# 3. 安装开发依赖
pip install -r mathlab/requirements.txt
pip install scikit-learn matplotlib pyqtgraph

# 4. 安装 pre-commit 钩子（可选）
pip install pre-commit
pre-commit install
```

### 代码规范

- **PEP 8**: Python 代码风格指南
- **类型提示**: 公共 API 添加类型标注
- **docstring**: 使用 Google 风格文档字符串

### 添加新功能

1. 在 `core/` 或 `utils/` 添加新模块；若是 UI 在 `ui/` 添加面板
2. 在 `tests/` 添加对应的测试文件
3. 在 `docs/` 更新相关文档
4. 若是可视化扩展，优先实现为插件
5. 提交代码，使用 Conventional Commits 规范

### 构建打包

```bash
# 使用 PyInstaller
pip install pyinstaller
pyinstaller mathlab/build_spec.spec

# 或使用 Nuitka
pip install nuitka
python -m nuitka --standalone --enable-plugin=pyside6 mathlab/main.py
```

### CI/CD

项目已配置 GitHub Actions：

- `.github/workflows/test.yml`：单元测试与覆盖率
- `.github/workflows/release.yml`：标签发布自动打包

---

## 测试

### 运行所有测试

```bash
cd mathlab
python -m pytest tests/ -v
```

### 运行特定测试

```bash
python -m pytest tests/test_core.py -v
python -m pytest tests/test_sandbox_security.py -v
python -m pytest tests/test_function_explorer.py -v
python -m pytest tests/test_octave_bridge.py -v
```

测试覆盖：

- 核心模块（几何、CAS、算法动画、AI、笔记本）
- 工具模块（主题、i18n、LaTeX、日志）
- 沙箱安全与会话隔离
- Octave 桥接与数值计算
- 函数 explorer 与解析几何

---

## 路线图

- **2.0 (已完成 · speed)**: 异步计算中枢、3D 渲染引擎、AI 集成、Fluent Design 主题
- **2.5 (已完成 · axiom)**: GeoGebra 级约束求解、笔记本、动画引擎、Octave 桥接、插件系统
- **2.6 (已完成 · Jupyter)**: 原生 JupyterLab 嵌入、跨进程双向 UDP IPC 通信、IPython 变量注入、隐藏 UI 的暗黑主题视觉融合
- **2.7 (已完成 · Polish)**: 全局容错恢复架构、惯性平移物理模型、QVariantAnimation 丝滑滚轮缩放、智能辅助线与磁吸、全新图标库、彩虹彩蛋
- **3.0 (规划中)**: Web 同步、多人协作、插件市场、云端教学资源

详见 [MATHLAB_2.5_PLAN.md](MATHLAB_2.5_PLAN.md) (及 2.7 版本实现)。

---

## 许可证

本项目采用 **Apache License 2.0** 开源许可证。完整许可证文本请参阅 [LICENSE](LICENSE) 文件。

---

## 联系方式

| 渠道 | 信息 |
|------|------|
| **项目主页** | https://github.com/jencaoking/Axiom-Mathematics-Panel |
| **问题反馈** | https://github.com/jencaoking/Axiom-Mathematics-Panel/issues |
| **讨论社区** | https://github.com/jencaoking/Axiom-Mathematics-Panel/discussions |
| **邮箱** | jencaoking@outlook.com |

---

## 致谢

MathLab 受益于以下开源项目：

- **SymPy** - 符号数学库
- **NumPy / SciPy** - 数值计算库
- **scikit-learn** - 机器学习库
- **PyTorch** - 深度学习框架
- **PySide6** - Qt for Python
- **Jedi** - Python 自动补全
- **Three.js** - 3D 渲染
- **ECharts** - 图表可视化
- **Monaco Editor** - 代码编辑

感谢所有贡献者的付出！

---

## 引用

如果您在学术项目中使用了 MathLab，请按以下格式引用：

```
@software{mathlab_jupyter,
  title  = {MathLab (Axiom): Interactive Mathematics, AI and 3D Teaching Software with JupyterLab Integration},
  author = {MathLab Team},
  version = {2.7.0},
  year   = {2026},
  url    = {https://github.com/jencaoking/Axiom-Mathematics-Panel}
}
```

---

<div align="center">

**Star us on GitHub** · **Report a Bug** · **Request a Feature**

Built with ❤️ by the MathLab Team

</div>