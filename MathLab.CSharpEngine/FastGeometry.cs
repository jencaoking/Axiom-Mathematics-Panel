#nullable enable
using System;
using System.Collections.Generic;

namespace MathLab.CSharpEngine;
public class FastGeometry
{
    private const double Epsilon = 1e-10;

    // 【核心优化】：预分配常驻内存缓冲区，杜绝 new 操作
    // 假设单例运行，避免了高频 GC。如果有并发多线程需求，可改为 [ThreadStatic] 或加锁
    private readonly double[] _lineLineBuffer = new double[2]; // 最多 1 个交点 (x, y)
    private readonly double[] _circleBuffer = new double[4];   // 最多 2 个交点 (x1, y1, x2, y2)

    /// <summary>
    /// 直线与直线交点 (Buffer复用版)
    /// </summary>
    public double[] SolveLineLineFast(double a1, double b1, double c1, double a2, double b2, double c2, out int pointCount)
    {
        pointCount = 0;
        double det = a1 * b2 - a2 * b1;
        if (Math.Abs(det) < Epsilon)
            return _lineLineBuffer;

        double rhs1 = -c1;
        double rhs2 = -c2;
        
        // 直接覆写缓冲区
        _lineLineBuffer[0] = (rhs1 * b2 - rhs2 * b1) / det;
        _lineLineBuffer[1] = (a1 * rhs2 - a2 * rhs1) / det;
        pointCount = 1;

        return _lineLineBuffer;
    }

    /// <summary>
    /// 直线与圆交点 (Buffer复用版)
    /// </summary>
    public double[] SolveLineCircleFast(double a, double b, double c, double cx, double cy, double r, out int pointCount)
    {
        pointCount = 0;
        double n2 = a * a + b * b;
        if (n2 < Epsilon) return _circleBuffer;

        double k = a * cx + b * cy + c;
        double n = Math.Sqrt(n2);
        double d = Math.Abs(k) / n;

        if (d > r + Epsilon) return _circleBuffer;

        double fx = cx - a * k / n2;
        double fy = cy - b * k / n2;

        if (Math.Abs(d - r) < Epsilon)
        {
            _circleBuffer[0] = fx;
            _circleBuffer[1] = fy;
            pointCount = 1;
            return _circleBuffer;
        }

        double h2 = r * r - d * d;
        double h = h2 > 0 ? Math.Sqrt(h2) : 0;
        
        _circleBuffer[0] = fx - h * b / n;
        _circleBuffer[1] = fy + h * a / n;
        _circleBuffer[2] = fx + h * b / n;
        _circleBuffer[3] = fy - h * a / n;
        pointCount = 2;

        return _circleBuffer;
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

        if (d > r1 + r2 || d < Math.Abs(r1 - r2)) return _circleBuffer;
        if (d < Epsilon && Math.Abs(r1 - r2) < Epsilon) return _circleBuffer;

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
            _circleBuffer[0] = x1;
            _circleBuffer[1] = y1;
            pointCount = 1;
            return _circleBuffer;
        }

        _circleBuffer[0] = x1;
        _circleBuffer[1] = y1;
        _circleBuffer[2] = x2;
        _circleBuffer[3] = y2;
        pointCount = 2;

        return _circleBuffer;
    }

    public double[] GenerateConicPoints(double A, double B, double C, double D, double E, double F, double xMin, double xMax, double yMin, double yMax, int numPoints)
    {
        if (numPoints <= 1) return Array.Empty<double>();
        
        List<double> points = new List<double>(numPoints * 4);
        double step = (xMax - xMin) / (numPoints - 1);

        for (int i = 0; i < numPoints; i++)
        {
            double x = xMin + i * step;
            double a_coeff = C;
            double b_coeff = B * x + E;
            double c_coeff = A * x * x + D * x + F;

            double discriminant = b_coeff * b_coeff - 4 * a_coeff * c_coeff;

            if (discriminant >= 0)
            {
                if (Math.Abs(a_coeff) < Epsilon)
                {
                    if (Math.Abs(b_coeff) > Epsilon)
                    {
                        double y = -c_coeff / b_coeff;
                        if (y >= yMin && y <= yMax)
                        {
                            points.Add(x);
                            points.Add(y);
                        }
                    }
                }
                else
                {
                    double sqrtDisc = Math.Sqrt(discriminant);
                    double y1 = (-b_coeff + sqrtDisc) / (2 * a_coeff);
                    double y2 = (-b_coeff - sqrtDisc) / (2 * a_coeff);

                    bool y1_valid = y1 >= yMin && y1 <= yMax;
                    bool y2_valid = y2 >= yMin && y2 <= yMax;

                    if (y1_valid)
                    {
                        points.Add(x);
                        points.Add(y1);
                    }
                    if (y2_valid && (!y1_valid || Math.Abs(y1 - y2) > 1e-6))
                    {
                        points.Add(x);
                        points.Add(y2);
                    }
                }
            }
        }

        return points.ToArray();
    }
}

