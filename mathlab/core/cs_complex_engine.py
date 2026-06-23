import sys
import os
import numpy as np

# 确保能找到 DLL 路径
dll_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'MathLab.CSharpEngine', 'bin', 'Release', 'netstandard2.0'))
if dll_path not in sys.path:
    sys.path.append(dll_path)

import clr
try:
    clr.AddReference("MathLab.CSharpEngine")
    from MathLab.CSharpEngine import FastComplex
except Exception as e:
    print(f"Failed to load C# Engine: {e}")
    FastComplex = None

class CsComplexEngine:
    """复平面引擎：连接 C# 算力与 NumPy 色彩渲染"""
    def __init__(self):
        if FastComplex is None:
            raise RuntimeError("C# Engine DLL is not loaded.")
        self._engine = FastComplex()

    def generate_mandelbrot_image(self, x_min, x_max, y_min, y_max, width, height, max_iter=256):
        """
        核心渲染流程：
        1. C# 并行计算出迭代矩阵
        2. Numpy 将迭代次数映射为 RGB 像素矩阵
        """
        # 1. 呼叫 C# 引擎计算 (吃满 CPU 多核)
        # 返回的是 System.Int32[] 
        res_flat = self._engine.GenerateMandelbrot(
            float(x_min), float(x_max), float(y_min), float(y_max), 
            int(width), int(height), int(max_iter)
        )
        
        # 2. 零成本内存转换 (int数组转换极快)
        iter_array = np.array(list(res_flat), dtype=np.int32)
        iter_matrix = iter_array.reshape((height, width))
        
        # 3. Numpy 极速调色盘 (向量化运算，瞬间完成)
        # 创建一个 HxWx3 的 RGB 矩阵
        image_rgb = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 找出那些逃逸的点 (iter < max_iter)
        mask = iter_matrix < max_iter
        
        # 使用平滑着色算法 (基于正弦波)，你可以随后修改这里玩出不同的色彩风格
        # 红色通道
        image_rgb[mask, 0] = (np.sin(0.1 * iter_matrix[mask]) * 127 + 128).astype(np.uint8)
        # 绿色通道
        image_rgb[mask, 1] = (np.sin(0.1 * iter_matrix[mask] + 2.094) * 127 + 128).astype(np.uint8)
        # 蓝色通道
        image_rgb[mask, 2] = (np.sin(0.1 * iter_matrix[mask] + 4.188) * 127 + 128).astype(np.uint8)
        
        # 未逃逸的点 (集合内部) 保持黑色 [0,0,0]
        
        return image_rgb

# 全局单例
cs_complex = CsComplexEngine()
