using System;
using System.Collections.Generic;
using MathNet.Numerics.LinearAlgebra;
using MathNet.Numerics.LinearAlgebra.Double;

namespace MathLab.CSharpEngine
{
    public class FastMath
    {
        /// <summary>
        /// 计算方阵的特征值和特征向量
        /// </summary>
        public (bool success, double[] eigenvalues_real, double[] eigenvalues_imag, double[] eigenvectors, string error) Eigenvalues(double[] flatMatrix, int rows, int cols)
        {
            try
            {
                var matrix = new double[rows, cols];
                for (int i = 0; i < rows; i++)
                    for (int j = 0; j < cols; j++)
                        matrix[i, j] = flatMatrix[i * cols + j];

                var M = DenseMatrix.OfArray(matrix);
                var evd = M.Evd();
                
                var evs = evd.EigenValues.ToArray();
                var evecs = evd.EigenVectors.ToArray();

                double[] eval_r = new double[evs.Length];
                double[] eval_i = new double[evs.Length];
                for (int i = 0; i < evs.Length; i++)
                {
                    eval_r[i] = evs[i].Real;
                    eval_i[i] = evs[i].Imaginary;
                }

                int vr = evecs.GetLength(0);
                int vc = evecs.GetLength(1);
                double[] evec_flat = new double[vr * vc];
                for (int i = 0; i < vr; i++)
                {
                    for (int j = 0; j < vc; j++)
                    {
                        evec_flat[i * vc + j] = evecs[i, j];
                    }
                }

                return (true, eval_r, eval_i, evec_flat, string.Empty);
            }
            catch (Exception ex)
            {
                return (false, null, null, null, ex.Message);
            }
        }

        /// <summary>
        /// Cholesky 分解
        /// </summary>
        public (bool success, double[] L, string error) Cholesky(double[] flatMatrix, int rows, int cols)
        {
            try
            {
                var matrix = new double[rows, cols];
                for (int i = 0; i < rows; i++)
                    for (int j = 0; j < cols; j++)
                        matrix[i, j] = flatMatrix[i * cols + j];

                var M = DenseMatrix.OfArray(matrix);
                var cholesky = M.Cholesky();
                
                var L_arr = cholesky.Factor.ToArray();
                int lr = L_arr.GetLength(0);
                int lc = L_arr.GetLength(1);
                double[] L_flat = new double[lr * lc];
                for (int i = 0; i < lr; i++)
                {
                    for (int j = 0; j < lc; j++)
                    {
                        L_flat[i * lc + j] = L_arr[i, j];
                    }
                }

                return (true, L_flat, string.Empty);
            }
            catch (Exception ex)
            {
                return (false, null, ex.Message);
            }
        }

        /// <summary>
        /// 求解线性方程组 Ax = b
        /// </summary>
        public (bool success, double[] x, double residualNorm, string error) SolveLinearSystem(double[] flatA, int rows, int cols, double[] b)
        {
            try
            {
                var matrixA = new double[rows, cols];
                for (int i = 0; i < rows; i++)
                    for (int j = 0; j < cols; j++)
                        matrixA[i, j] = flatA[i * cols + j];

                var matA = DenseMatrix.OfArray(matrixA);
                var vecB = new DenseVector(b);
                var x = matA.Solve(vecB);
                
                var residual = matA * x - vecB;
                double residualNorm = residual.L2Norm();

                return (true, x.ToArray(), residualNorm, string.Empty);
            }
            catch (Exception ex)
            {
                return (false, null, 0.0, ex.Message);
            }
        }
    }
}
