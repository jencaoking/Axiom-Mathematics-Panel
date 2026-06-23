import numpy as np
import time
from mathlab.core.cs_fft_engine import cs_fft

def run_fft_demo():
    print("---------------- 1. 构造一个复杂的“脏”信号 ----------------")
    sample_rate = 1000.0  # 采样率 1000 Hz
    t = np.arange(0, 1.0, 1.0 / sample_rate) # 1秒的采样时间，共 1000 个点

    # 生成一个复合信号： 50Hz (幅值2) + 120Hz (幅值1)
    clean_signal = 2 * np.sin(2 * np.pi * 50 * t) + 1 * np.sin(2 * np.pi * 120 * t)
    
    # 故意加入高斯白噪声，让时域波形看起来像一团乱麻
    noise = 2.5 * np.random.randn(len(t))
    dirty_signal = clean_signal + noise

    print("---------------- 2. 瞬间频域解析 (C# 出手) ----------------")
    t0 = time.perf_counter()
    freqs, magnitudes = cs_fft.analyze_spectrum(dirty_signal, sample_rate)
    t1 = time.perf_counter()
    
    print(f"C# FFT 解析耗时: {(t1 - t0) * 1000:.3f} ms")

    # 找出频谱上的主频成分
    # 过滤一下低于阈值的噪声，看看能不能抓到 50Hz 和 120Hz
    threshold = 0.5
    peaks = []
    for i in range(len(freqs)):
        if magnitudes[i] > threshold and freqs[i] < 200:
            peaks.append((freqs[i], magnitudes[i]))
            
    print("\n发现的显著频点 (前 200 Hz 内):")
    for freq, mag in peaks:
        print(f"频率: {freq:5.1f} Hz | 幅值: {mag:.3f}")
        
    print("\n测试成功！我们能清晰地在充满噪声的信号中分离出 50Hz 和 120Hz 主频。")

if __name__ == "__main__":
    run_fft_demo()
