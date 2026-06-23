#nullable enable
using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using MathNet.Numerics.LinearAlgebra;
using MathNet.Numerics.LinearAlgebra.Double;

namespace MathLab.CSharpEngine;
public class FastMath
{
    public Dictionary<string, object> Eigenvalues(double[,] matrix)
    {
        var M = DenseMatrix.OfArray(matrix);
        var evd = M.Evd();
        
        var result = new Dictionary<string, object>();
        result["eigenvalues"] = evd.EigenValues.ToArray();
        result["eigenvectors"] = evd.EigenVectors.ToArray();
        return result;
    }

    public Dictionary<string, object> Cholesky(double[,] matrix)
    {
        var M = DenseMatrix.OfArray(matrix);
        var cholesky = M.Cholesky();
        
        var result = new Dictionary<string, object>();
        result["L"] = cholesky.Factor.ToArray();
        return result;
    }

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

    // --- 新增：高性能一维平铺数组接口 (Flat API) ---

    public Dictionary<string, object> EigenvaluesFlat(double[] flatMatrix, int rows, int cols)
    {
        var matrix = new double[rows, cols];
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++)
                matrix[i, j] = flatMatrix[i * cols + j];
        var M = DenseMatrix.OfArray(matrix);
        
        var evd = M.Evd();
        
        var result = new Dictionary<string, object>();
        result["eigenvalues"] = evd.EigenValues.ToArray();
        
        var eigenVecs = evd.EigenVectors.ToArray();
        var flatVecs = new System.Numerics.Complex[rows * cols];
        int idx = 0;
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++)
                flatVecs[idx++] = eigenVecs[i, j];
                
        result["eigenvectors"] = flatVecs;
        return result;
    }

    public Dictionary<string, object> CholeskyFlat(double[] flatMatrix, int rows, int cols)
    {
        var matrix = new double[rows, cols];
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++)
                matrix[i, j] = flatMatrix[i * cols + j];
        var M = DenseMatrix.OfArray(matrix);
        var cholesky = M.Cholesky();
        
        var L_arr = cholesky.Factor.ToArray();
        var L_flat = new double[rows * cols];
        int idx = 0;
        for (int i = 0; i < L_arr.GetLength(0); i++)
            for (int j = 0; j < L_arr.GetLength(1); j++)
                L_flat[idx++] = L_arr[i, j];
        
        var result = new Dictionary<string, object>();
        result["L"] = L_flat; 
        return result;
    }

    public Dictionary<string, object> SolveLinearSystemFlat(double[] flatA, int rows, int cols, double[] b)
    {
        var matrixA = new double[rows, cols];
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++)
                matrixA[i, j] = flatA[i * cols + j];
        var matA = DenseMatrix.OfArray(matrixA);
        var vecB = new DenseVector(b);
        var x = matA.Solve(vecB);
        
        var residual = matA * x - vecB;

        var result = new Dictionary<string, object>();
        result["x"] = x.ToArray(); 
        result["residual_norm"] = residual.L2Norm();
        return result;
    }
}

