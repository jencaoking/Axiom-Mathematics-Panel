"""
解析几何深化功能测试脚本
测试圆锥曲线、函数绘图和轨迹追踪功能
"""
import sys
import os

# 添加项目路径
mathlab_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, mathlab_dir)

# 直接导入 geometry_engine 模块，避免触发 core/__init__.py
import importlib.util
spec = importlib.util.spec_from_file_location("geometry_engine", os.path.join(mathlab_dir, "core", "geometry_engine.py"))
geometry_engine_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geometry_engine_module)
GeometryEngine = geometry_engine_module.GeometryEngine
import numpy as np

def test_conic_sections():
    """测试圆锥曲线"""
    print("=" * 60)
    print("测试1: 圆锥曲线")
    print("=" * 60)
    
    engine = GeometryEngine()
    
    # 测试椭圆
    print("\n1.1 创建椭圆...")
    center_id = engine.add_point(0, 0, name='C1')
    ellipse_id = engine.add_ellipse(center_id, a=3.0, b=2.0)
    ellipse = engine.get_object(ellipse_id)
    print(f"   椭圆创建成功: {ellipse.name}")
    print(f"   方程: {ellipse.to_latex()}")
    print(f"   点数: {len(ellipse.coordinates.get('points', []))}")
    
    # 测试双曲线
    print("\n1.2 创建双曲线...")
    center_id2 = engine.add_point(5, 0, name='C2')
    hyperbola_id = engine.add_hyperbola(center_id2, a=2.0, b=1.5)
    hyperbola = engine.get_object(hyperbola_id)
    print(f"   双曲线创建成功: {hyperbola.name}")
    print(f"   方程: {hyperbola.to_latex()}")
    
    # 测试抛物线
    print("\n1.3 创建抛物线...")
    vertex_id = engine.add_point(0, -2, name='V1')
    parabola_id = engine.add_parabola(vertex_id, p=1.0, direction='up')
    parabola = engine.get_object(parabola_id)
    print(f"   抛物线创建成功: {parabola.name}")
    print(f"   方程: {parabola.to_latex()}")
    
    # 测试一般圆锥曲线
    print("\n1.4 创建一般圆锥曲线 (圆)...")
    conic_id = engine.add_conic_section(A=1, B=0, C=1, D=0, E=0, F=-4)
    conic = engine.get_object(conic_id)
    print(f"   圆锥曲线创建成功: {conic.name}")
    print(f"   方程: {conic.to_latex()}")
    print(f"   生成点数: {len(conic.points_data)}")
    
    print("\n✓ 圆锥曲线测试通过!")


def test_function_plots():
    """测试函数绘图"""
    print("\n" + "=" * 60)
    print("测试2: 函数绘图")
    print("=" * 60)
    
    engine = GeometryEngine()
    
    # 测试显函数 y = x^2
    print("\n2.1 绘制显函数 y = x^2...")
    func1_id = engine.add_function_plot('x**2', x_range=(-5, 5), num_points=200)
    func1 = engine.get_object(func1_id)
    print(f"   函数绘图创建成功: {func1.name}")
    print(f"   表达式: {func1.expression}")
    print(f"   生成点数: {len(func1.points_data)}")
    if func1.points_data:
        print(f"   示例点: {func1.points_data[0]}, {func1.points_data[len(func1.points_data)//2]}")
    
    # 测试正弦函数
    print("\n2.2 绘制正弦函数 y = sin(x)...")
    from sympy import sin
    func2_id = engine.add_function_plot('sin(x)', x_range=(-6.28, 6.28), num_points=300)
    func2 = engine.get_object(func2_id)
    print(f"   正弦函数创建成功: {func2.name}")
    print(f"   生成点数: {len(func2.points_data)}")
    
    # 测试隐函数 x^2 + y^2 = 1 (单位圆)
    print("\n2.3 绘制隐函数 x^2 + y^2 - 1 = 0...")
    impl_id = engine.add_implicit_plot('x**2 + y**2 - 1', x_range=(-2, 2), y_range=(-2, 2))
    impl = engine.get_object(impl_id)
    print(f"   隐函数绘图创建成功: {impl.name}")
    print(f"   表达式: {impl.expression}")
    print(f"   生成点数: {len(impl.points_data)}")
    
    # 测试极坐标 r = 2*cos(theta) (圆)
    print("\n2.4 绘制极坐标 r = 2*cos(theta)...")
    polar_id = engine.add_polar_plot('2*cos(theta)', theta_range=(0, 2*np.pi), num_points=300)
    polar = engine.get_object(polar_id)
    print(f"   极坐标绘图创建成功: {polar.name}")
    print(f"   表达式: {polar.expression}")
    print(f"   生成点数: {len(polar.points_data)}")
    
    print("\n✓ 函数绘图测试通过!")


def test_locus():
    """测试动点轨迹"""
    print("\n" + "=" * 60)
    print("测试3: 动点轨迹追踪")
    print("=" * 60)
    
    engine = GeometryEngine()
    
    # 创建驱动点和追踪点
    print("\n3.1 创建驱动点和追踪点...")
    driver_id = engine.add_point(0, 0, name='Driver')
    tracer_id = engine.add_point(2, 0, name='Tracer')
    
    # 创建轨迹追踪器
    print("3.2 创建轨迹追踪器...")
    locus_id = engine.add_locus(tracer_id, driver_id, max_points=100)
    locus = engine.get_object(locus_id)
    print(f"   轨迹追踪器创建成功: {locus.name}")
    print(f"   追踪点ID: {locus.tracer_point_id}")
    print(f"   驱动点ID: {locus.driver_point_id}")
    
    # 模拟点的移动并更新轨迹
    print("\n3.3 模拟驱动点移动并更新轨迹...")
    for i in range(10):
        angle = i * 0.5
        x = 3 * np.cos(angle)
        y = 3 * np.sin(angle)
        engine.update_point(driver_id, x=x, y=y)
        
        # 假设追踪点与驱动点有某种关系（这里简单设置为相同位置）
        engine.update_point(tracer_id, x=x+1, y=y)
        
        # 更新轨迹
        engine.update_locus(locus_id)
    
    locus = engine.get_object(locus_id)
    print(f"   轨迹点数: {len(locus.trail_points)}")
    if locus.trail_points:
        print(f"   前3个点: {locus.trail_points[:3]}")
    
    print("\n✓ 动点轨迹测试通过!")


def test_serialization():
    """测试序列化和反序列化"""
    print("\n" + "=" * 60)
    print("测试4: 序列化/反序列化")
    print("=" * 60)
    
    engine = GeometryEngine()
    
    # 创建各种对象
    print("\n4.1 创建测试对象...")
    center_id = engine.add_point(0, 0, name='Center')
    ellipse_id = engine.add_ellipse(center_id, a=3.0, b=2.0)
    func_id = engine.add_function_plot('x**2', x_range=(-5, 5))
    
    # 序列化
    print("4.2 序列化所有对象...")
    data = engine.serialize_all()
    print(f"   序列化完成，对象数: {len(data['objects'])}")
    
    # 创建新引擎并反序列化
    print("4.3 反序列化到新引擎...")
    engine2 = GeometryEngine()
    engine2.deserialize_all(data)
    print(f"   反序列化完成，对象数: {len(engine2.objects)}")
    
    # 验证对象
    for obj_id, obj in engine2.objects.items():
        print(f"   - {obj.type}: {obj.name}")
    
    print("\n✓ 序列化/反序列化测试通过!")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("解析几何深化功能测试套件")
    print("=" * 60)
    
    try:
        test_conic_sections()
        test_function_plots()
        test_locus()
        test_serialization()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
