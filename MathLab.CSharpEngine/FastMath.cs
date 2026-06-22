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
        public Dictionary<string, object> Eigenvalues(double[,] matrix)
        {
            var M = DenseMatrix.OfArray(matrix);
            var evd = M.Evd();
            
            var result = new Dictionary<string, object>();
            result["eigenvalues"] = evd.EigenValues.ToArray();
            result["eigenvectors"] = evd.EigenVectors.ToArray();
            return result;
        }

        /// <summary>
        /// Cholesky 分解
        /// </summary>
        public Dictionary<string, object> Cholesky(double[,] matrix)
        {
            var M = DenseMatrix.OfArray(matrix);
            var cholesky = M.Cholesky();
            
            var result = new Dictionary<string, object>();
            result["L"] = cholesky.Factor.ToArray();
            return result;
        }

        /// <summary>
        /// 求解线性方程组 Ax = b
        /// </summary>
        public Dictionary<string, object> SolveLinearSystem(double[,] A, double[] b)
        {
            var matA = DenseMatrix.OfArray(A);
            var vecB = new DenseVector(b);
            var x = matA.Solve(vecB);
            
            var residual = matA * x - vecB;
            double residualNorm = residual.L2Norm();

            var result = new Dictionary<string, object>();
            result["x"] = x.ToArray();
            result["residual_norm"] = residualNorm;
            return result;
        }
    }
}
