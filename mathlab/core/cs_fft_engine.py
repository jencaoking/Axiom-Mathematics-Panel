import sys
import os
import clr
import numpy as np

# 确保能找到 DLL 路径
dll_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'MathLab.CSharpEngine', 'bin', 'Release', 'netstandard2.0'))
if dll_path not in sys.path:
    sys.path.append(dll_path)

os.environ.setdefault('PYTHONNET_RUNTIME', 'coreclr')

try:
    clr.AddReference("MathLab.CSharpEngine")
    from MathLab.CSharpEngine import FastFFT
except Exception as e:
    print(f"Failed to load C# FFT Engine: {e}")
    FastFFT = None


class CsFFTEngine:
    """频域分析引擎：C# FFT 算力 + NumPy 数据重塑"""
    def __init__(self):
        if FastFFT is None:
            raise RuntimeError("C# Engine DLL is not loaded.")
        self._engine = FastFFT()

    def analyze_spectrum(self, signal_array: np.ndarray, sample_rate: float):
        """
        对一维时域信号进行频域分析
        返回: (frequencies, magnitudes) 两个一维 numpy 数组
        """
        import System

        # 1. 确保信号是一维且类型正确
        signal_np = np.asarray(signal_array, dtype=np.float64).ravel()

        # 2. 极速封送至 C# 环境
        c_signal = System.Array[System.Double](signal_np.tolist())

        # 3. 呼叫 C# 引擎进行原地 FFT 计算
        res_flat = self._engine.ComputeFFT(c_signal, float(sample_rate))

        # 4. 瞬间提取并使用 NumPy 重塑为 N x 2 的矩阵
        res_np = np.array(list(res_flat), dtype=np.float64).reshape(-1, 2)

        # 切片返回：第一列是频率，第二列是幅值
        return res_np[:, 0], res_np[:, 1]


# 全局单例
cs_fft = CsFFTEngine()
