# MathLab Bug 报告汇总

## 问题概述

用户反馈启动 MathLab exe 后只闪现黑窗口，无任何报错和界面。经分析，这是由于多个导入问题和日志系统配置不当导致的启动崩溃。

---

## 一、已修复的 Bug

### Bug 1：导入 `get_agent` 失败

| 项目 | 详情 |
|------|------|
| **问题文件** | `mathlab/ui/ai_tools_panel.py` |
| **问题描述** | 导入 `from mathlab.core.agent_registry import get_agent`，但该模块中没有 `get_agent` 函数 |
| **错误类型** | `ImportError: cannot import name 'get_agent'` |
| **修复文件** | `mathlab/core/agent_registry.py` |
| **修复内容** | 新增 `AgentInfo` 类和 `get_agent()` 函数 |
| **修复时间** | 2026-06-23 |

---

### Bug 2：导入 `MathLabCodeEditor` 失败

| 项目 | 详情 |
|------|------|
| **问题文件** | `mathlab/ui/main_window.py` |
| **问题描述** | 类名被改为 `AutocompleteTextEdit`，但仍在导入旧名称 `MathLabCodeEditor` |
| **错误类型** | `ImportError: cannot import name 'MathLabCodeEditor'` |
| **修复文件** | `mathlab/ui/main_window.py` |
| **修复内容** | 改为导入 `AutocompleteTextEdit` |
| **修复时间** | 2026-06-23 |

---

### Bug 3：导入 `MathAgent` 失败

| 项目 | 详情 |
|------|------|
| **问题文件** | `mathlab/ui/ai_tools_panel.py` |
| **问题描述** | 导入 `MathAgent`，但实际定义的是 `BaseMathAgent`、`GeometryAgent`、`DataVizAgent` |
| **错误类型** | `ImportError: cannot import name 'MathAgent'` |
| **修复文件** | `mathlab/ui/ai_tools_panel.py` |
| **修复内容** | 改用 `GeometryAgent`，并正确注入 `ai_manager` |
| **修复时间** | 2026-06-23 |

---

### Bug 4：导入 `EChartsBridge` 失败

| 项目 | 详情 |
|------|------|
| **问题文件** | `mathlab/plugins/echarts_viewer/main.py` |
| **问题描述** | 导入 `EChartsBridge`，但 `bridge.py` 只有 `render_chart` 函数 |
| **错误类型** | `ImportError: cannot import name 'EChartsBridge'` |
| **修复文件** | `mathlab/plugins/echarts_viewer/bridge.py` |
| **修复内容** | 参考 `plugin_3d_viewer/bridge.py` 新增 `EChartsBridge` 类 |
| **修复时间** | 2026-06-23 |

---

### Bug 5：导入 `MonacoCodeEditor` 失败

| 项目 | 详情 |
|------|------|
| **问题文件** | `mathlab/ui/notebook_panel.py` |
| **问题描述** | 导入 `MonacoCodeEditor`，但该类不存在 |
| **错误类型** | `ImportError: cannot import name 'MonacoCodeEditor'` |
| **修复文件** | `mathlab/ui/code_editor.py` |
| **修复内容** | 新增 `MonacoCodeEditor` 类 |
| **修复时间** | 2026-06-23 |

---

### Bug 6：`jedi` 依赖缺失导致启动崩溃

| 项目 | 详情 |
|------|------|
| **问题文件** | `mathlab/core/python_repl.py` |
| **问题描述** | `import jedi` 是硬依赖，但 `requirements.txt` 中未列出，PyInstaller 打包时未包含 |
| **错误类型** | `ModuleNotFoundError: No module named 'jedi'` |
| **修复文件** | `mathlab/core/python_repl.py`, `requirements.txt`, `mathlab.spec` |
| **修复内容** | 改为软导入，添加到依赖列表和打包配置 |
| **修复时间** | 2026-06-24 |

---

### Bug 7：日志文件路径在打包后不可写

| 项目 | 详情 |
|------|------|
| **问题文件** | `mathlab/utils/logger.py` |
| **问题描述** | 打包后日志写到只读的 `_MEIPASS` 目录，无法写入 |
| **影响** | 崩溃时无日志记录 |
| **修复文件** | `mathlab/utils/logger.py` |
| **修复内容** | 打包模式下写到 exe 同级目录的 `logs/` 文件夹 |
| **修复时间** | 2026-06-24 |

---

### Bug 8：启动崩溃无任何错误反馈

| 项目 | 详情 |
|------|------|
| **问题文件** | `mathlab/main.py` |
| **问题描述** | `console=False` 导致错误被完全吞掉，用户看不到任何报错信息 |
| **影响** | 无法诊断启动失败原因 |
| **修复文件** | `mathlab/main.py` |
| **修复内容** | 添加 `_write_crash_log()` 函数和最外层 try/except |
| **修复时间** | 2026-06-24 |

---

## 二、已知但未完全修复的问题

### Issue 1：Jupyter 功能被静默禁用

| 项目 | 详情 |
|------|------|
| **问题文件** | `mathlab/ui/main_window.py`, `mathlab/core/jupyter_manager.py` |
| **问题描述** | `main_window.py` 导入 `JupyterManager`，但实际定义的是 `JupyterSandbox`，导致 Jupyter 功能被静默禁用 |
| **严重程度** | 中（不影响启动） |
| **状态** | 已确认，待修复 |

---

## 三、修复验证步骤

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 重新打包
pyinstaller mathlab.spec --clean

# 3. 测试运行
dist/MathLab/MathLab.exe
```

---

## 四、崩溃日志位置

修复后，若仍有问题，可查看以下日志文件：

| 日志文件 | 路径 | 用途 |
|---------|------|------|
| `crash.log` | exe 同级目录 | 启动崩溃报告 |
| `logs/mathlab.log` | exe 同级目录 | 运行时日志 |

---

## 五、文件修改清单

| 文件路径 | 修改类型 | 备注 |
|---------|---------|------|
| `mathlab/core/agent_registry.py` | 新增函数 | 添加 `get_agent()` 和 `AgentInfo` |
| `mathlab/ui/code_editor.py` | 新增类 | 添加 `MonacoCodeEditor` |
| `mathlab/ui/main_window.py` | 修复导入 | 改为导入 `AutocompleteTextEdit` |
| `mathlab/ui/ai_tools_panel.py` | 修复导入 | 改为导入 `GeometryAgent` |
| `mathlab/plugins/echarts_viewer/bridge.py` | 新增类 | 添加 `EChartsBridge` |
| `mathlab/core/python_repl.py` | 修复导入 | 将 `jedi` 改为软导入 |
| `requirements.txt` | 添加依赖 | 添加 `jedi` |
| `mathlab.spec` | 更新配置 | 添加 `jedi` 和 `mathlab.ui.code_editor` |
| `mathlab/utils/logger.py` | 修复路径 | 打包模式下日志写到正确位置 |
| `mathlab/main.py` | 添加异常处理 | 添加崩溃日志机制 |

---

**报告生成时间**：2026-06-24  
**报告版本**：v1.0  
**修复状态**：已完成 8 个关键 Bug 的修复