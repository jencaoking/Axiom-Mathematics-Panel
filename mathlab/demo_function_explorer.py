"""
动态函数探索器演示脚本

此脚本展示了如何使用函数探索器的核心功能
"""

import sys
import os

# 添加mathlab目录到路径
mathlab_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, mathlab_dir)

from core.geometry_engine import GeometryEngine

def demo_function_plotting():
    """演示函数绘图功能"""
    print("=" * 70)
    print("动态函数探索器 - 功能演示")
    print("=" * 70)
    
    engine = GeometryEngine()
    
    # 1. 显函数绘图
    print("\n1. 显函数绘图 (y = f(x))")
    print("-" * 70)
    
    functions_explicit = [
        ("x^2", "抛物线"),
        ("sin(x)", "正弦函数"),
        ("exp(-x^2)", "高斯函数"),
        ("1/x", "反比例函数"),
    ]
    
    for expr, desc in functions_explicit:
        obj_id = engine.add_function_plot(expr, x_range=(-5, 5), num_points=300)
        func_obj = engine.get_object(obj_id)
        print(f"   ✓ {desc:12s}: y = {expr:20s} | 点数: {len(func_obj.points_data)}")
    
    # 2. 隐函数绘图
    print("\n2. 隐函数绘图 (f(x,y) = 0)")
    print("-" * 70)
    
    functions_implicit = [
        ("x^2 + y^2 - 4", "圆 (半径2)"),
        ("x^2/4 + y^2/9 - 1", "椭圆"),
        ("x^2 - y^2 - 1", "双曲线"),
    ]
    
    for expr, desc in functions_implicit:
        obj_id = engine.add_implicit_plot(expr, x_range=(-5, 5), y_range=(-5, 5))
        impl_obj = engine.get_object(obj_id)
        print(f"   ✓ {desc:12s}: {expr:20s} | 点数: {len(impl_obj.points_data)}")
    
    # 3. 极坐标绘图
    print("\n3. 极坐标绘图 (r = f(θ))")
    print("-" * 70)
    
    import math
    functions_polar = [
        ("2*cos(theta)", "圆"),
        ("theta", "阿基米德螺线"),
        ("2*(1 + cos(theta))", "心形线"),
    ]
    
    for expr, desc in functions_polar:
        obj_id = engine.add_polar_plot(expr, theta_range=(0, 2*math.pi), num_points=300)
        polar_obj = engine.get_object(obj_id)
        print(f"   ✓ {desc:12s}: r = {expr:20s} | 点数: {len(polar_obj.points_data)}")
    
    # 4. 参数化函数示例
    print("\n4. 参数化函数示例 (带滑块控制)")
    print("-" * 70)
    
    param_functions = [
        ("A*sin(omega*x + phi)", ["A", "omega", "phi"], "正弦波参数化"),
        ("a*x^2 + b*x + c", ["a", "b", "c"], "二次函数一般式"),
        ("a*exp(b*x)", ["a", "b"], "指数函数"),
    ]
    
    for expr, params, desc in param_functions:
        print(f"   • {desc}")
        print(f"     表达式: {expr}")
        print(f"     参数: {', '.join(params)}")
        print(f"     → 系统将自动生成 {len(params)} 个滑块控件")
        print()
    
    # 5. 图象变换示例
    print("\n5. 图象变换演示")
    print("-" * 70)
    
    base_func = "x^2"
    print(f"   基础函数: y = {base_func}")
    print()
    
    transformations = [
        ("右移 1 单位", "(x-1)^2", "f(x) → f(x-1)"),
        ("上移 2 单位", "x^2 + 2", "f(x) → f(x)+2"),
        ("Y轴伸缩 2 倍", "2*x^2", "f(x) → 2*f(x)"),
        ("X轴反射", "(-x)^2", "f(x) → f(-x)"),
        ("Y轴反射", "-(x^2)", "f(x) → -f(x)"),
    ]
    
    for trans_name, result_expr, formula in transformations:
        print(f"   • {trans_name:12s}: y = {result_expr:15s} ({formula})")
    
    print("\n" + "=" * 70)
    print("演示完成!")
    print("=" * 70)
    print("\n提示:")
    print("  • 在 MathLab 中打开 '视图 → 函数探索器' 面板")
    print("  • 输入上述表达式并点击 '绘制函数'")
    print("  • 拖动参数滑块实时观察图象变化")
    print("  • 使用变换按钮快速应用几何变换")
    print()

if __name__ == '__main__':
    demo_function_plotting()
