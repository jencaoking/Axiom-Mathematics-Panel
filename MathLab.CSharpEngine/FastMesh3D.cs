#nullable enable
using System;
using System.Threading.Tasks;

namespace MathLab.CSharpEngine;
public class FastMesh3D
{
    /// <summary>
    /// 高性能 3D 动态波纹曲面网格生成
    /// 返回一维平铺数组：[x1, y1, z1, x2, y2, z2, ...] 供 WebGL BufferGeometry 直接加载
    /// </summary>
    public float[] GenerateRippleMesh(double xMin, double xMax, double yMin, double yMax, int xSegments, int ySegments, double timeParam, double frequency)
    {
        // [BUG修复] 参数校验：防止零或负数导致崩溃
        if (xSegments <= 0 || ySegments <= 0)
            throw new ArgumentException("xSegments and ySegments must be positive.");

        // 计算顶点总数与面片所需的浮点数大小
        // 为了让 WebGL 渲染最快，我们直接生成未索引的三角形顶点流 (Triangles List)
        // 每个矩形网格由 2 个三角形组成 = 6个顶点 = 18个 float 元素
        int totalFloats = xSegments * ySegments * 18;
        float[] meshBuffer = new float[totalFloats];

        double dx = (xMax - xMin) / xSegments;
        double dy = (yMax - yMin) / ySegments;

        // 并行计算 X 轴切片，吃满 CPU 每一个核心
        Parallel.For(0, xSegments, i =>
        {
            double x0 = xMin + i * dx;
            double x1 = x0 + dx;

            for (int j = 0; j < ySegments; j++)
            {
                double y0 = yMin + j * dy;
                double y1 = y0 + dy;

                // 计算矩形网格的 4 个角顶点的 Z 轴高度 (经典的 sin(r)/r 涟漪函数 + 时间相位)
                float z00 = CalculateRipple(x0, y0, timeParam, frequency);
                float z10 = CalculateRipple(x1, y0, timeParam, frequency);
                float z01 = CalculateRipple(x0, y1, timeParam, frequency);
                float z11 = CalculateRipple(x1, y1, timeParam, frequency);

                // 计算当前矩形在常驻一维缓冲区中的绝对偏移量
                int offset = (i * ySegments + j) * 18;

                // 三角形 1 (顶点 00 -> 10 -> 01)
                meshBuffer[offset + 0] = (float)x0;  meshBuffer[offset + 1] = (float)y0;  meshBuffer[offset + 2] = z00;
                meshBuffer[offset + 3] = (float)x1;  meshBuffer[offset + 4] = (float)y0;  meshBuffer[offset + 5] = z10;
                meshBuffer[offset + 6] = (float)x0;  meshBuffer[offset + 7] = (float)y1;  meshBuffer[offset + 8] = z01;

                // 三角形 2 (顶点 10 -> 11 -> 01)
                meshBuffer[offset + 9] = (float)x1;  meshBuffer[offset + 10] = (float)y0; meshBuffer[offset + 11] = z10;
                meshBuffer[offset + 12] = (float)x1; meshBuffer[offset + 13] = (float)y1; meshBuffer[offset + 14] = z11;
                meshBuffer[offset + 15] = (float)x0; meshBuffer[offset + 16] = (float)y1; meshBuffer[offset + 17] = z01;
            }
        });

        return meshBuffer;
    }

    private float CalculateRipple(double x, double y, double t, double freq)
    {
        double r = Math.Sqrt(x * x + y * y);
        // sin(freq*r)*cos(t)/r 的极限 (r→0) = freq*cos(t)，数学上严格成立
        if (r < 1e-6) return (float)(freq * Math.Cos(t));
        return (float)(Math.Sin(freq * r) * Math.Cos(t) / r);
    }
}

