#nullable enable
using System;
using System.Numerics;
using MathNet.Numerics.IntegralTransforms;

namespace MathLab.CSharpEngine;
public class FastFFT
{
    /// <summary>
    /// 极速快速傅里叶变换 (FFT)
    /// 自动丢弃冗余的共轭对称部分，直接输出平铺的 [freq0, mag0, freq1, mag1...] 数组
    /// </summary>
    /// <param name="signal">一维时域信号样本</param>
    /// <param name="sampleRate">采样率 (Hz)</param>
    /// <returns>平铺的频率与幅值数组</returns>
    public double[] ComputeFFT(double[] signal, double sampleRate)
    {
        if (signal == null || signal.Length == 0)
            throw new ArgumentException("Signal array must not be null or empty.");

        int n = signal.Length;
        
        // FFT 需要复数数组。实数信号的虚部初始化为 0
        Complex[] complexSignal = new Complex[n];
        for (int i = 0; i < n; i++)
        {
            complexSignal[i] = new Complex(signal[i], 0);
        }

        // 执行原地 (In-place) 快速傅里叶变换，速度极快
        Fourier.Forward(complexSignal, FourierOptions.Default);

        // 对于实数信号，FFT 结果是对称的，我们只需要前半部分 (0 到 奈奎斯特频率)
        int halfN = n / 2 + 1; // [BUG修复] 包含奈奎斯特频率分量
        
        // 预分配缓冲区: 长度为 halfN * 2 (每个频点包含一个频率值和一个幅值)
        double[] result = new double[halfN * 2];

        for (int i = 0; i < halfN; i++)
        {
            double freq = i * sampleRate / n;
            
            // 计算幅值并进行物理归一化 (直流分量除以 N，其他交流分量除以 N/2)
            // 奈奎斯特频点 (偶数长度时 i==n/2) 同样是自共轭的，不应乘以 2
            double magnitude = complexSignal[i].Magnitude;
            bool isNyquist = (n % 2 == 0) && (i == n / 2);
            magnitude = (i == 0 || isNyquist) ? (magnitude / n) : (magnitude * 2.0 / n);

            result[i * 2] = freq;
            result[i * 2 + 1] = magnitude;
        }

        return result;
    }
}

