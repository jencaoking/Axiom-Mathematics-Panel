using System;
using System.Collections.Generic;

namespace MathLab.CSharpEngine
{
    public class FastGeometry
    {
        private const double Epsilon = 1e-10;

        /// <summary>
        /// 直线与直线交点
        /// 返回平铺数组 [x, y]，无交点返回空数组
        /// </summary>
        public (bool success, double[] result, string error) SolveLineLine(double a1, double b1, double c1, double a2, double b2, double c2)
        {
            try
            {
                double det = a1 * b2 - a2 * b1;
                if (Math.Abs(det) < Epsilon)
                    return (true, new double[0], string.Empty);

                double rhs1 = -c1;
                double rhs2 = -c2;
                double x = (rhs1 * b2 - rhs2 * b1) / det;
                double y = (a1 * rhs2 - a2 * rhs1) / det;

                return (true, new double[] { x, y }, string.Empty);
            }
            catch (Exception ex)
            {
                return (false, null, ex.Message);
            }
        }

        /// <summary>
        /// 直线与圆交点
        /// 返回平铺数组 [x1, y1, x2, y2, ...]
        /// </summary>
        public (bool success, double[] result, string error) SolveLineCircle(double a, double b, double c, double cx, double cy, double r)
        {
            try
            {
                double n2 = a * a + b * b;
                if (n2 < Epsilon) return (true, new double[0], string.Empty);

                double k = a * cx + b * cy + c;
                double n = Math.Sqrt(n2);
                double d = Math.Abs(k) / n;

                if (d > r + Epsilon) return (true, new double[0], string.Empty);

                double fx = cx - a * k / n2;
                double fy = cy - b * k / n2;

                if (Math.Abs(d - r) < Epsilon)
                {
                    return (true, new double[] { fx, fy }, string.Empty);
                }

                double h2 = r * r - d * d;
                double h = h2 > 0 ? Math.Sqrt(h2) : 0;
                
                double x1 = fx - h * b / n;
                double y1 = fy + h * a / n;
                double x2 = fx + h * b / n;
                double y2 = fy - h * a / n;

                return (true, new double[] { x1, y1, x2, y2 }, string.Empty);
            }
            catch (Exception ex)
            {
                return (false, null, ex.Message);
            }
        }

        /// <summary>
        /// 圆与圆交点
        /// 返回平铺数组 [x1, y1, x2, y2, ...]
        /// </summary>
        public (bool success, double[] result, string error) SolveCircleCircle(double cx1, double cy1, double r1, double cx2, double cy2, double r2)
        {
            try
            {
                double dx = cx2 - cx1;
                double dy = cy2 - cy1;
                double d = Math.Sqrt(dx * dx + dy * dy);

                if (d > r1 + r2 || d < Math.Abs(r1 - r2)) return (true, new double[0], string.Empty);
                if (d < Epsilon && Math.Abs(r1 - r2) < Epsilon) return (true, new double[0], string.Empty);

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
                    return (true, new double[] { x1, y1 }, string.Empty);
                }

                return (true, new double[] { x1, y1, x2, y2 }, string.Empty);
            }
            catch (Exception ex)
            {
                return (false, null, ex.Message);
            }
        }

        /// <summary>
        /// 一般二次曲线生成点
        /// Ax^2 + Bxy + Cy^2 + Dx + Ey + F = 0
        /// 返回 flat array [x1, y1, x2, y2, ...]
        /// </summary>
        public (bool success, double[] result, string error) GenerateConicPoints(double A, double B, double C, double D, double E, double F, double xMin, double xMax, double yMin, double yMax, int numPoints)
        {
            try
            {
                if (numPoints <= 1) return (true, new double[0], string.Empty);
                
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
                            if (y2_valid && Math.Abs(y1 - y2) > 1e-6)
                            {
                                points.Add(x);
                                points.Add(y2);
                            }
                        }
                    }
                }

                return (true, points.ToArray(), string.Empty);
            }
            catch (Exception ex)
            {
                return (false, null, ex.Message);
            }
        }
    }
}
