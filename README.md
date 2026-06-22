# MathLab (Axiom)

<div align="center">
  <img src="https://via.placeholder.com/800x200.png?text=MathLab+3.5+-+The+Agentic+Mathematics+Platform" alt="MathLab Banner">
</div>

<div align="center">

**[English](README_EN.md) | 简体中文**

</div>

MathLab 是一款面向未来的**多智能体交互式数学教育与科研桌面软件**。它突破了传统“套壳聊天框”的局限，打造了一套真正的工业级、L5 自动化自治的多智能体（Multi-Agent）桌面环境。

从基础的几何作图、代数求解，到复杂的定理证明和交互式教学大纲驱动，MathLab 完美融合了本地高性能图形引擎与云端大语言模型，并配以极具未来感的 Agentic UI。

---

## 🚀 MathLab 3.5 核心亮点：L5 Agentic 架构

在 MathLab 3.5 的巅峰重构中，我们完成了四大核心维度的跃迁，打造了“自动驾驶级别”的 AI 教学基建：

### 🛡️ Phase 1: 视觉安全掌控 (Trust & Safety)
建立极客级别的状态栏与“影子状态（Shadow State）”。让 AI 的每一步计算与画笔调用都在监控之下，消除了未知状态带来的恐惧，实现安全的“草稿模式”。

### 🤖 Phase 2: 多智能体分工与容错自省 (Swarm Routing & Reflection)
摒弃了臃肿的“全能大模型”，引入了多专家协作的 **Swarm 架构**：
- 自动识别意图的 `Transfer Protocol` (交接流转协议)。
- 搭载失败快速重试（`Fail Fast`）与自我反思机制（`Self-Reflection`），当调用画板出错时，AI 能自主纠错并重新绘制。

### 🧩 Phase 3: 按需装载上下文 (JIT Context Assembly)
内置高精度动态上下文组装器（Context Assembler）。告别 Token 费用爆炸与注意力稀释（Lost in the Middle），仅在需要时精准注入 LaTeX 规则、画布 JSON 或特定几何规则。

### 🎓 Phase 4: 思执分离教学双轨制 (Plan + Teach)
独创的教研、授课双层流转：
- **Plan（教学规划）**：教研组长专门拆解画布与题目，生成强类型的大纲清单（Syllabus JSON）。
- **Teach（课堂讲解）**：授课讲师依据大纲，结合激光笔工具，进行无剧透的沉浸式苏格拉底互动教学。

---

## ⚙️ 核心模块与技术栈

### 五层架构体系

```text
┌────────────────────────────────────────────────────────────────────────┐
│                       用户界面层 (UI Layer)                            │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐      │
│ │2D 画板 │ │3D 画板 │ │笔记本  │ │命令面板│ │Agent UI│ │Jupyter │      │
│ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘      │
├────────────────────────────────────────────────────────────────────────┤
│                      业务逻辑层 (Core Layer)                           │
│ ┌────────────────────────────────────────────────────────────────┐     │
│ │ 几何引擎 (DAG)   CAS 数学总线   动画引擎   多智能体路由管理        │     │
│ └────────────────────────────────────────────────────────────────┘     │
├────────────────────────────────────────────────────────────────────────┤
│                      扩展与数据引擎 (Data & VM Layer)                  │
│ ┌────────────────────────────────────────────────────────────────┐     │
│ │ Plugin VM        NumEngine      WebEngine Sandbox              │     │
│ └────────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
```

- **GeometryEngine**：基于有向无环图（DAG）的依赖管理，支持几何对象的创建、更新和约束求解。
- **CASProvider**：封装 SymPy 提供表达式化简、方程求解、微积分运算等功能。
- **Agent Registry & Tools**：内建丰富的天团专家（教研组长、几何专家、出题考官）和数十种原子操作 Tool 调用。
- **Notebook**：SageMath 风格的 Cell 笔记本，支持 Markdown 和代码单元格的混合编排。

---

## 🛠 开发指南

### 开发环境搭建

```bash
git clone https://github.com/jencaoking/Axiom-Mathematics-Panel.git
cd Axiom-Mathematics-Panel
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r mathlab/requirements.txt
pip install pre-commit
pre-commit install
```

### 构建打包

```bash
pyinstaller mathlab/build_spec.spec
python -m nuitka --standalone --enable-plugin=pyside6 mathlab/main.py
```

### 运行测试

```bash
cd mathlab
python -m pytest tests/ -v
```

---

## 路线图 (Roadmap)

- **2.0**: 异步计算中枢、3D 渲染引擎、AI 集成
- **2.5**: GeoGebra 级约束求解、笔记本、动画引擎、插件系统
- **3.0**: Agentic UI、NL2Draw 自然语言作图、视觉错题本
- **3.5**: 🌟 **多智能体架构 (Swarm)、思执分离大纲双轨制、纠错重试环**
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

## 致谢与引用

MathLab 受益于以下卓越的开源项目与框架：

- **PySide6** - Qt for Python
- **SymPy / NumPy / SciPy** - 数学计算基石
- **Three.js** - 3D 渲染
- **Monaco Editor** - 代码编辑引擎

```bibtex
@software{mathlab_jupyter,
  title  = {MathLab (Axiom): Interactive Mathematics, AI and 3D Teaching Software},
  author = {MathLab Team},
  version = {3.5.0},
  year   = {2026},
  url    = {https://github.com/jencaoking/Axiom-Mathematics-Panel}
}
```

<div align="center">

**Star us on GitHub** · **Report a Bug** · **Request a Feature**

Built with ❤️ by the MathLab Team

</div>
