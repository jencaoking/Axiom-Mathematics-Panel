#nullable enable
using System;
using System.Collections.Generic;

namespace MathLab.CSharpEngine;
public class FastGeometry
{
    private const double Epsilon = 1e-10;

    // 【核心优化】：每线程独立常驻缓冲区，杜绝 new 和线程竞争
    [ThreadStatic] private static double[]? t_lineLineBuffer;
    [ThreadStatic] private static double[]? t_circleBuffer;

    private static double[] LineLineBuffer => t_lineLineBuffer ??= new double[2]; // 最多 1 个交点 (x, y)
    private static double[] CircleBuffer => t_circleBuffer ??= new double[4];     // 最多 2 个交点 (x1, y1, x2, y2)

    /// <summary>
    /// 直线与直线交点 (Buffer复用版)
    /// </summary>
    public double[] SolveLineLineFast(double a1, double b1, double c1, double a2, double b2, double c2, out int pointCount)
    {
        pointCount = 0;
        double det = a1 * b2 - a2 * b1;
        if (Math.Abs(det) < Epsilon)
            return LineLineBuffer;

        double rhs1 = -c1;
        double rhs2 = -c2;
        
        // 直接覆写缓冲区
        LineLineBuffer[0] = (rhs1 * b2 - rhs2 * b1) / det;
        LineLineBuffer[1] = (a1 * rhs2 - a2 * rhs1) / det;
        pointCount = 1;

        return LineLineBuffer;
    }

    /// <summary>
    /// 直线与圆交点 (Buffer复用版)
    /// </summary>
    public double[] SolveLineCircleFast(double a, double b, double c, double cx, double cy, double r, out int pointCount)
    {
        pointCount = 0;
        double n2 = a * a + b * b;
        if (n2 < Epsilon) return CircleBuffer;

        double k = a * cx + b * cy + c;
        double n = Math.Sqrt(n2);
        double d = Math.Abs(k) / n;

        if (d > r + Epsilon) return CircleBuffer;

        double fx = cx - a * k / n2;
        double fy = cy - b * k / n2;

        if (Math.Abs(d - r) < Epsilon)
        {
            CircleBuffer[0] = fx;
            CircleBuffer[1] = fy;
            pointCount = 1;
            return CircleBuffer;
        }

        double h2 = r * r - d * d;
        double h = h2 > 0 ? Math.Sqrt(h2) : 0;
        
        CircleBuffer[0] = fx - h * b / n;
        CircleBuffer[1] = fy + h * a / n;
        CircleBuffer[2] = fx + h * b / n;
        CircleBuffer[3] = fy - h * a / n;
        pointCount = 2;

        return CircleBuffer;
    }

    /// <summary>
    /// 圆与圆交点 (Buffer复用版)
    /// </summary>
    public double[] SolveCircleCircleFast(double cx1, double cy1, double r1, double cx2, double cy2, double r2, out int pointCount)
    {
        pointCount = 0;
        double dx = cx2 - cx1;
        double dy = cy2 - cy1;
        double d = Math.Sqrt(dx * dx + dy * dy);

        if (d > r1 + r2 || d < Math.Abs(r1 - r2)) return CircleBuffer;
        if (d < Epsilon && Math.Abs(r1 - r2) < Epsilon) return CircleBuffer;

        double a = (r1 * r1 - r2 * r2 + d * d) / (2 * d);
        double h2 = r1 * r1 - a * a;
        double h = h2 > 0 ? Math.Sqrt(h2) : 0;

        double xm = cx1 + a * dx / d;
        double ym = cy1 + a * dy / d;

        double x1 = xm - h * dy / d;
        double y1 = ym + h * dx / d;
        double x2 = xm + h * dy / d;
        double y2 = ym - h * dx / d;

        if (Math.Abs(h) < Epsilon)
        {
            CircleBuffer[0] = x1;
            CircleBuffer[1] = y1;
            pointCount = 1;
            return CircleBuffer;
        }

        CircleBuffer[0] = x1;
        CircleBuffer[1] = y1;
        CircleBuffer[2] = x2;
        CircleBuffer[3] = y2;
        pointCount = 2;

        return CircleBuffer;
    }

    /// <summary>
    /// 圆锥曲线采样点生成 (双轴采样版)
    /// 对 X 轴和 Y 轴分别扫描，避免切线接近垂直/水平时漏采样
    /// </summary>
    public double[] GenerateConicPoints(double A, double B, double C, double D, double E, double F, double xMin, double xMax, double yMin, double yMax, int numPoints)
    {
        if (numPoints <= 1) return Array.Empty<double>();
        
        List<double> points = new List<double>(numPoints * 4);

        // ── Pass 1：沿 X 轴扫描，对每个 x 解 y ──
        // Cy² + (Bx+E)y + (Ax²+Dx+F) = 0
        double stepX = (xMax - xMin) / (numPoints - 1);
        for (int i = 0; i < numPoints; i++)
        {
            double x = xMin + i * stepX;
            double a_coeff = C;
            double b_coeff = B * x + E;
            double c_coeff = A * x * x + D * x + F;

            AddQuadraticSolutions(points, x, a_coeff, b_coeff, c_coeff, yMin, yMax, isXSweep: true);
        }

        // ── Pass 2：沿 Y 轴扫描，对每个 y 解 x ──
        // Ax² + (By+D)x + (Cy²+Ey+F) = 0
        // 补充 Pass 1 在切线接近垂直时漏掉的采样区域
        double stepY = (yMax - yMin) / (numPoints - 1);
        for (int i = 0; i < numPoints; i++)
        {
            double y = yMin + i * stepY;
            double a_coeff = A;
            double b_coeff = B * y + D;
            double c_coeff = C * y * y + E * y + F;

            AddQuadraticSolutions(points, y, a_coeff, b_coeff, c_coeff, xMin, xMax, isXSweep: false);
        }

        return points.ToArray();
    }

    /// <summary>
    /// 求解二次方程 a*t² + b*t + c = 0 并将有效解添加到点集
    /// </summary>
    /// <param name="fixedCoord">固定坐标值 (x 或 y)</param>
    /// <param name="isXSweep">true 时 fixedCoord 是 x，求 y；false 时 fixedCoord 是 y，求 x</param>
    private static void AddQuadraticSolutions(List<double> points, double fixedCoord,
        double a_coeff, double b_coeff, double c_coeff,
        double rangeMin, double rangeMax, bool isXSweep)
    {
        double discriminant = b_coeff * b_coeff - 4 * a_coeff * c_coeff;
        if (discriminant < 0) return;

        if (Math.Abs(a_coeff) < Epsilon)
        {
            if (Math.Abs(b_coeff) > Epsilon)
            {
                double sol = -c_coeff / b_coeff;
                if (sol >= rangeMin && sol <= rangeMax)
                {
                    if (isXSweep) { points.Add(fixedCoord); points.Add(sol); }
                    else          { points.Add(sol); points.Add(fixedCoord); }
                }
            }
            return;
        }

        double sqrtDisc = Math.Sqrt(discriminant);
        double sol1 = (-b_coeff + sqrtDisc) / (2 * a_coeff);
        double sol2 = (-b_coeff - sqrtDisc) / (2 * a_coeff);

        bool sol1_valid = sol1 >= rangeMin && sol1 <= rangeMax;
        bool sol2_valid = sol2 >= rangeMin && sol2 <= rangeMax;

        if (sol1_valid)
        {
            if (isXSweep) { points.Add(fixedCoord); points.Add(sol1); }
            else          { points.Add(sol1); points.Add(fixedCoord); }
        }
        if (sol2_valid && (!sol1_valid || Math.Abs(sol1 - sol2) > 1e-6))
        {
            if (isXSweep) { points.Add(fixedCoord); points.Add(sol2); }
            else          { points.Add(sol2); points.Add(fixedCoord); }
        }
    }
}
