import sys
import os

print("Testing SmartCalculusSolver...")
from mathlab.core.cas_provider import SmartCalculusSolver

solver = SmartCalculusSolver()

print("\n--- 案例 1: 有完美解析解的函数 ---")
# 案例 1: 有完美解析解的函数
res1 = solver.solve_integral("x**2", "x", 0, 1)
print(f"Result 1: {res1}")

print("\n--- 案例 2: 没有解析解的著名函数 ---")
# 案例 2: 没有解析解的著名函数 (高斯积分或复杂三角组合)
# SymPy 算不出积分原函数，会触发降级，C# 会瞬间算出数值解
res2 = solver.solve_integral("sin(x)/x", "x", 1, 10)
print(f"Result 2: {res2}")

print("\nTest completed successfully!")
