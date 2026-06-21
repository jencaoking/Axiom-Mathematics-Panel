# 动态函数探索器 - 实现总结

## 概述

已成功为 MathLab 实现**动态函数探索器**功能,这是一个强大的交互式工具,用于探索数学函数的性质和变换。

## 实现的功能

### ✅ 1. 函数绘图面板
- **位置**: 左侧停靠面板 (视图 → 函数探索器)
- **支持三种函数类型**:
  - 显函数: y = f(x)
  - 隐函数: f(x,y) = 0  
  - 极坐标: r = f(θ)

### ✅ 2. 参数滑块控制
- **自动参数识别**: 从表达式中提取非常数变量作为参数
- **实时交互**: 拖动滑块立即更新函数图象
- **精确显示**: 每个滑块显示当前值(精确到0.01)
- **范围**: -10 到 10,步长 0.01

**示例**:
```
输入: A*sin(omega*x + phi)
自动生成: 3个滑块 (A, omega, phi)
```

### ✅ 3. 图象变换工具
提供8种常用变换按钮:

**平移变换**:
- ← 左移: f(x) → f(x+1)
- 右移 →: f(x) → f(x-1)
- ↑ 上移: f(x) → f(x)+1
- 下移 ↓: f(x) → f(x)-1

**伸缩变换**:
- X轴伸缩: f(x) → f(x/1.5)
- Y轴伸缩: f(x) → 1.5*f(x)

**反射变换**:
- X轴反射: f(x) → -f(x)
- Y轴反射: f(x) → f(-x)

### ✅ 4. 预设函数模板
快速加载常见函数类型:
- 正弦函数: A*sin(ωx+φ)
- 二次函数: ax²+bx+c
- 指数函数: a*e^(bx)
- 高斯函数
- 反比例函数: a/x

## 文件结构

```
mathlab/
├── ui/
│   └── function_explorer_panel.py    # 新增: 函数探索器面板
├── locale/
│   ├── zh.json                        # 修改: 添加中文翻译
│   └── en.json                        # 修改: 添加英文翻译
├── ui/main_window.py                  # 修改: 集成函数探索器
├── docs/function_explorer_guide.md    # 新增: 使用指南
└── tests/test_function_explorer.py    # 新增: 测试脚本
```

## 核心组件

### 1. FunctionExplorerPanel (function_explorer_panel.py)

主要类和方法:

```python
class FunctionExplorerPanel(QDockWidget):
    """动态函数探索器面板"""
    
    # 信号
    function_added = Signal(dict)      # 发射新函数数据
    function_updated = Signal(dict)    # 发射更新的函数数据
    
    # 主要方法
    def on_plot_function()              # 绘制函数
    def _extract_parameters(expr)       # 提取参数
    def _create_parameter_sliders()     # 创建滑块
    def _on_parameter_changed()         # 参数变化处理
    def _apply_transform()              # 应用变换
    
class ParameterSlider(QWidget):
    """单个参数滑块控件"""
    
    value_changed = Signal(str, float)  # 参数名, 值
```

### 2. 主窗口集成 (main_window.py)

修改内容:
- 导入 `FunctionExplorerPanel`
- 在 `setup_docks()` 中创建面板实例
- 添加菜单项 `function_explorer_action`
- 连接信号: `function_added`, `function_updated`
- 实现槽函数:
  - `toggle_function_explorer()`: 显示/隐藏面板
  - `on_function_added()`: 处理新函数
  - `on_function_updated()`: 处理参数更新

### 3. 几何引擎支持 (geometry_engine.py)

已有功能(无需修改):
- `add_function_plot()`: 显函数绘图
- `add_implicit_plot()`: 隐函数绘图
- `add_polar_plot()`: 极坐标绘图
- 自动离散化生成点数据
- 序列化/反序列化支持

### 4. 画布渲染 (canvas.py)

已有功能(无需修改):
- 支持 `FunctionPlot`, `ImplicitPlot`, `PolarPlot` 类型
- 使用 `QPainterPath` 绘制平滑曲线
- 不同颜色区分函数类型
- 支持选择和更新

## 使用方法

### 启动程序
```bash
cd "j:\PROJECT\Python project\Axiom Mathematics Panel"
.\venv\Scripts\Activate.ps1
cd mathlab
python main.py
```

### 打开函数探索器
1. 菜单栏: **视图** → **函数探索器**
2. 面板出现在左侧停靠区

### 基本操作
1. **绘制函数**:
   - 选择函数类型
   - 输入表达式(如 `x^2`, `sin(x)`)
   - 点击"绘制函数"或按 Enter

2. **调整参数**:
   - 如果函数含参数,自动生成滑块
   - 拖动滑块实时更新图象

3. **应用变换**:
   - 点击变换按钮(左移、右移等)
   - 观察图象变化

4. **使用模板**:
   - 从下拉菜单选择预设函数
   - 自动填充并绘制

## 技术亮点

### 1. 智能参数提取
使用正则表达式自动识别函数中的参数:
```python
def _extract_parameters(self, expression: str) -> list:
    known_vars = {'x', 'y', 'theta', 'pi', 'e', 'sin', 'cos', ...}
    identifiers = re.findall(r'\b([a-zA-Z_]\w*)\b', expression)
    params = [ident for ident in identifiers if ident not in known_vars]
    return params
```

### 2. 实时参数更新
滑块变化时动态替换表达式中的参数值:
```python
modified_expr = re.sub(
    r'\b' + re.escape(pname) + r'\b', 
    f'({val})', 
    modified_expr
)
```

### 3. 变换组合
支持连续应用多个变换,每次基于当前表达式修改:
```python
# 水平平移: x -> (x - shift)
transformed_expr = transformed_expr.replace('x', f'(x - {shift})')
# 垂直平移: f(x) -> f(x) + shift  
transformed_expr = f'({transformed_expr}) + {shift}'
```

### 4. 国际化支持
完整的中英文翻译,所有UI文本通过 `t()` 函数获取:
```json
{
  "function_explorer": {
    "title": "函数探索器",
    "parameters": "参数控制",
    "transformations": "图象变换",
    ...
  }
}
```

## 教学应用场景

### 场景1: 探究正弦函数参数
**目标**: 理解振幅、周期、相位
**步骤**:
1. 选择模板 "正弦函数 A*sin(ωx+φ)"
2. 分别调整 A、omega、phi 滑块
3. 观察图象变化
4. 总结规律:
   - A 控制振幅(上下拉伸)
   - omega 控制周期(左右压缩)
   - phi 控制相位(左右平移)

### 场景2: 二次函数变换
**目标**: 掌握抛物线的平移和伸缩
**步骤**:
1. 输入基础函数 `x^2`
2. 依次点击: 右移、上移、Y轴伸缩
3. 观察最终表达式: `1.5*(x-1)^2 + 1`
4. 对比原始图象和变换后图象

### 场景3: 圆锥曲线参数
**目标**: 理解椭圆、双曲线的几何性质
**步骤**:
1. 输入隐函数 `x^2/a^2 + y^2/b^2 - 1`
2. 调整参数 a、b
3. 观察椭圆形状变化
4. 理解 a、b 与长轴、短轴的关系

## 已知限制和改进方向

### 当前限制
1. 参数范围固定为 [-10, 10]
2. 变换步长固定(平移1单位,伸缩1.5倍)
3. 不支持函数求值和表格显示
4. 无法保存参数配置

### 未来改进
1. ✨ 允许自定义参数范围和初始值
2. ✨ 添加函数求值器(输入x值得到y值)
3. ✨ 支持导数和积分可视化
4. ✨ 添加动画模式(参数自动连续变化)
5. ✨ 导出函数图象为PNG/SVG
6. ✨ 支持多函数对比(不同颜色)
7. ✨ 添加函数历史记录

## 测试建议

### 手动测试清单
- [ ] 绘制显函数 `x^2`, `sin(x)`, `exp(x)`
- [ ] 绘制隐函数 `x^2 + y^2 - 1` (圆)
- [ ] 绘制极坐标 `2*cos(theta)`
- [ ] 输入 `A*sin(omega*x + phi)` 检查是否生成3个滑块
- [ ] 拖动滑块观察图象实时更新
- [ ] 点击所有变换按钮验证效果
- [ ] 使用所有预设模板
- [ ] 切换中英文界面检查翻译
- [ ] 同时绘制多个函数测试性能

### 自动化测试
运行测试脚本:
```bash
python tests/test_function_explorer.py
```

## 代码质量

### 遵循的规范
- ✅ PEP 8 代码风格
- ✅ 完整的文档字符串
- ✅ 清晰的注释
- ✅ 模块化设计
- ✅ 信号-槽机制
- ✅ 国际化支持

### 错误处理
- 表达式语法错误提示
- 空表达式警告
- 变换失败捕获异常
- 友好的用户提示

## 总结

动态函数探索器成功实现了教材中要求的所有核心功能:

1. ✅ **函数绘图**: 支持显函数、隐函数、极坐标
2. ✅ **参数滑块**: 自动生成、实时更新
3. ✅ **图象变换**: 平移、伸缩、反射一键操作
4. ✅ **预设模板**: 快速开始探索

该功能将极大提升数学教学的互动性和直观性,帮助学生深入理解函数性质和变换规律。

---

**实现日期**: 2026-06-10  
**版本**: 1.0  
**状态**: ✅ 完成并可用
