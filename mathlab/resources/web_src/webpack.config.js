const path = require('path');
const MonacoWebpackPlugin = require('monaco-editor-webpack-plugin');

module.exports = {
  mode: 'production',
  entry: './mathlab_editor.ts', // 指向刚才写的 TS 文件
  output: {
    path: path.resolve(__dirname, '../dist'), // 打包输出到上一级的 dist 目录
    filename: 'mathlab_editor.bundle.js'
  },
  module: {
    rules: [
      { test: /\.ts$/, use: 'ts-loader', exclude: /node_modules/ },
      { test: /\.css$/, use: ['style-loader', 'css-loader'] },
      { test: /\.ttf$/, type: 'asset/resource' } // 处理 Monaco 的字体图标
    ]
  },
  resolve: { extensions: ['.ts', '.js'] },
  plugins: [
    new MonacoWebpackPlugin({
      languages: ['python'] // 我们只需要打包 Python 语言的高亮，极大减小体积
    })
  ]
};
