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
    }
}
