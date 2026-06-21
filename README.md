# MathLab

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)]()
[![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)]()

> **MathLab** 是一款交互式数学与AI教学桌面软件，集动态几何画板、Python编程学习环境、算法可视化和AI辅助学习于一体。

## 目录

- [特性](#特性)
- [快速开始](#快速开始)
- [功能演示](#功能演示)
- [目录结构](#目录结构)
- [技术架构](#技术架构)
- [核心模块](#核心模块)
- [开发指南](#开发指南)
- [测试](#测试)
- [许可证](#许可证)
- [联系方式](#联系方式)

---

## 特性

### 🎯 核心功能

| 功能 | 描述 |
|------|------|
| **动态几何画板** | 支持点、线段、圆、多边形等几何对象，基于依赖DAG实现实时联动 |
| **Python编程环境** | 内置安全沙箱的交互式Python REPL，支持代码补全和历史记录 |
| **符号计算系统** | 基于SymPy的完整CAS，支持化简、求导、积分、方程求解 |
| **算法可视化** | 排序、搜索、图论等算法的逐步动画演示 |
| **AI辅助学习** | 线性/多项式回归、K-Means聚类、神经网络训练等ML功能 |
| **全局命令面板** | VS Code 风格的全局命令控制台，支持模糊搜索、快捷执行 |
| **界面交互与微动画**| 引入自适应前景色 Feather Icons 矢量图标；基于 `QPropertyAnimation` 对侧边栏提供 200ms 柔和淡入淡出转场 |
| **主题设置持久化** | 用户的主题选择自动写入 `settings.json` 配置文件，并在启动时秒级恢复历史记忆 |

### 🔒 安全特性

- **进程隔离**: 用户代码在独立子进程中执行
- **超时控制**: 防止无限循环和死锁
- **资源限制**: 内存和执行时间双重保护
- **命名空间隔离**: 用户代码与系统环境分离

### 🛠️ 技术栈

```
GUI框架:     PySide6 (Qt for Python)
符号计算:    SymPy
数值计算:    NumPy / SciPy
机器学习:    scikit-learn / PyTorch / ONNX Runtime
可视化:      matplotlib / pyqtgraph / networkx
打包工具:    PyInstaller
```

---

## 快速开始

### 环境要求

- Python 3.10 或更高版本
- Windows 10+ / macOS 10.14+ / Ubuntu 20.04+

### 安装

#### 方式一：从源码安装

```bash
# 克隆项目
git clone https://github.com/jencaoking/Axiom-Mathematics-Panel.git
cd Axiom-Mathematics-Panel

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\Activate.ps1  # Windows

# 安装依赖
pip install -r mathlab/requirements.txt

# 运行
cd mathlab
python main.py
```

#### 方式二：使用 pip 安装

```bash
pip install mathlab
mathlab
```

### 开发模式运行

```bash
cd mathlab
python main.py
```

---

## 功能演示

### 几何作图

```python
# 在控制台输入以下命令
>>> draw_point(0, 0)    # 绘制点
>>> draw_point(3, 4)    # 绘制点
>>> draw_segment(p1, p2)  # 绘制线段
>>> draw_circle(p1, 5)   # 绘制圆
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
- **图论算法**: BFS、DFS、Dijkstra最短路径
- **几何算法**: 凸包
- **机器学习**: K-Means聚类

### AI机器学习

```python
>>> fit_linear(points)              # 线性回归
>>> fit_polynomial(points, 3)       # 多项式回归
>>> cluster_kmeans(data, n=3)       # K-Means聚类
>>> generate_random_points(n=100)   # 生成随机数据
```

---

## 目录结构

```
mathlab/
├── main.py                    # 程序入口
├── setup.py                   # 安装配置
├── requirements.txt           # 依赖列表
│
├── ui/                        # 前端界面模块
│   ├── __init__.py
│   ├── main_window.py         # 主窗口布局
│   ├── canvas.py               # 几何画布 (QGraphicsView)
│   ├── code_editor.py          # 代码编辑器
│   ├── function_explorer_panel.py  # 函数 explorer 面板
│   ├── algebra_panel.py        # 代数侧边栏
│   ├── console.py              # Python 控制台
│   ├── properties_panel.py     # 属性面板
│   ├── command_bar.py          # 命令输入栏
│   ├── algo_vis_panel.py       # 算法可视化面板
│   ├── ai_tools_panel.py       # AI 工具面板
│   ├── preferences_dialog.py   # 设置对话框
│   ├── animations.py           # 动画辅助驱动 (淡入淡出过渡)
│   └── styles.qss              # 样式表
│
├── core/                      # 后端内核模块
│   ├── __init__.py
│   ├── geometry_engine.py      # 几何引擎 (DAG 依赖管理)
│   ├── cas_provider.py          # 符号计算服务 (SymPy 封装)
│   ├── algo_animator.py         # 算法动画框架
│   ├── ai_manager.py            # AI 管理器
│   ├── python_repl.py           # Python 控制台内核
│   ├── sandbox.py              # 沙箱子进程
│   ├── sandbox_script.py       # 沙箱脚本
│   ├── async_workers.py        # 异步工作线程
│   └── signals.py              # 信号定义
│
├── data/                      # 数据存储
│   ├── __init__.py
│   ├── project.py              # 项目文件管理
│   └── file_manager.py         # 文件分类与检索
│
├── utils/                     # 工具函数
│   ├── __init__.py
│   ├── latex_renderer.py       # LaTeX 渲染
│   ├── theme_manager.py        # 主题切换
│   ├── i18n_manager.py         # 国际化
│   └── helpers.py              # 通用辅助函数
│
├── tests/                     # 单元测试
│   ├── __init__.py
│   ├── test_core.py            # 核心模块测试
│   └── test_utils.py           # 工具模块测试
│
├── docs/                      # 文档
│   ├── api.md                  # API 文档
│   └── user_guide.md           # 用户指南
│
├── locale/                    # 国际化资源
│   ├── en.json                 # 英文
│   └── zh.json                 # 中文
│
├── resources/                 # 资源文件
│   └── resources.qrc          # Qt 资源文件
│
├── LICENSE                    # Apache 2.0 许可证
└── docs/                      # 项目文档
    ├── analytic_geometry_guide.md       # 解析几何指南
    ├── function_explorer_guide.md       # 函数 explorer 指南
    ├── function_explorer_implementation.md  # 函数 explorer 实现
    ├── function_explorer_quickstart.md  # 函数 explorer 快速开始
    ├── session_mode_guide.md            # 会话模式指南
    └── sandbox_security_refactor.md     # 沙箱安全重构文档
```

---

## 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户界面层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │  几何画布   │  │  代数面板   │  │  控制台     │  │ AI面板  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                         核心业务层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │  几何引擎   │  │  CAS计算    │  │ 算法动画    │  │ AI管理  │ │
│  │  (DAG)     │  │  (SymPy)   │  │ (生成器)   │  │ (ML)    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                         安全隔离层                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Python REPL + 沙箱进程                    ││
│  └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                         数据持久层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  项目管理   │  │  文件管理   │  │  主题配置   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### 核心类设计

#### GeometryEngine

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

#### AlgoAnimator

```python
class AlgoAnimator:
    def load_algorithm(self, name, **params) -> bool
    def step(self) -> dict
    def reset(self) -> None
    def get_state(self) -> dict
```

---

## 核心模块

### 几何引擎 (GeometryEngine)

基于有向无环图(DAG)的依赖管理，支持：
- 点、线段、圆、多边形等几何对象
- 约束求解和实时联动
- 对象序列化与反序列化

### 符号计算 (CASProvider)

封装SymPy提供：
- 表达式化简与展开
- 方程(组)求解
- 微积分运算
- LaTeX输出

### 算法动画 (AlgoAnimator)

基于Python生成器的算法可视化框架：
- 排序算法：冒泡、快速、归并
- 搜索算法：二分、线性
- 图论算法：BFS、DFS、Dijkstra
- 几何算法：Graham扫描凸包
- 机器学习：K-Means

### Python REPL

安全的交互式Python解释器：
- 命名空间隔离
- 超时控制
- 魔法命令（%clear, %history, %vars）
- 代码补全

### AI管理器 (AIManager)

集成多种机器学习功能：
- 线性/多项式回归
- K-Means/DBSCAN聚类
- ONNX模型推理
- PyTorch神经网络

---

## 开发指南

### 开发环境搭建

```bash
# 1. 克隆仓库
git clone https://github.com/your-repo/mathlab.git
cd mathlab

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\Activate.ps1  # Windows

# 3. 安装开发依赖
pip install -r mathlab/requirements.txt

# 4. 安装pre-commit钩子（可选）
pip install pre-commit
pre-commit install
```

### 代码规范

项目遵循以下代码规范：
- **PEP 8**: Python代码风格指南
- **类型提示**: 公共API添加类型标注
- **docstring**: 使用Google风格文档字符串

### 添加新功能

1. **创建新模块**: 在 `core/` 或 `utils/` 添加新模块
2. **编写测试**: 在 `tests/` 添加对应的测试文件
3. **更新文档**: 在 `docs/` 更新相关文档
4. **提交代码**: 使用 conventional commits 规范

### 构建打包

```bash
# 使用 Nuitka 打包（需要额外安装）
pip install nuitka
python -m nuitka --standalone --enable-plugin=pyside6 mathlab/main.py
```

---

## 测试

### 运行所有测试

```bash
cd mathlab
python -m unittest discover -s tests -v
```

### 运行特定测试

```bash
# 核心模块测试
python -m unittest tests.test_core -v

# 工具模块测试
python -m unittest tests.test_utils -v
```

---

## 许可证

本项目采用 **Apache License 2.0** 开源许可证。

```
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

   2. Grant of Copyright License.

   3. Grant of Patent License.

   4. Redistribution.

   5. Submission of Contributions.

   6. Trademarks.

   7. Disclaimer of Warranty.

   8. Limitation of Liability.

   9. Accepting Warranty or Additional Liability.
```

完整许可证文本请参阅 [LICENSE](LICENSE) 文件。

---

## 联系方式

| 渠道 | 信息 |
|------|------|
| **项目主页** | https://github.com/jencaoking/Axiom-Mathematics-Panel.git |
| **问题反馈** | https://github.com/jencaoking/Axiom-Mathematics-Panel.git/issues |
| **讨论社区** | https://github.com/jencaoking/Axiom-Mathematics-Panel.git/discussions |
| **邮箱** | jencaoking@outlook.com |

---

## 致谢

MathLab 受益于以下开源项目：

- **SymPy** - 符号数学库
- **NumPy** - 数值计算库
- **scikit-learn** - 机器学习库
- **PyTorch** - 深度学习框架
- **PySide6** - Qt for Python
- **Jedi** - Python自动补全

感谢所有贡献者的付出！

---

## 引用

如果您在学术项目中使用了 MathLab，请按以下格式引用：

```
@software{mathlab2024,
  title = {MathLab: Interactive Mathematics and AI Teaching Software},
  author = {MathLab Team},
  version = {1.0.0},
  year = {2024},
  url = {https://github.com/jencaoking/Axiom-Mathematics-Panel.git}
}
```

---

<div align="center">

**Star us on GitHub** · **Report a Bug** · **Request a Feature**

Built with ❤️ by the MathLab Team

</div>
