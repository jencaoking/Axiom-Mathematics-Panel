import time
import numpy as np

# 首先禁用 cs_geometry
import mathlab.core.cs_geometry_engine as cs_geom
cs_geom.cs_geometry._engine = None 

from mathlab.core.geometry_engine import GeometryEngine

def benchmark_intersections(engine, n_iters=1000):
    # 构建环境
    p1 = engine.add_point(0, 0)
    p2 = engine.add_point(10, 10)
    p3 = engine.add_point(0, 10)
    p4 = engine.add_point(10, 0)
    
    c1 = engine.add_circle(p1, 5)
    c2 = engine.add_circle(p2, 5)
    
    l1 = engine.add_line(p1, p2)
    l2 = engine.add_line(p3, p4)

    # 预热一下获取所有对象
    obj_l1 = engine.get_object(l1)
    obj_l2 = engine.get_object(l2)
    obj_c1 = engine.get_object(c1)
    obj_c2 = engine.get_object(c2)
    
    # 手动调用内部计算
    inter = engine.get_object(engine.add_intersection(c1, c2))
    
    start_t = time.perf_counter()
    for _ in range(n_iters):
        inter._solve_intersection(obj_c1, obj_c2)
        inter._solve_intersection(obj_l1, obj_l2)
        inter._solve_intersection(obj_l1, obj_c1)
    
    return (time.perf_counter() - start_t) * 1000  # ms


def benchmark_conic(engine, n_iters=100):
    conic_id = engine.add_conic_section(1, 0, 1, 0, 0, -25)  # x^2 + y^2 - 25 = 0 (Circle)
    obj_conic = engine.get_object(conic_id)
    
    start_t = time.perf_counter()
    for _ in range(n_iters):
        obj_conic.generate_points(num_points=1000)
    
    return (time.perf_counter() - start_t) * 1000


def run_benchmark():
    print("========================================")
    print("MathLab 几何引擎基准测试 (Python vs C#)")
    print("========================================")
    
    engine = GeometryEngine()
    
    # 纯 Python 测试
    print("[1] 纯 Python 原生算法")
    py_inter = benchmark_intersections(engine, 1000)
    print(f"  > 相交计算 (1000次): {py_inter:.2f} ms")
    py_conic = benchmark_conic(engine, 100)
    print(f"  > 圆锥曲线生成 (100次, 每条1000点): {py_conic:.2f} ms")
    
    # 启用 C# 引擎
    print("\n[2] 启用 C# 优化引擎")
    try:
        import clr
        clr.AddReference("MathLab.CSharpEngine")
        from MathLab.CSharpEngine import FastGeometry
        cs_geom.cs_geometry._engine = FastGeometry()
    except Exception as e:
        print(f"  > 无法加载 C# 引擎: {e}")
        return
        
    cs_inter = benchmark_intersections(engine, 1000)
    print(f"  > 相交计算 (1000次): {cs_inter:.2f} ms")
    cs_conic = benchmark_conic(engine, 100)
    print(f"  > 圆锥曲线生成 (100次, 每条1000点): {cs_conic:.2f} ms")

    print("\n========================================")
    print(f"相交性能提升: {py_inter / cs_inter:.2f}x")
    print(f"曲线生成性能提升: {py_conic / cs_conic:.2f}x")

if __name__ == "__main__":
    run_benchmark()
