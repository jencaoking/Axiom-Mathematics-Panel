# MathLab (代号: Axiom)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)]()
[![Version](https://img.shields.io/badge/Version-3.0.3-red.svg)]()

> **MathLab 3.0 (代号: Axiom)** 是一款交互式数学、AI 与 3D 教学桌面软件，集动态几何画板（2D 与 3D）、Python 编程学习环境、符号/数值计算、算法可视化、AI 具身学习、交互笔记本与插件扩展于一体。本版本在经历了长期的底层架构重构后，正式迎来了 **v3.0.3 Agentic UI（智能代理交互）** 的全面升级！

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
| **JupyterLab 深度集成** | 嵌有原生 JupyterLab 单元，支持跨进程双向 UDP 数据绑定与变量同步 |
| **算法可视化** | 排序、搜索、图论、凸包、K-Means 等算法的逐步动画演示 |
| **动画引擎** | Manim 风格的数学动画时间轴与缓动，支持关键帧与过渡曲线 |
| **Agentic UI 与自然语言作图** | AI 通过工具调用直接在原生画布上绘制图形 |
| **智能出题与视觉错题本** | 互动测验卡片，AI 自动绘制解析图 |
| **Monaco 意图穿透** | 通过 JS 注入打通 Monaco Editor，AI 可解读高亮代码 |
| **AI 辅助探索** | 线性/多项式回归、K-Means/DBSCAN 聚类、ONNX 推理 |
| **全局命令面板** | VS Code 风格的全局命令控制台，支持模糊搜索、快捷执行 |
| **智能作图** | 10像素物理防抖的几何控制点磁吸、临时距离辅助线 |
| **工业级容错与恢复** | 全局异常守护引擎，30秒极速快照 AutoSaver |
| **插件系统** | 统一 `Plugin` 基类 + 插件管理器，支持生命周期、热加载与扩展 API |

### 🔒 安全特性

- **进程隔离**: 用户代码在独立子进程中执行
- **超时控制**: 防止无限循环和死锁
- **资源限制**: 内存与执行时间双重保护
- **命名空间隔离**: 用户代码与系统环境分离
- **WebEngine 沙箱**: 浏览器侧渲染进程可显式释放

### 🛠️ 技术栈

```
GUI框架:        PySide6 (Qt for Python) + Qt WebEngine
跨进程通信:     UDP Socket 极速双向数据绑定 (Tx: 45678, Rx: 45679)
符号计算:       SymPy (预留 Maxima / Giac 多引擎总线)
数值计算:       NumPy / SciPy / OctaveBridge
机器学习:       scikit-learn / PyTorch (可选) / ONNX Runtime (可选)
可视化:         matplotlib / pyqtgraph / Three.js (3D) / ECharts (2D)
动画:           自研 Animation Engine (Manim 风格关键帧)
笔记本:         自研 Notebook & JupyterLab 混合沙箱
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
git clone https://github.com/jencaoking/Axiom-Mathematics-Panel.git
cd Axiom-Mathematics-Panel
python -m venv venv
source venv/bin/activate
pip install -r mathlab/requirements.txt
pip install scikit-learn matplotlib pyqtgraph onnxruntime
cd mathlab
python main.py
```

#### 方式二：使用 pip 安装

```bash
pip install mathlab
pip install "mathlab[ai]"
pip install "mathlab[neural]"
pip install "mathlab[visualization]"
pip install "mathlab[full]"
mathlab
```

---

## 功能演示

### 几何作图（控制台 REPL）

```python
>>> draw_point(0, 0)
>>> draw_point(3, 4)
>>> draw_segment(p1, p2)
>>> draw_circle(p1, 5)
```

### 符号计算

```python
>>> solve('x**2 - 4 = 0', 'x')
>>> simplify('x**2 + 2*x**2')
>>> integrate('x**2', 'x')
>>> differentiate('sin(x)', 'x')
```

### Agentic UI 与自然语言作图 (NL2Draw)

在 AI 助手中输入：**"帮我画一个直角三角形，然后再画一个以直角顶点为圆心，半径为 2 的圆。"**

### JupyterLab 双向交互

```python
from mathlab_api import mlab
mlab.draw_point('A', 2.0, 3.0)
mlab.draw_point('B', 6.0, 3.0)
mlab.draw_line('L1', 'A', 'B')
```

---

## 目录结构

```
Axiom-Mathematics-Panel/
├── mathlab/
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── canvas.py
│   │   ├── geogebra_canvas.py
│   │   ├── code_editor.py
│   │   ├── jupyter_panel.py
│   │   └── ai_tools_panel.py
│   ├── core/
│   │   ├── geometry_engine.py
│   │   ├── geogebra_engine.py
│   │   ├── cas_provider.py
│   │   ├── ai_manager.py
│   │   └── jupyter_manager.py
│   ├── plugins/
│   │   ├── plugin_3d_viewer/
│   │   ├── echarts_viewer/
│   │   └── matrix_tools/
│   ├── tests/
│   ├── docs/
│   ├── locale/
│   └── resources/
├── LICENSE
└── README.md
```

---

## 技术架构

### 五层架构体系

```
┌──────────────────────────────────────────────────────────────────────┐
│                        用户界面层 (UI Layer)                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │
│  │2D 画板 │ │3D 画板 │ │笔记本  │ │命令面板│ │AI 面板 │ │Jupyter │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│                       业务逻辑层 (Core Layer)                         │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Geometry Engine │ CAS Bus   │ Animation  │  NumEngine         │  │
│  │ (DAG + Constraints)│ (SymPy +) │ (Manim 风格)│ (BLAS/Octave) │  │
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
│  └────────┘ └────────┘ └────────┘ └────────┘                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 核心模块

### GeometryEngine / GeoGebraEngine

基于有向无环图的依赖管理，支持几何对象的创建、更新和约束求解。

### CASProvider

封装 SymPy 提供表达式化简、方程求解、微积分运算等功能。

### NumEngine / OctaveBridge

高性能数值计算引擎，支持矩阵运算、特征值分解、奇异值分解等。

### Notebook

SageMath 风格多 Cell 笔记本，支持 Markdown 和代码单元格的混合编排。

### AIManager

流式大模型核心，支持 Function Calling、实时 Token 消耗统计、滑动窗口记忆管理。

---

## 插件系统

### 内置插件

| 插件 | 功能 |
|------|------|
| `plugin_3d_viewer` | 基于 Three.js 的 3D 几何查看器 |
| `echarts_viewer` | 基于 ECharts 的 2D 交互图表 |
| `matrix_tools` | 矩阵运算辅助工具集 |

### 开发自定义插件

```python
from mathlab.core.plugin_base import Plugin

class MyPlugin(Plugin):
    name = "my_plugin"
    version = "0.1.0"

    def activate(self, ctx):
        ctx.register_command("hello", self.say_hello)

    def deactivate(self, ctx):
        pass

    def say_hello(self, ctx):
        ctx.notify("Hello from MyPlugin!")
```

---

## 开发指南

### 开发环境搭建

```bash
git clone https://github.com/jencaoking/Axiom-Mathematics-Panel.git
cd Axiom-Mathematics-Panel
python -m venv venv
source venv/bin/activate
pip install -r mathlab/requirements.txt
pip install pre-commit
pre-commit install
```

### 代码规范

- **PEP 8**: Python 代码风格指南
- **类型提示**: 公共 API 添加类型标注
- **docstring**: 使用 Google 风格文档字符串

### 构建打包

```bash
pyinstaller mathlab/build_spec.spec
python -m nuitka --standalone --enable-plugin=pyside6 mathlab/main.py
```

---

## 测试

### 运行测试

```bash
cd mathlab
python -m pytest tests/ -v
```

### 测试覆盖

- 核心模块（几何、CAS、算法动画、AI、笔记本）
- 工具模块（主题、i18n、LaTeX、日志）
- 沙箱安全与会话隔离
- Octave 桥接与数值计算

---

## 路线图

- **2.0**: 异步计算中枢、3D 渲染引擎、AI 集成
- **2.5**: GeoGebra 级约束求解、笔记本、动画引擎、插件系统
- **2.6**: JupyterLab 嵌入、跨进程双向 UDP IPC 通信
- **2.7**: 全局容错恢复架构、惯性平移物理模型、智能辅助线
- **3.0**: Agentic UI、NL2Draw 自然语言作图、视觉错题本
- **4.0**: Web 同步、多人协作、插件市场、云端教学资源

---

## 许可证

本项目采用 **Apache License 2.0** 开源许可证。

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
- **PySide6** - Qt for Python
- **Three.js** - 3D 渲染
- **Monaco Editor** - 代码编辑

---

## 引用

```
@software{mathlab_jupyter,
  title  = {MathLab (Axiom): Interactive Mathematics, AI and 3D Teaching Software},
  author = {MathLab Team},
  version = {3.0.3},
  year   = {2026},
  url    = {https://github.com/jencaoking/Axiom-Mathematics-Panel}
}
```

---

<div align="center">

**Star us on GitHub** · **Report a Bug** · **Request a Feature**

Built with ❤️ by the MathLab Team

</div>
