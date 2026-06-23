import time
import numpy as np
from mathlab.core.num_engine import NumEngine
from mathlab.core.cs_num_engine import CsNumEngine

def run_benchmark():
    py_engine = NumEngine()
    cs_engine = CsNumEngine()
    
    print("="*40)
    print("MathLab 底层引擎性能基准测试 (SciPy vs MathNet)")
    print("="*40)
    
    # 1. 求解线性方程组 (1000 x 1000 矩阵)
    N = 1000
    print(f"\n[1] 求解线性方程组 ({N}x{N})")
    A = np.random.rand(N, N)
    # Ensure diagonally dominant so it's well-behaved
    A = A + np.eye(N) * N
    b = np.random.rand(N)
    
    # Python (SciPy) 预热
    _ = py_engine.solve_linear_system(A, b)
    # C# (MathNet) 预热
    _ = cs_engine.solve_linear_system(A, b)
    
    t0 = time.time()
    res_py = py_engine.solve_linear_system(A, b)
    t1 = time.time()
    print(f"  > Python (SciPy) 耗时: {(t1 - t0)*1000:.2f} ms | 残差: {res_py['residual_norm']:.2e}")
    
    t0 = time.time()
    res_cs = cs_engine.solve_linear_system(A, b)
    t1 = time.time()
    print(f"  > C# (MathNet)  耗时: {(t1 - t0)*1000:.2f} ms | 残差: {res_cs['residual_norm']:.2e}")
    
    
    # 2. Cholesky 分解 (1000 x 1000 正定矩阵)
    print(f"\n[2] Cholesky 分解 ({N}x{N})")
    # 创建正定矩阵
    M = np.random.rand(N, N)
    A_pd = M @ M.T + np.eye(N) * 1e-3
    
    _ = py_engine.cholesky(A_pd)
    _ = cs_engine.cholesky(A_pd)
    
    t0 = time.time()
    res_py_chol = py_engine.cholesky(A_pd)
    t1 = time.time()
    print(f"  > Python (SciPy) 耗时: {(t1 - t0)*1000:.2f} ms")
    
    t0 = time.time()
    res_cs_chol = cs_engine.cholesky(A_pd)
    t1 = time.time()
    print(f"  > C# (MathNet)  耗时: {(t1 - t0)*1000:.2f} ms")


if __name__ == "__main__":
    run_benchmark()
