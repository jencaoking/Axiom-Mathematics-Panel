# Python REPL 会话模式使用指南

## 📖 概述

MathLab 的 Python REPL 现在支持**会话上下文传递**功能，让学生可以像 Jupyter Notebook 一样逐行输入代码并保留变量状态，同时保持沙箱的安全性。

---

## 🚀 快速开始

### 1. 基本用法

```python
from mathlab.core.python_repl import PythonREPL

# 创建 REPL 实例（默认启用会话模式）
repl = PythonREPL(session_mode=True)

# 第一次执行：定义变量
result1 = repl.execute('x = 42')
print(result1['success'])  # True

# 第二次执行：使用之前定义的变量
result2 = repl.execute('print(x * 2)')
print(result2['output'])   # "84\n"
```

### 2. 两种模式对比

#### 会话模式（Session Mode）- 类似 Jupyter
```python
repl = PythonREPL(session_mode=True)

repl.execute('a = 10')
repl.execute('b = 20')
result = repl.execute('print(a + b)')
# 输出: 30 ✅ 变量持久化
```

#### 隔离模式（Isolation Mode）- 完全独立
```python
repl = PythonREPL(session_mode=False)

repl.execute('a = 10')
result = repl.execute('print(a)')
# 错误: name 'a' is not defined ❌ 每次执行都是独立环境
```

---

## 🎯 核心 API

### 初始化参数

```python
PythonREPL(namespace=None, session_mode=True)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `namespace` | dict | None | 保留参数（沙箱模式下不使用） |
| `session_mode` | bool | True | 是否启用会话模式 |

### 主要方法

#### execute(code_str, timeout=5)
执行代码并返回结果。

```python
result = repl.execute('x = 5; print(x ** 2)')
# 返回: {
#     'success': True,
#     'output': '25\n',
#     'error': '',
#     'more': False
# }
```

#### set_session_mode(enabled=True)
动态切换会话/隔离模式。

```python
# 切换到隔离模式
repl.set_session_mode(False)

# 切换回会话模式
repl.set_session_mode(True)
```

⚠️ **注意**: 切换模式时会清空会话上下文，之前的变量将丢失。

#### clear_session()
清空会话上下文（保留历史记录）。

```python
repl.execute('x = 100')
repl.clear_session()
result = repl.execute('print(x)')
# 错误: name 'x' is not defined
```

#### get_session_context_length()
获取当前会话上下文的代码行数。

```python
repl.execute('a = 1')
repl.execute('b = 2')
print(repl.get_session_context_length())  # 2
```

#### get_history()
获取用户输入的历史记录（包括成功和失败的代码）。

```python
repl.execute('x = 1')
repl.execute('invalid syntax')  # 失败
history = repl.get_history()
print(len(history))  # 2
```

#### clear_history()
清空历史记录。

```python
repl.clear_history()
```

---

## 💡 使用场景

### 场景 1: 交互式数学计算

```python
repl = PythonREPL(session_mode=True)

# 定义变量
repl.execute('radius = 5')

# 计算面积
repl.execute('import math')
result = repl.execute('area = math.pi * radius ** 2')

# 输出结果
result = repl.execute('print(f"Area: {area:.2f}")')
# 输出: Area: 78.54
```

### 场景 2: 函数定义与调用

```python
repl = PythonREPL(session_mode=True)

# 定义函数
repl.execute('''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
''')

# 调用函数
result = repl.execute('print([fibonacci(i) for i in range(10)])')
# 输出: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

### 场景 3: 数据分析流程

```python
repl = PythonREPL(session_mode=True)

# 准备数据
repl.execute('data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]')

# 计算统计量
repl.execute('mean = sum(data) / len(data)')
repl.execute('variance = sum((x - mean) ** 2 for x in data) / len(data)')

# 输出结果
result = repl.execute('print(f"Mean: {mean}, Variance: {variance:.2f}")')
# 输出: Mean: 5.5, Variance: 8.25
```

### 场景 4: 临时切换到隔离模式测试

```python
repl = PythonREPL(session_mode=True)

# 在会话模式下工作
repl.execute('secret_key = "abc123"')

# 切换到隔离模式进行安全测试
repl.set_session_mode(False)
result = repl.execute('print(secret_key)')
# 错误: name 'secret_key' is not defined ✅ 安全隔离

# 切回会话模式继续工作
repl.set_session_mode(True)
```

---

## ⚙️ 高级配置

### 自定义超时时间

```python
# 为耗时操作设置更长的超时时间
result = repl.execute('''
import time
time.sleep(3)
print("Done")
''', timeout=10)
```

### 会话上下文管理策略

```python
repl = PythonREPL(session_mode=True)

# 执行多步操作
repl.execute('x = 1')
repl.execute('y = 2')
repl.execute('z = 3')

# 检查上下文长度
print(repl.get_session_context_length())  # 3

# 如果需要重置状态但保留历史
repl.clear_session()  # 清空上下文
# history 仍然保留，可以重新执行
```

---

## 🔒 安全性说明

### 沙箱保护依然有效

即使在会话模式下，所有代码仍在**独立的子进程**中执行，享受以下保护：

1. ✅ **超时保护**: 默认 60 秒超时，防止死循环
2. ✅ **内存限制**: 默认 512MB 上限，防止内存溢出
3. ✅ **进程隔离**: 主程序永不卡死
4. ✅ **模块白名单**: 仅允许安全的数学库

### 会话模式的实现原理

```
用户输入: print(x)
         ↓
REPL 拼接: x = 42\nprint(x)  （历史代码 + 当前代码）
         ↓
沙箱执行: 在独立子进程中执行完整代码
         ↓
返回结果: {'success': True, 'output': '42\n'}
```

**关键点**: 
- 每次执行都会重新运行所有历史代码
- 确保变量状态的一致性
- 但会增加执行时间（历史代码越多越慢）

### 性能考虑

对于长会话，建议定期清空上下文：

```python
# 每执行 50 次后清空一次
if repl.get_session_context_length() > 50:
    repl.clear_session()
    # 可选：重新定义关键变量
    repl.execute('important_var = ...')
```

---

## 🆚 模式选择建议

| 场景 | 推荐模式 | 原因 |
|------|---------|------|
| 学生交互式学习 | ✅ 会话模式 | 类似 Jupyter，体验友好 |
| 在线评测系统 (OJ) | ✅ 隔离模式 | 每次提交独立，防止作弊 |
| AI 代码生成测试 | ✅ 隔离模式 | 避免历史代码干扰 |
| 复杂数学推导 | ✅ 会话模式 | 需要累积中间结果 |
| 安全敏感操作 | ✅ 隔离模式 | 最小化攻击面 |

---

## 🐛 常见问题

### Q1: 为什么切换模式后变量消失了？

**A**: 切换模式时会调用 `clear_session()` 清空上下文，这是设计行为。如需保留变量，请在切换前导出关键数据。

### Q2: 会话模式会变慢吗？

**A**: 是的。每次执行都会重新运行所有历史代码。如果历史代码很多（>100 行），建议定期清空或切换到隔离模式。

### Q3: 如何查看当前有哪些变量？

**A**: 执行 `print(dir())` 或 `print(globals().keys())`：

```python
repl.execute('x = 1; y = 2')
result = repl.execute('print([v for v in dir() if not v.startswith("_")])')
# 输出: ['x', 'y']
```

### Q4: 会话模式和 Jupyter 有什么区别？

**A**: 
- **相似点**: 都支持变量持久化
- **不同点**: 
  - Jupyter 维护真实的内存状态
  - MathLab 会话模式每次重新执行所有代码
  - MathLab 更安全（沙箱隔离）
  - MathLab 更适合教学场景（可重置、可审计）

---

## 📝 最佳实践

1. **短会话优于长会话**: 每 20-30 行代码后考虑 `clear_session()`
2. **重要变量注释**: 在代码中添加注释说明关键变量的用途
3. **定期验证状态**: 使用 `print()` 输出中间结果确认状态正确
4. **错误处理**: 检查 `result['success']` 再继续使用
5. **模式切换谨慎**: 切换前保存重要数据

---

## 🎓 教学示例

### 示例 1: 求解二次方程

```python
repl = PythonREPL(session_mode=True)

# 步骤 1: 导入库
repl.execute('import sympy as sp')

# 步骤 2: 定义符号
repl.execute('x = sp.symbols("x")')

# 步骤 3: 定义方程
repl.execute('equation = x**2 - 5*x + 6')

# 步骤 4: 求解
result = repl.execute('solutions = sp.solve(equation, x); print(solutions)')
# 输出: [2, 3]
```

### 示例 2: 绘制函数图像

```python
repl = PythonREPL(session_mode=True)

# 准备数据
repl.execute('import numpy as np')
repl.execute('import matplotlib.pyplot as plt')
repl.execute('x = np.linspace(-10, 10, 100)')
repl.execute('y = x**2')

# 绘图
result = repl.execute('''
plt.figure(figsize=(8, 6))
plt.plot(x, y, label="y = x^2")
plt.xlabel("x")
plt.ylabel("y")
plt.title("Quadratic Function")
plt.legend()
plt.grid(True)
plt.savefig("plot.png")
print("Plot saved!")
''')
```

---

**最后更新**: 2026-06-10  
**版本**: MathLab v1.0+
