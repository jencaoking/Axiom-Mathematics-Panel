# 解析几何深化功能使用指南

## 概述

本次更新为 MathLab 添加了强大的解析几何功能，包括：
- **圆锥曲线**：椭圆、双曲线、抛物线的原生支持
- **一般方程渲染**：支持通过一般方程 Ax²+Bxy+Cy²+Dx+Ey+F=0 直接绘制曲线
- **函数绘图**：显函数、隐函数、极坐标方程的可视化
- **动点轨迹**：追踪几何依赖点的运动轨迹

---

## 1. 圆锥曲线

### 1.1 椭圆 (Ellipse)

```python
# 创建中心点
center_id = draw_point(0, 0)

# 创建椭圆：半长轴 a=3, 半短轴 b=2
ellipse_id = draw_ellipse(center_id, a=3.0, b=2.0)
```

**参数说明：**
- `center_id`: 椭圆中心点的 ID
- `a`: 半长轴长度（默认 2.0）
- `b`: 半短轴长度（默认 1.0）
- `rotation`: 旋转角度（弧度，默认 0）

**标准方程：**
$$\frac{(x-h)^2}{a^2} + \frac{(y-k)^2}{b^2} = 1$$

### 1.2 双曲线 (Hyperbola)

```python
# 创建中心点
center_id = draw_point(5, 0)

# 创建双曲线：实半轴 a=2, 虚半轴 b=1.5
hyperbola_id = draw_hyperbola(center_id, a=2.0, b=1.5)
```

**参数说明：**
- `center_id`: 双曲线中心点的 ID
- `a`: 实半轴长度（默认 1.0）
- `b`: 虚半轴长度（默认 1.0）
- `rotation`: 旋转角度（弧度，默认 0）

**标准方程：**
$$\frac{(x-h)^2}{a^2} - \frac{(y-k)^2}{b^2} = 1$$

### 1.3 抛物线 (Parabola)

```python
# 创建顶点
vertex_id = draw_point(0, -2)

# 创建抛物线：焦距 p=1, 开口向上
parabola_id = draw_parabola(vertex_id, p=1.0, direction='up')
```

**参数说明：**
- `vertex_id`: 抛物线顶点的 ID
- `p`: 焦距参数（默认 1.0）
- `direction`: 开口方向 ('up', 'down', 'left', 'right'，默认 'up')

**标准方程（开口向上）：**
$$(x-h)^2 = 4p(y-k)$$

### 1.4 一般圆锥曲线 (ConicSection)

```python
# 绘制圆：x² + y² - 4 = 0
conic_id = draw_conic(A=1, B=0, C=1, D=0, E=0, F=-4)

# 绘制椭圆：x² + 2y² - 6 = 0
conic_id = draw_conic(A=1, B=0, C=2, D=0, E=0, F=-6)

# 绘制双曲线：x² - y² - 1 = 0
conic_id = draw_conic(A=1, B=0, C=-1, D=0, E=0, F=-1)
```

**参数说明：**
- `A, B, C, D, E, F`: 一般方程系数
- `x_range`: x 轴范围（默认 (-10, 10)）
- `y_range`: y 轴范围（默认 (-10, 10)）

**一般方程：**
$$Ax^2 + Bxy + Cy^2 + Dx + Ey + F = 0$$

---

## 2. 函数绘图

### 2.1 显函数 y = f(x)

```python
# 绘制抛物线 y = x²
func_id = plot_function('x**2', x_range=(-5, 5))

# 绘制正弦函数 y = sin(x)
func_id = plot_function('sin(x)', x_range=(-6.28, 6.28))

# 绘制指数函数 y = e^x
func_id = plot_function('exp(x)', x_range=(-3, 3))
```

**参数说明：**
- `expression`: 函数表达式字符串（使用 SymPy 语法）
- `x_range`: x 轴范围（默认 (-10, 10)）
- `num_points`: 采样点数（默认 500）

**支持的函数：**
- 基本运算：`+`, `-`, `*`, `/`, `**`
- 三角函数：`sin`, `cos`, `tan`
- 指数对数：`exp`, `log`
- 其他：`sqrt`, `Abs`

### 2.2 隐函数 f(x,y) = 0

```python
# 绘制单位圆：x² + y² - 1 = 0
impl_id = plot_implicit('x**2 + y**2 - 1', x_range=(-2, 2), y_range=(-2, 2))

# 绘制双曲线：x² - y² - 1 = 0
impl_id = plot_implicit('x**2 - y**2 - 1', x_range=(-3, 3), y_range=(-3, 3))

# 绘制心形线：(x²+y²-1)³ - x²y³ = 0
impl_id = plot_implicit('(x**2 + y**2 - 1)**3 - x**2*y**3', 
                        x_range=(-2, 2), y_range=(-2, 2))
```

**参数说明：**
- `expression`: 隐函数表达式字符串（f(x,y) = 0 的左边部分）
- `x_range`: x 轴范围（默认 (-10, 10)）
- `y_range`: y 轴范围（默认 (-10, 10)）
- `resolution`: 网格分辨率（默认 400）

### 2.3 极坐标 r = f(θ)

```python
import math

# 绘制圆：r = 2*cos(θ)
polar_id = plot_polar('2*cos(theta)', theta_range=(0, 2*math.pi))

# 绘制玫瑰线：r = cos(3θ)
polar_id = plot_polar('cos(3*theta)', theta_range=(0, 2*math.pi))

# 绘制阿基米德螺线：r = θ
polar_id = plot_polar('theta', theta_range=(0, 4*math.pi))

# 绘制心形线：r = 1 - cos(θ)
polar_id = plot_polar('1 - cos(theta)', theta_range=(0, 2*math.pi))
```

**参数说明：**
- `expression`: 极坐标方程表达式字符串
- `theta_range`: θ 的范围（默认 (0, 2π)）
- `num_points`: 采样点数（默认 500）

**注意：** 使用变量名 `theta` 表示角度 θ

---

## 3. 动点轨迹 (Locus)

动点轨迹功能可以追踪一个点随另一个点移动时的运动路径。

### 3.1 基本用法

```python
# 创建驱动点（主动运动的点）
driver_id = draw_point(0, 0)

# 创建追踪点（被追踪的点）
tracer_id = draw_point(2, 0)

# 创建轨迹追踪器
locus_id = create_locus(tracer_id, driver_id)

# 模拟驱动点移动并更新轨迹
for i in range(100):
    angle = i * 0.1
    x = 3 * cos(angle)
    y = 3 * sin(angle)
    
    # 更新驱动点位置
    update_point(driver_id, x=x, y=y)
    
    # 更新追踪点位置（根据几何关系）
    update_point(tracer_id, x=x+1, y=y)
    
    # 记录轨迹点
    update_locus(locus_id)
```

**参数说明：**
- `tracer_id`: 被追踪点的 ID
- `driver_id`: 驱动点的 ID
- `max_points`: 最大轨迹点数（默认 1000）

### 3.2 实际应用场景

**场景1：圆周上的点的轨迹**
```python
# 驱动点在圆周上运动，追踪点固定在驱动点上
driver_id = draw_point(0, 0)
tracer_id = draw_point(1, 0)
locus_id = create_locus(tracer_id, driver_id)

# 让驱动点绕原点做圆周运动
for i in range(100):
    angle = i * 0.1
    x = 2 * cos(angle)
    y = 2 * sin(angle)
    update_point(driver_id, x=x, y=y)
    update_point(tracer_id, x=x+1, y=y)  # 追踪点相对驱动点偏移
    update_locus(locus_id)
```

**场景2：中点轨迹**
```python
# A、B 两点运动，追踪它们的中点 M
A_id = draw_point(-2, 0)
B_id = draw_point(2, 0)
M_id = draw_point(0, 0)  # 中点

locus_id = create_locus(M_id, A_id)

for i in range(50):
    t = i * 0.1
    # A 点在左半圆运动
    update_point(A_id, x=-2*cos(t), y=2*sin(t))
    # B 点在右半圆运动
    update_point(B_id, x=2*cos(t), y=2*sin(t))
    # 更新中点
    mid_x = (A.coordinates['x'] + B.coordinates['x']) / 2
    mid_y = (A.coordinates['y'] + B.coordinates['y']) / 2
    update_point(M_id, x=mid_x, y=mid_y)
    update_locus(locus_id)
```

---

## 4. 综合示例

### 4.1 椭圆的焦点性质演示

```python
# 创建椭圆
center_id = draw_point(0, 0)
ellipse_id = draw_ellipse(center_id, a=3.0, b=2.0)

# 计算焦点位置 c = sqrt(a² - b²)
c = sqrt(3**2 - 2**2)  # ≈ 2.236

# 标记两个焦点
F1_id = draw_point(-c, 0)
F2_id = draw_point(c, 0)

# 在椭圆上取一点 P
P_id = draw_point(3*cos(pi/4), 2*sin(pi/4))

# 连接 PF1 和 PF2
segment1_id = draw_segment(P_id, F1_id)
segment2_id = draw_segment(P_id, F2_id)

# 验证：PF1 + PF2 = 2a = 6
```

### 4.2 函数与圆锥曲线的交点

```python
# 绘制抛物线 y = x²
func_id = plot_function('x**2', x_range=(-3, 3))

# 绘制直线 y = x + 1
line_func_id = plot_function('x + 1', x_range=(-3, 3))

# 求解交点：x² = x + 1 => x² - x - 1 = 0
solutions = solve('x**2 - x - 1', 'x')
print(f"交点 x 坐标: {solutions}")
```

### 4.3 摆线（旋轮线）轨迹

```python
# 模拟圆的滚动，追踪圆上一点的轨迹
center_id = draw_point(0, 1)  # 圆心
tracer_id = draw_point(0, 0)  # 圆上的点
locus_id = create_locus(tracer_id, center_id)

radius = 1
for i in range(100):
    t = i * 0.1
    # 圆心沿 x 轴移动
    cx = radius * t
    cy = radius
    update_point(center_id, x=cx, y=cy)
    
    # 圆上点的参数方程（摆线）
    px = radius * (t - sin(t))
    py = radius * (1 - cos(t))
    update_point(tracer_id, x=px, y=py)
    
    update_locus(locus_id)
```

---

## 5. 注意事项

### 5.1 性能优化

- **采样点数**：对于复杂函数，适当减少 `num_points` 可以提高性能
- **隐函数分辨率**：`resolution` 参数影响精度和速度，建议根据需求调整
- **轨迹点数**：设置合理的 `max_points` 避免内存占用过大

### 5.2 表达式语法

所有函数表达式使用 **SymPy** 语法：
- 乘法必须显式写出：`2*x` 而非 `2x`
- 幂运算使用 `**`：`x**2` 而非 `x^2`
- 函数调用使用括号：`sin(x)` 而非 `sin x`

### 5.3 坐标系

- 画布使用标准笛卡尔坐标系
- x 轴向右为正，y 轴向上为正
- 角度单位为**弧度**

### 5.4 颜色方案

不同类型的曲线使用不同颜色以便区分：
- 椭圆：橙色 (#ff6b00)
- 双曲线：红色 (#d90429)
- 抛物线：紫色 (#7209b7)
- 一般圆锥曲线：粉色 (#f72585)
- 显函数：青色 (#4cc9f0)
- 隐函数：蓝色 (#4361ee)
- 极坐标：深蓝 (#3a0ca3)
- 轨迹：粉色 (#f72585)

---

## 6. API 参考

### GeometryEngine 新增方法

```python
# 圆锥曲线
add_ellipse(center_id, a=2.0, b=1.0, rotation=0, name=None)
add_hyperbola(center_id, a=1.0, b=1.0, rotation=0, name=None)
add_parabola(vertex_id, p=1.0, direction='up', name=None)
add_conic_section(A=1, B=0, C=1, D=0, E=0, F=-1, x_range=(-10,10), y_range=(-10,10), name=None)

# 函数绘图
add_function_plot(expression, x_range=(-10,10), num_points=500, name=None)
add_implicit_plot(expression, x_range=(-10,10), y_range=(-10,10), resolution=400, name=None)
add_polar_plot(expression, theta_range=(0, 2π), num_points=500, name=None)

# 轨迹追踪
add_locus(tracer_point_id, driver_point_id, max_points=1000, name=None)
update_locus(locus_id)
```

### REPL 快捷命令

```python
draw_ellipse(center_id, a, b)
draw_hyperbola(center_id, a, b)
draw_parabola(vertex_id, p, direction)
draw_conic(A, B, C, D, E, F)

plot_function(expr, x_range)
plot_implicit(expr, x_range, y_range)
plot_polar(expr, theta_range)

create_locus(tracer_id, driver_id)
update_locus(locus_id)
```

---

## 7. 常见问题

**Q: 为什么隐函数绘图很慢？**
A: 隐函数需要在网格上逐点计算，分辨率越高越慢。可以尝试降低 `resolution` 参数。

**Q: 如何清除轨迹？**
A: 调用 `locus.clear_trail()` 方法或重新创建轨迹对象。

**Q: 轨迹点太多怎么办？**
A: 创建时设置较小的 `max_points` 参数，或者定期调用 `clear_trail()` 清空旧点。

**Q: 如何在代码中获取曲线上的点？**
A: 通过 `engine.get_object(obj_id).points_data` 访问离散点列表。

**Q: 支持三维图形吗？**
A: 当前版本仅支持二维平面几何。三维功能将在未来版本中添加。

---

## 结语

通过这些新功能，MathLab 现在可以：
- ✅ 直观展示圆锥曲线的几何性质
- ✅ 可视化各类函数图像
- ✅ 动态演示动点轨迹的形成过程
- ✅ 辅助解析几何问题的求解和理解

祝您使用愉快！如有问题，请参考文档或提交 Issue。
