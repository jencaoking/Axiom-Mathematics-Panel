using System;
using System.Threading.Tasks;

namespace MathLab.CSharpEngine
{
    public class FastComplex
    {
        /// <summary>
        /// 并行计算 Mandelbrot 集合逃逸时间
        /// 返回一维平铺的 int 数组，表示每个像素点的迭代次数
        /// </summary>
        public int[] GenerateMandelbrot(double xMin, double xMax, double yMin, double yMax, int width, int height, int maxIterations)
        {
            int[] result = new int[width * height];
            
            // 计算每个像素在复平面上对应的步长
            double dx = (xMax - xMin) / (width - 1);
            double dy = (yMax - yMin) / (height - 1);

            // 开启多核并行计算，将 Y 轴切分给多个 CPU 线程
            Parallel.For(0, height, y =>
            {
                // 注意：屏幕 Y 轴向下，复平面 Y(虚轴) 向上，这里做反转映射
                double cImag = yMax - y * dy; 
                int rowOffset = y * width;

                for (int x = 0; x < width; x++)
                {
                    double cReal = xMin + x * dx;
                    
                    // Z_0 = C
                    double zReal = cReal;
                    double zImag = cImag;
                    int iter = 0;
                    
                    // 缓存平方值，减少乘法运算次数 (性能极高)
                    double zReal2 = zReal * zReal;
                    double zImag2 = zImag * zImag;

                    // 逃逸判定半径 R=2 (R^2 = 4)
                    while (zReal2 + zImag2 <= 4.0 && iter < maxIterations)
                    {
                        // Z_{n+1} = Z_n^2 + C 展开
                        zImag = 2 * zReal * zImag + cImag;
                        zReal = zReal2 - zImag2 + cReal;
                        
                        zReal2 = zReal * zReal;
                        zImag2 = zImag * zImag;
                        iter++;
                    }
                    
                    // 记录该像素点的最终迭代次数
                    result[rowOffset + x] = iter;
                }
            });

            return result;
        }
        public int[] GenerateJulia(double xMin, double xMax, double yMin, double yMax, int width, int height, int maxIterations, double cReal, double cImag)
        {
            int[] result = new int[width * height];
            
            double dx = (xMax - xMin) / (width - 1);
            double dy = (yMax - yMin) / (height - 1);

            // 同样开启多核并行
            Parallel.For(0, height, y =>
            {
                double pixelImag = yMax - y * dy; // 屏幕坐标转复平面虚轴
                int rowOffset = y * width;

                for (int x = 0; x < width; x++)
                {
                    double pixelReal = xMin + x * dx; // 屏幕坐标转复平面实轴
                    
                    // Julia 集的关键区别：Z 的初始值是当前像素坐标，C 是全图固定的常数
                    double zReal = pixelReal;
                    double zImag = pixelImag;
                    int iter = 0;
                    
                    double zReal2 = zReal * zReal;
                    double zImag2 = zImag * zImag;

                    while (zReal2 + zImag2 <= 4.0 && iter < maxIterations)
                    {
                        // 展开复数乘法
                        zImag = 2 * zReal * zImag + cImag;
                        zReal = zReal2 - zImag2 + cReal;
                        
                        zReal2 = zReal * zReal;
                        zImag2 = zImag * zImag;
                        iter++;
                    }
                    
                    result[rowOffset + x] = iter;
                }
            });

            return result;
        }

        public float[] GenerateMandelbrotSmooth(double xMin, double xMax, double yMin, double yMax, int width, int height, int maxIterations)
        {
            float[] result = new float[width * height];
            double dx = (xMax - xMin) / (width - 1);
            double dy = (yMax - yMin) / (height - 1);

            // 逃逸半径的平方加大，半径越大，平滑对数计算越精准。这里设 R=100，R^2=10000
            const double EscapeRadiusSq = 10000.0;
            const double Log2 = 0.6931471805599453; // 预计算 ln(2) 极速常量

            Parallel.For(0, height, y =>
            {
                double cImag = yMax - y * dy;
                int rowOffset = y * width;

                for (int x = 0; x < width; x++)
                {
                    double cReal = xMin + x * dx;
                    double zReal = cReal;
                    double zImag = cImag;
                    int iter = 0;

                    double zReal2 = zReal * zReal;
                    double zImag2 = zImag * zImag;

                    while (zReal2 + zImag2 <= EscapeRadiusSq && iter < maxIterations)
                    {
                        zImag = 2 * zReal * zImag + cImag;
                        zReal = zReal2 - zImag2 + cReal;
                        zReal2 = zReal * zReal;
                        zImag2 = zImag * zImag;
                        iter++;
                    }

                    if (iter < maxIterations)
                    {
                        // 【魔法时刻】连续逃逸时间微积分平滑公式
                        // modulus = sqrt(zReal2 + zImag2) -> ln(modulus) = 0.5 * ln(zReal2 + zImag2)
                        double log_zn = Math.Log(zReal2 + zImag2) / 2.0;
                        double nu = Math.Log(log_zn / Log2) / Log2;
                        
                        // 保存为浮点数：使得颜色从离散的阶梯变成了平滑的斜坡
                        result[rowOffset + x] = (float)(iter + 1 - nu);
                    }
                    else
                    {
                        // 集合内部（未逃逸）
                        result[rowOffset + x] = (float)maxIterations;
                    }
                }
            });

            return result;
        }
    }
}
