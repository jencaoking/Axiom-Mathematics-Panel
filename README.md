# MathLab (Axiom) — 多智能体交互式数学教育与科研桌面平台

<div align="center">
  <img src="https://via.placeholder.com/900x250.png?text=MathLab+3.5+-+The+Agentic+Mathematics+Platform" alt="MathLab Banner">
</div>

<div align="center">

**[English](README_EN.md) | 简体中文**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-red.svg)](https://doc.qt.io/qtforpython-6/)
[![Release](https://img.shields.io/badge/version-3.5.0-orange.svg)](https://github.com/jencaoking/Axiom-Mathematics-Panel/releases)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#测试)

</div>

---

**MathLab** 是一款面向未来的**多智能体交互式数学教育与科研桌面软件**。它突破了传统"套壳聊天框"的局限，打造了一套真正的工业级、L5 自动化自治的多智能体（Multi-Agent）桌面环境。

从基础的几何作图、代数求解，到复杂的定理证明和交互式教学大纲驱动，MathLab 完美融合了本地高性能图形引擎与云端大语言模型，并配以极具未来感的 Agentic UI。

---

## 目录

- [核心亮点](#-核心亮点l5-agentic-架构)
- [系统架构](#-系统架构)
- [功能模块详解](#-功能模块详解)
- [快速开始](#-快速开始)
- [开发指南](#-开发指南)
- [项目结构](#-项目结构)
- [技术栈](#-技术栈)
- [插件系统](#-插件系统)
- [API 接口](#-api-接口)
- [测试](#-测试)
- [构建与发布](#-构建与发布)
- [已知问题](#-已知问题)
- [路线图](#-路线图)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)
- [联系方式](#-联系方式)
- [致谢](#-致谢与引用)

---

## 核心亮点：L5 Agentic 架构

在 MathLab 3.5 的巅峰重构中，我们完成了四大核心维度的跃迁，打造了"自动驾驶级别"的 AI 教学基建：

### Phase 1: 视觉安全掌控 (Trust & Safety)

建立极客级别的状态栏与"影子状态（Shadow State）"。让 AI 的每一步计算与画笔调用都在监控之下，消除了未知状态带来的恐惧，实现安全的"草稿模式"。

- **实时状态监控**：所有 AI 操作在状态栏可见
- **影子状态**：后台记录 AI 行为轨迹
- **安全沙盒**：代码执行在隔离环境中

### Phase 2: 多智能体分工与容错自省 (Swarm Routing & Reflection)

摒弃了臃肿的"全能大模型"，引入了多专家协作的 **Swarm 架构**：

- **Transfer Protocol（交接流转协议）**：自动识别意图的智能路由
- **Fail Fast（快速重试）**：失败时自动重试机制
- **Self-Reflection（自我反思）**：当调用画板出错时，AI 能自主纠错并重新绘制

| 专家角色 | 职责 | 工具 |
|---------|------|------|
| 🟢 全科助教 | 前台接待，意图识别，任务分发 | Transfer Protocol |
| 📐 几何专家 | 几何作图、证明、求面积/角度 | execute_geometry_draw, highlight_geometry_elements |
| 📝 出题考官 | 智能出题、难度评估 | quiz_generator |
| 🧠 教研组长 | 教学规划、大纲生成 | submit_teaching_plan |

### Phase 3: 按需装载上下文 (JIT Context Assembly)

内置高精度动态上下文组装器（Context Assembler）：

- **告别 Token 费用爆炸**：仅在需要时注入相关上下文
- **避免注意力稀释**：解决 Lost in the Middle 问题
- **精准注入**：按需加载 LaTeX 规则、画布 JSON 或特定几何规则

### Phase 4: 思执分离教学双轨制 (Plan + Teach)

独创的教研、授课双层流转：

- **Plan（教学规划）**：教研组长专门拆解画布与题目，生成强类型的大纲清单（Syllabus JSON）
- **Teach（课堂讲解）**：授课讲师依据大纲，结合激光笔工具，进行无剧透的沉浸式苏格拉底互动教学

---

## 系统架构

### 五层架构体系

```
┌────────────────────────────────────────────────────────────────────────┐
│                       用户界面层 (UI Layer)                            │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│ │2D 画板 │ │3D 画板 │ │笔记本  │ │命令面板│ │Agent UI│ │Jupyter │   │
│ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
├────────────────────────────────────────────────────────────────────────┤
│                      业务逻辑层 (Core Layer)                           │
│ ┌────────────────────────────────────────────────────────────────┐    │
│ │ 几何引擎 (DAG)   CAS 数学总线   动画引擎   多智能体路由管理    │    │
│ └────────────────────────────────────────────────────────────────┘    │
├────────────────────────────────────────────────────────────────────────┤
│                      扩展与数据引擎 (Data & VM Layer)                  │
│ ┌────────────────────────────────────────────────────────────────┐    │
│ │ Plugin VM        NumEngine      WebEngine Sandbox              │    │
│ └────────────────────────────────────────────────────────────────┘    │
├────────────────────────────────────────────────────────────────────────┤
│                      安全隔离层 (Sandbox Layer)                        │
│ ┌────────────────────────────────────────────────────────────────┐    │
│ │  Python REPL (subprocess)  │  WebEngine Sandbox  │  Plugin VM │    │
│ └────────────────────────────────────────────────────────────────┘    │
├────────────────────────────────────────────────────────────────────────┤
│                      数据与协作层 (Data Layer)                         │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│ │ 项目文件 │ │ 资源库   │ │ WebSocket│ │ 云端同步 │                 │
│ │ (.mlproj)│ │(教学资源)│ │ 协作引擎 │ │(可选)    │                 │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘                 │
└────────────────────────────────────────────────────────────────────────┘
```

### 核心引擎详解

#### GeometryEngine（几何引擎）

基于有向无环图（DAG）的依赖管理，支持几何对象的创建、更新和约束求解。

**支持的几何对象：**
- **基础对象**：点（Point）、线段（Segment）、直线（Line）、圆（Circle）
- **圆锥曲线**：椭圆（Ellipse）、双曲线（Hyperbola）、抛物线（Parabola）、一般圆锥曲线（ConicSection）
- **函数图像**：显式函数（FunctionPlot）、隐函数（ImplicitPlot）、极坐标函数（PolarPlot）
- **高级对象**：多边形（Polygon）、轨迹（Locus）

**核心特性：**
- DAG 依赖追踪：对象之间建立父子关系
- 实时更新：修改父对象时子对象自动重算
- 约束求解：支持平行、垂直、相切等几何约束

#### CASProvider（符号计算引擎）

封装 SymPy 提供表达式化简、方程求解、微积分运算等功能。

**支持的运算：**
```python
solve(equation, var)           # 方程求解
simplify(expression)           # 表达式化简
integrate(expression, var)     # 不定积分
differentiate(expression, var) # 求导
limit(expression, var, point)  # 极限
factor(expression)             # 因式分解
series(expression, var, point) # 级数展开
```

#### Agent Registry & Tools（多智能体系统）

内建丰富的天团专家和数十种原子操作 Tool 调用：

| 专家 ID | 名称 | 图标 | 专属工具 |
|---------|------|------|----------|
| `general` | 全科助教 | 🟢 | Transfer Protocol |
| `geometry` | 几何专家 | 📐 | execute_geometry_draw, highlight_geometry_elements |
| `quiz` | 出题考官 | 📝 | quiz_generator |
| `planner` | 教研组长 | 🧠 | submit_teaching_plan |

#### Notebook（交互笔记本）

SageMath 风格的 Cell 笔记本，支持 Markdown 和代码单元格的混合编排。

**单元格类型：**
- `CODE` — Python/MathLab 代码
- `MARKDOWN` — 富文本（支持 LaTeX 公式）
- `MATH` — 数学公式（自动渲染）
- `GEO` — 嵌入式几何画板
- `PLOT` — 函数/几何图形

---

## 功能模块详解

### 1. 2D 几何画板

提供专业的几何作图与交互功能：

- **自由绘制**：点、线段、直线、圆、多边形
- **约束系统**：平行、垂直、相切、共线、共圆
- **测量工具**：距离、角度、面积、周长、斜率
- **变换操作**：反射、旋转、平移、缩放
- **轨迹追踪**：实时绘制点的运动轨迹

### 2. 3D 渲染引擎

基于 Three.js + PyQtWebEngine 的 3D 可视化：

- **曲面绘制**：参数曲面、隐函数曲面
- **向量场**：三维向量场可视化
- **等值面**：等值面渲染
- **交互控制**：旋转、缩放、平移

### 3. 算法可视化

内置多种经典算法的动态演示：

- **排序算法**：冒泡排序、快速排序、归并排序、堆排序
- **图论算法**：Dijkstra 最短路径、BFS/DFS 遍历
- **动态规划**：背包问题、最长公共子序列
- **树操作**：二叉树遍历、AVL 旋转

### 4. AI 对话系统

基于大语言模型的智能对话：

- **意图识别**：自动判断用户需求（作图/出题/讲解）
- **工具调用**：Function Calling 实现画板操作
- **上下文管理**：JIT Context Assembly 按需加载
- **多轮对话**：支持上下文记忆

### 5. Jupyter 集成

内嵌 JupyterLab 的交互式计算环境：

- **代码执行**：实时运行 Python 代码
- **LaTeX 渲染**：数学公式即时显示
- **变量同步**：Python ↔ Qt 双向通信
- **文件操作**：支持 .ipynb 文件读写

### 6. 命令面板

快速访问所有功能的统一入口：

- **快捷键**：Ctrl+K / Ctrl+Shift+P
- **模糊搜索**：输入关键词快速定位
- **最近使用**：记录常用操作
- **自定义命令**：支持用户扩展

---

## 快速开始

### 环境要求

- **Python**：3.10 或更高版本
- **操作系统**：Windows 10+、macOS 12+、Ubuntu 20.04+
- **内存**：建议 8GB 以上
- **磁盘空间**：至少 2GB 可用空间

### 安装步骤

#### 方式一：从源码安装（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/jencaoking/Axiom-Mathematics-Panel.git
cd Axiom-Mathematics-Panel

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 4. 安装依赖
pip install -r mathlab/requirements.txt

# 5. 安装开发工具（可选）
pip install pre-commit
pre-commit install
```

#### 方式二：使用预编译包

从 [Releases](https://github.com/jencaoking/Axiom-Mathematics-Panel/releases) 页面下载对应平台的安装包：

- **Windows**：`MathLab-3.5.0-win64.exe`
- **macOS**：`MathLab-3.5.0-macos.dmg`
- **Linux**：`MathLab-3.5.0-linux.AppImage`

### 启动应用

```bash
# 开发模式
python mathlab/main.py

# 或使用模块方式
python -m mathlab
```

### 快速验证

启动后，在命令面板中输入以下命令验证安装：

```python
# 测试几何引擎
draw_point("A", 0, 0)
draw_point("B", 3, 4)
draw_line("AB", "A", "B")

# 测试 CAS
from mathlab.core.cas_provider import CASProvider
cas = CASProvider()
result = cas.solve_equation("x**2 - 4", "x")
print(result)  # 应输出 [-2, 2]
```

---

## 开发指南

### 开发环境搭建

```bash
# 安装开发依赖
pip install -r mathlab/requirements.txt
pip install -r mathlab/requirements-optional.txt

# 安装 pre-commit hooks
pre-commit install
```

### IDE 配置

#### VS Code

推荐安装以下扩展：
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Python Indent (KevinRose.vsc-python-indent)

项目已包含 `.vscode/settings.json` 配置。

#### PyCharm

1. 打开项目根目录
2. 配置 Python 解释器为 `venv/Scripts/python`
3. 标记 `mathlab` 为 Sources Root

### 代码规范

- **格式化**：使用 `black` 进行代码格式化
- **Lint**：使用 `ruff` 进行代码检查
- **类型注解**：推荐使用 type hints
- **文档字符串**：使用 Google 风格

```bash
# 格式化代码
black mathlab/

# 代码检查
ruff check mathlab/

# 类型检查（可选）
mypy mathlab/
```

### 调试技巧

#### 使用 VS Code 调试

项目包含 `.vscode/launch.json`，可直接按 F5 启动调试。

#### 日志系统

MathLab 内置完整的日志系统：

```python
from mathlab.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("这是一条信息日志")
logger.debug("这是一条调试日志")
logger.warning("这是一条警告日志")
logger.error("这是一条错误日志")
```

日志文件位于 `mathlab/logs/` 目录。

### 提交规范

使用 Conventional Commits 规范：

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

---

## 项目结构

```
Axiom-Mathematics-Panel/
├── mathlab/                          # 主包目录
│   ├── __init__.py                   # 包初始化
│   ├── main.py                       # 应用入口
│   ├── config/                       # 配置文件
│   │   └── settings.json             # 默认配置
│   ├── core/                         # 核心引擎
│   │   ├── agent_registry.py         # 多智能体注册表
│   │   ├── ai_manager.py             # AI 管理器
│   │   ├── ai_provider_config.py     # AI 提供商配置
│   │   ├── ai_tools.py               # AI 工具定义
│   │   ├── algo_animator.py          # 算法动画器
│   │   ├── animation.py              # 动画引擎
│   │   ├── async_workers.py          # 异步工作线程
│   │   ├── canvas_tracker.py         # 画布状态追踪
│   │   ├── cas_provider.py           # CAS 符号计算
│   │   ├── command_manager.py        # 命令管理器
│   │   ├── context_assembler.py      # 上下文组装器
│   │   ├── error_manager.py          # 错误管理器
│   │   ├── extension_api.py          # 扩展 API
│   │   ├── geogebra_engine.py        # GeoGebra 兼容引擎
│   │   ├── geometry_engine.py        # 几何引擎核心
│   │   ├── geometry_engine_v1.py     # 几何引擎 v1
│   │   ├── geometry_helpers.py       # 几何辅助函数
│   │   ├── ipc_client.py             # IPC 客户端
│   │   ├── ipc_server.py             # IPC 服务端
│   │   ├── jupyter_manager.py        # Jupyter 管理器
│   │   ├── memory_manager.py         # 内存管理器
│   │   ├── notebook.py               # 笔记本核心
│   │   ├── num_engine.py             # 数值计算引擎
│   │   ├── octave_bridge.py          # Octave 桥接
│   │   ├── plugin_base.py            # 插件基类
│   │   ├── plugin_manager.py         # 插件管理器
│   │   ├── prompt_manager.py         # 提示词管理器
│   │   ├── python_repl.py            # Python REPL
│   │   ├── sandbox.py                # 沙盒环境
│   │   ├── sandbox_script.py         # 沙盒脚本
│   │   ├── signals.py                # Qt 信号定义
│   │   └── smart_guides.py           # 智能辅助线
│   ├── ui/                           # 用户界面
│   │   ├── ai_cursor.py              # AI 光标
│   │   ├── ai_tools_panel.py         # AI 工具面板
│   │   ├── algebra_panel.py          # 代数面板
│   │   ├── algo_vis_panel.py         # 算法可视化面板
│   │   ├── animated_widgets.py       # 动画组件
│   │   ├── animations.py             # UI 动画
│   │   ├── canvas.py                 # 2D 画布
│   │   ├── code_editor.py            # 代码编辑器
│   │   ├── command_bar.py            # 命令栏
│   │   ├── console.py                # 控制台
│   │   ├── easter_eggs.py            # 彩蛋
│   │   ├── floating_bubble.py        # 浮动气泡
│   │   ├── function_explorer_panel.py # 函数探索器
│   │   ├── geogebra_algebra_panel.py # GeoGebra 代数面板
│   │   ├── geogebra_canvas.py        # GeoGebra 画布
│   │   ├── geometry_panel.py         # 几何面板
│   │   ├── interactive_widgets.py    # 交互组件
│   │   ├── jupyter_panel.py          # Jupyter 面板
│   │   ├── latex_chat_widget.py      # LaTeX 聊天组件
│   │   ├── main_window.py            # 主窗口
│   │   ├── markdown_cell.py          # Markdown 单元格
│   │   ├── math_console.py           # 数学控制台
│   │   ├── notebook_panel.py         # 笔记本面板
│   │   ├── omni_bar.py               # 全能栏
│   │   ├── preferences_dialog.py     # 偏好设置对话框
│   │   ├── properties_panel.py       # 属性面板
│   │   ├── quiz_panel.py             # 测验面板
│   │   ├── styles.qss                # QSS 样式表
│   │   └── icons/                    # 图标资源
│   ├── plugins/                      # 内置插件
│   │   ├── echarts_viewer/           # ECharts 图表
│   │   ├── matrix_tools/             # 矩阵工具
│   │   └── plugin_3d_viewer/         # 3D 查看器
│   ├── data/                         # 数据层
│   │   └── project.py                # 项目管理
│   ├── utils/                        # 工具函数
│   │   └── logger.py                 # 日志系统
│   ├── resources/                    # 资源文件
│   │   └── icons/                    # 应用图标
│   ├── tests/                        # 测试用例
│   ├── docs/                         # 文档
│   ├── locale/                       # 国际化
│   ├── logs/                         # 日志目录
│   ├── scripts/                      # 脚本工具
│   └── requirements.txt              # 依赖列表
├── .github/                          # GitHub 配置
│   └── workflows/                    # CI/CD 工作流
│       ├── test.yml                  # 测试工作流
│       ├── release.yml               # 发布工作流
│       └── release_2.6.yml           # 2.6 发布工作流
├── build/                            # 构建输出
├── dist/                             # 发布包
├── venv/                             # 虚拟环境
├── mathlab_api.py                    # API 接口
├── pyproject.toml                    # 项目配置
├── requirements.txt                  # 根依赖
├── mathlab.spec                      # PyInstaller 配置
├── LICENSE                           # Apache 2.0 许可证
├── README.md                         # 项目说明
├── BUGS.md                           # Bug 追踪
├── DEVELOPMENT_PLAN.md               # 开发计划
└── MATHLAB_2.5_PLAN.md               # 2.5 版本规划
```

---

## 技术栈

### 核心依赖

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **GUI 框架** | PySide6 | ≥6.5.0 | Qt for Python，跨平台桌面 UI |
| **符号计算** | SymPy | ≥1.12 | CAS 符号计算引擎 |
| **数值计算** | NumPy | ≥1.26 | 数组运算、线性代数 |
| **科学计算** | SciPy | ≥1.11 | 高级数值算法 |
| **图论** | NetworkX | ≥3.1 | 图数据结构与算法 |
| **代码补全** | Jedi | ≥0.19 | Python 代码智能提示 |
| **进程监控** | psutil | ≥5.9 | 系统资源监控 |

### Jupyter 集成

| 组件 | 版本 | 用途 |
|------|------|------|
| JupyterLab | ≥4.0 | 交互式计算环境 |
| Jupyter Client | ≥8.0 | Jupyter 协议客户端 |
| ipykernel | ≥6.0 | IPython 内核 |
| Jupyter Server | ≥2.0 | Jupyter 服务器 |

### AI 集成

| 组件 | 用途 |
|------|------|
| OpenAI API | GPT 系列模型调用 |
| Function Calling | 工具调用协议 |
| Streaming | 流式响应 |

### 可选依赖

| 组件 | 用途 |
|------|------|
| Three.js | 3D 渲染 |
| ECharts | 高级图表 |
| Monaco Editor | 代码编辑器 |

### 开发工具

| 工具 | 用途 |
|------|------|
| pytest | 单元测试 |
| pytest-qt | Qt 测试支持 |
| pre-commit | Git hooks |
| black | 代码格式化 |
| ruff | 代码检查 |

---

## 插件系统

MathLab 支持插件扩展，内置以下插件：

### 内置插件

#### 1. 3D Viewer（plugin_3d_viewer）

基于 Three.js + PyQtWebEngine 的 3D 可视化插件。

**功能：**
- 参数曲面绘制
- 隐函数曲面
- 向量场可视化
- 交互式旋转/缩放

#### 2. ECharts Viewer（echarts_viewer）

集成 ECharts 的高级图表插件。

**功能：**
- 柱状图、折线图、饼图
- 散点图、热力图
- 实时数据更新
- 双向事件交互

#### 3. Matrix Tools（matrix_tools）

矩阵运算工具插件。

**功能：**
- 矩阵可视化
- 特征值/特征向量
- SVD 分解
- 矩阵运算

### 开发自定义插件

```python
from mathlab.core.plugin_base import MathLabPlugin

class MyPlugin(MathLabPlugin):
    """自定义插件示例"""
    
    def __init__(self, api):
        super().__init__(api)
        self.name = "My Plugin"
        self.version = "1.0.0"
    
    def activate(self):
        """插件激活时调用"""
        self.api.register_command("my_command", self.my_handler)
    
    def deactivate(self):
        """插件停用时调用"""
        self.api.unregister_command("my_command")
    
    def my_handler(self, *args):
        """命令处理器"""
        # 你的逻辑
        pass
```

---

## API 接口

### MathLabEngine API

提供 Python 脚本调用 MathLab 功能的 API：

```python
from mathlab_api import MathLabEngine

# 初始化引擎
mlab = MathLabEngine()

# 绘制点
mlab.draw_point("A", 0, 0)
mlab.draw_point("B", 3, 4)

# 绘制线段
mlab.draw_line("AB", "A", "B")

# 清空画布
mlab.clear()
```

### IPC 通信

MathLab 使用 UDP 协议进行进程间通信：

- **发送端口**：45678（Python → Qt）
- **接收端口**：45679（Qt → Python）

### 变量同步

Qt 界面与 Python 内核之间的变量自动同步：

```python
# 在 Python 中修改变量，Qt 界面自动更新
mlab._handle_qt_msg({
    "cmd": "sync_var",
    "name": "my_variable",
    "val": 42
})
```

---

## 测试

### 运行测试

```bash
# 运行所有测试
cd mathlab
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_geometry.py -v

# 运行带标记的测试
python -m pytest -m "not slow"

# 生成覆盖率报告
python -m pytest --cov=mathlab tests/
```

### 测试配置

测试配置位于 `pyproject.toml`：

```toml
[tool.pytest.ini_options]
testpaths = ["mathlab/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "slow: marks tests as slow",
    "qt: marks tests that require Qt event loop",
]
```

### 测试分类

| 类别 | 说明 | 命令 |
|------|------|------|
| 单元测试 | 核心引擎测试 | `pytest tests/unit/` |
| 集成测试 | 模块间交互测试 | `pytest tests/integration/` |
| UI 测试 | Qt 界面测试 | `pytest -m qt tests/` |
| 性能测试 | 性能基准测试 | `pytest -m slow tests/` |

---

## 构建与发布

### 使用 PyInstaller 构建

```bash
# 构建可执行文件
pyinstaller mathlab/build_spec.spec

# 输出位于 dist/ 目录
```

### 使用 Nuitka 构建

```bash
# Nuitka 构建（性能更优）
python -m nuitka --standalone --enable-plugin=pyside6 mathlab/main.py
```

### CI/CD 工作流

项目使用 GitHub Actions 进行自动化：

#### test.yml - 测试工作流

- **触发条件**：Push 到 main/develop，Pull Request
- **执行内容**：代码检查、单元测试、覆盖率报告

#### release.yml - 发布工作流

- **触发条件**：创建 Tag（v*）
- **执行内容**：构建多平台发布包、创建 GitHub Release

### 版本管理

版本号遵循语义化版本（Semantic Versioning）：

- **主版本号**：不兼容的 API 变更
- **次版本号**：向下兼容的功能新增
- **修订号**：向下兼容的问题修复

---

## 已知问题

详见 [BUGS.md](BUGS.md)，包含 78 个已知问题的详细追踪。

### P0 致命问题（已修复）

- ✅ `ai_manager.py:171` — Tool call 参数从未 JSON 反序列化
- ✅ `ai_manager.py:226,255` — `QThread.wait()` 无超时导致 GUI 冻结

### P1 高危问题（部分未修复）

- ⚠️ `ai_manager.py:253-270` — 旧 QThread worker 未 `deleteLater()`
- ⚠️ `sandbox.py:113-114` — `stdin.write()` 无 try/except
- ⚠️ `geometry_engine.py:364-365` — 线段交点忽略线段边界

---

## 路线图

### 版本历史

| 版本 | 代号 | 主要特性 |
|------|------|----------|
| **1.0** | - | 基础几何画板 |
| **2.0** | speed | 异步计算中枢、3D 渲染引擎、AI 集成 |
| **2.5** | axiom | GeoGebra 约束求解、笔记本、动画引擎、插件系统 |
| **3.0** | - | Agentic UI、NL2Draw 自然语言作图、视觉错题本 |
| **3.5** | - | 🌟 多智能体架构、思执分离大纲双轨制、纠错重试环 |

### 未来规划

#### 4.0 计划

- **Web 同步**：跨设备数据同步
- **多人协作**：实时协作编辑
- **插件市场**：第三方插件生态
- **云端教学资源**：在线资源库

#### 长期愿景

- 支持更多数学引擎（Maxima、Giac）
- 完整的动画导出系统（GIF/MP4/SVG）
- 教学资源社区
- 移动端支持

---

## 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. **Fork** 本仓库
2. **创建特性分支**：`git checkout -b feature/amazing-feature`
3. **提交更改**：`git commit -m 'feat: Add amazing feature'`
4. **推送到分支**：`git push origin feature/amazing-feature`
5. **创建 Pull Request**

### 贡献类型

- 🐛 **Bug 修复**：修复已知问题
- ✨ **新功能**：添加新的特性
- 📝 **文档**：完善项目文档
- 🧪 **测试**：增加测试覆盖率
- 🎨 **UI/UX**：界面和交互优化
- 🔧 **重构**：代码质量改进

### 开发规范

- 遵循 Conventional Commits 规范
- 确保所有测试通过
- 更新相关文档
- 保持代码风格一致

---

## 许可证

本项目采用 **Apache License 2.0** 开源许可证。

```
Copyright 2024 MathLab Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## 联系方式

| 渠道 | 信息 |
|------|------|
| **项目主页** | https://github.com/jencaoking/Axiom-Mathematics-Panel |
| **问题反馈** | https://github.com/jencaoking/Axiom-Mathematics-Panel/issues |
| **讨论社区** | https://github.com/jencaoking/Axiom-Mathematics-Panel/discussions |
| **邮箱** | jencaoking@outlook.com |

---

## 致谢与引用

MathLab 受益于以下卓越的开源项目与框架：

- **[PySide6](https://doc.qt.io/qtforpython-6/)** — Qt for Python
- **[SymPy](https://www.sympy.org/)** — 符号计算库
- **[NumPy](https://numpy.org/)** — 数值计算基础
- **[SciPy](https://scipy.org/)** — 科学计算库
- **[NetworkX](https://networkx.org/)** — 图论库
- **[Jupyter](https://jupyter.org/)** — 交互式计算环境
- **[Three.js](https://threejs.org/)** — 3D 渲染
- **[ECharts](https://echarts.apache.org/)** — 数据可视化

### 引用本项目

如果您在学术研究中使用了 MathLab，请引用：

```bibtex
@software{mathlab_jupyter,
  title  = {MathLab (Axiom): Interactive Mathematics, AI and 3D Teaching Software},
  author = {MathLab Team},
  version = {3.5.0},
  year   = {2026},
  url    = {https://github.com/jencaoking/Axiom-Mathematics-Panel}
}
```

---

<div align="center">

**Star us on GitHub** · **Report a Bug** · **Request a Feature**

Built with ❤️ by the MathLab Team

</div>
