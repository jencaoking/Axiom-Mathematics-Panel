import sys
import os
import numpy as np

dll_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'MathLab.CSharpEngine', 'bin', 'Release', 'netstandard2.0'))
if dll_path not in sys.path:
    sys.path.append(dll_path)

import os
os.environ.setdefault('PYTHONNET_RUNTIME', 'coreclr')
import clr
try:
    clr.AddReference("MathLab.CSharpEngine")
    from MathLab.CSharpEngine import FastCalculus
except Exception as e:
    print(f"Failed to load C# Calculus Engine: {e}")
    FastCalculus = None

# 导入 .NET 的 Func 泛型委托和 Double 类型
from System import Func, Double

class CsCalculusEngine:
    """自适应微积分混合引擎"""
    def __init__(self):
        if FastCalculus is None:
            raise RuntimeError("C# Engine DLL is not loaded.")
        self._engine = FastCalculus()

    def integrate_adaptive(self, py_func, a: float, b: float, tol: float = 1e-8):
        """
        将 Python Callable 传入 C# 进行自适应积分
        """
        # 【魔法发生地】：将 Python 函数包裹为 C# 的 Func<double, double> 委托
        cs_delegate = Func[Double, Double](py_func)
        
        # 呼叫 C# 引擎，C# 会在内部的自适应循环中不断回调这个委托
        return self._engine.IntegrateAdaptive(cs_delegate, float(a), float(b), float(tol))

    def differentiate(self, py_func, x: float):
        cs_delegate = Func[Double, Double](py_func)
        return self._engine.Differentiate(cs_delegate, float(x))

    def integrate_discrete(self, y_array: np.ndarray, dx: float):
        import System
        # 打平并转为 C# 一维数组 (复用我们在 NumEngine 里的平铺优化)
        c_y_flat = System.Array[System.Double](y_array.ravel().tolist())
        return self._engine.IntegrateDiscrete(c_y_flat, float(dx))

cs_calculus = CsCalculusEngine()
