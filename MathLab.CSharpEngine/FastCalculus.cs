#nullable enable
using System;
using MathNet.Numerics.Integration;
using MathNet.Numerics.Differentiation;

namespace MathLab.CSharpEngine;
public class FastCalculus
{
    // 初始化数值微分器 (中心差分法，精度极高)
    private readonly NumericalDerivative _differentiator = new NumericalDerivative();

    /// <summary>
    /// 自适应数值积分 (接收来自 Python 的动态函数委托)
    /// 采用双指数变换算法 (Double Exponential Transformation)，极其擅长处理端点奇点和高频振荡
    /// </summary>
    public double IntegrateAdaptive(Func<double, double> f, double a, double b, double targetTolerance)
    {
        try
        {
            // GaussKronrodRule 或 DoubleExponentialTransformation 都可以
            // 这里使用 DoubleExponential 鲁棒性最强
            return DoubleExponentialTransformation.Integrate(f, a, b, targetTolerance);
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"数值积分不收敛或发生错误: {ex.Message}");
        }
    }

    /// <summary>
    /// 高精度数值微分
    /// </summary>
    public double Differentiate(Func<double, double> f, double x)
    {
        // EvaluateDerivative 的参数：函数, x值, 求导阶数(1代表一阶导数)
        return _differentiator.EvaluateDerivative(f, x, 1);
    }

    /// <summary>
    /// 离散点云的极速辛普森积分 (Simpson's 1/3 Rule)
    /// 专门用于处理 3D 曲面体积、离散采样数据的积分，无惧 GC 压力
    /// </summary>
    public double IntegrateDiscrete(double[] yArray, double dx)
    {
        if (yArray == null || yArray.Length < 3) return 0;

        int n = yArray.Length - 1;
        
        // [BUG修复] Simpson 1/3 法则要求偶数个区间（奇数个点）
        // 如果 n 为奇数，最后一个区间用梯形法则单独处理
        int simpsonN = (n % 2 == 0) ? n : n - 1;
        double sum = yArray[0] + yArray[simpsonN];

        for (int i = 1; i < simpsonN; i++)
        {
            sum += (i % 2 == 0) ? 2 * yArray[i] : 4 * yArray[i];
        }

        double result = sum * dx / 3.0;
        
        // 如果 n 为奇数，最后一个区间使用梯形法则补偿
        if (simpsonN < n)
        {
            result += (yArray[n - 1] + yArray[n]) * dx / 2.0;
        }

        return result;
    }
}

