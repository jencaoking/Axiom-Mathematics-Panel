# mathlab/plugins/plugin_3d_viewer/main.py
import os
import json
import numpy as np
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl
from mathlab.core.plugin_base import MathLabPlugin
from .bridge import ThreeJSBridge


class ThreeJSViewerPlugin(MathLabPlugin):
    """
    3D 曲面渲染插件。
    策略：Python 负责 NumPy 高性能计算 Z 轴数组，
    前端 Three.js 负责构建 PlaneGeometry 网格并完成光照渲染。
    """
    name = "3D Surface Viewer"
    version = "1.0.0"
    author = "MathLab Team"
    description = "基于 Three.js 的 3D 曲面实时渲染引擎，支持多种数学曲面与交互式轨道控制。"

    # 网格精度配置
    SEGMENTS = 80   # 80×80 网格 → 6561 个顶点，兼顾质量与性能
    SIZE = 20       # 空间范围 [-10, 10]

    def on_activate(self, api):
        self.api = api

        # ── 1. 构建 WebEngine 视图 ──────────────────────────────────────────
        self.web_view = QWebEngineView()

        # ── 2. 建立 Qt ↔ JS 通信信道 ─────────────────────────────────────────
        self.channel = QWebChannel()
        self.bridge = ThreeJSBridge(api)
        self.channel.registerObject("py_bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # ── 3. 加载本地 Three.js 前端 ─────────────────────────────────────────
        html_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "web", "index.html"
        )
        self.web_view.load(QUrl.fromLocalFile(html_path))

        # ── 4. 注册到侧边栏 ──────────────────────────────────────────────────
        api.add_sidebar_panel("3D 空间", self.web_view)

        # ── 5. 注册渲染指令 ──────────────────────────────────────────────────
        surfaces = [
            ("plot3d.ripple",   "3D渲染: 水波纹涟漪 (Ripple)",           "ripple"),
            ("plot3d.saddle",   "3D渲染: 双曲抛物面 / 马鞍面 (Saddle)",  "saddle"),
            ("plot3d.peaks",    "3D渲染: 高斯峰丛 (Peaks)",              "peaks"),
            ("plot3d.torus_z",  "3D渲染: 圆环截面 (Torus Z)",            "torus_z"),
            ("plot3d.sine_xy",  "3D渲染: 二元正弦叠加 (Sine XY)",        "sine_xy"),
            ("plot3d.gaussian", "3D渲染: 三维高斯函数 (Gaussian)",        "gaussian"),
        ]
        for cmd_id, title, shape in surfaces:
            # 使用默认参数捕获 shape，避免闭包共用同一变量
            api.register_command(
                id=cmd_id,
                title=title,
                action=lambda s=shape: self._render_surface(s),
                category="3D视图"
            )

        api.print_to_console("[3D Surface Viewer] 插件加载完毕，共注册 6 个曲面指令。", "info")

    # ── 核心计算逻辑 ─────────────────────────────────────────────────────────

    def _render_surface(self, shape_type: str):
        """
        用 NumPy 计算指定曲面的 Z 值矩阵，
        然后将扁平化后的一维数组序列化为 JSON 推送给 Three.js 渲染。
        """
        self.api.print_to_console(
            f"[3D Engine] 正在计算 '{shape_type}' 曲面（{self.SEGMENTS}×{self.SEGMENTS} 网格）...",
            "info"
        )

        n = self.SEGMENTS + 1  # 每边顶点数
        half = self.SIZE / 2
        x = np.linspace(-half, half, n)
        y = np.linspace(-half, half, n)
        X, Y = np.meshgrid(x, y)

        # ── 各曲面计算公式 ─────────────────────────────────────────────────
        if shape_type == "ripple":
            R = np.sqrt(X**2 + Y**2) + 1e-9
            Z = 4.0 * np.sin(R) / R                         # sinc 衰减水波

        elif shape_type == "saddle":
            Z = (X**2 - Y**2) / 10.0                        # 双曲抛物面

        elif shape_type == "peaks":
            # MATLAB peaks() 函数的标准实现
            Z = (3 * (1 - X/3)**2 * np.exp(-(X/3)**2 - (Y/3 + 1)**2)
                 - 10 * (X/30 - (X/3)**3 - (Y/3)**5) * np.exp(-(X/3)**2 - (Y/3)**2)
                 - (1/3) * np.exp(-(X/3 + 1)**2 - (Y/3)**2))

        elif shape_type == "torus_z":
            R_outer = 7.0   # 大半径
            r_inner = 3.0   # 小半径
            dist = np.sqrt(X**2 + Y**2)
            inner_sq = r_inner**2 - (dist - R_outer)**2
            # 只在圆环管道范围内有效，其他区域设为 0
            valid = inner_sq >= 0
            Z = np.where(valid, np.sqrt(np.maximum(inner_sq, 0)), 0.0)

        elif shape_type == "sine_xy":
            Z = np.sin(X * 0.5) * np.cos(Y * 0.5) * 4.0   # 二元正弦叠加

        elif shape_type == "gaussian":
            # 多个高斯峰的叠加
            Z = (3.0 * np.exp(-0.1 * (X**2 + Y**2))
                 + 2.0 * np.exp(-0.3 * ((X - 5)**2 + (Y - 5)**2))
                 + 1.5 * np.exp(-0.3 * ((X + 5)**2 + (Y - 4)**2)))

        else:
            self.api.print_to_console(f"[3D Engine] 未知曲面类型: {shape_type}", "error")
            return

        # ── 归一化 Z 轴并打包为 JSON ────────────────────────────────────────
        z_flat = Z.flatten()
        z_min, z_max = float(z_flat.min()), float(z_flat.max())

        payload = {
            "shape":    shape_type,
            "size":     self.SIZE,
            "segments": self.SEGMENTS,
            "z_values": [round(float(v), 4) for v in z_flat],
            "z_min":    round(z_min, 4),
            "z_max":    round(z_max, 4),
        }

        json_str = json.dumps(payload)
        # 使用转义处理，防止 JSON 字符串中的单引号破坏 JS 调用
        escaped = json_str.replace("\\", "\\\\").replace("'", "\\'")
        js_script = f"window.renderSurface('{escaped}');"
        self.web_view.page().runJavaScript(js_script)

    def on_deactivate(self):
        """释放 WebEngine 页面资源，彻底终止 Chromium 渲染子进程。"""
        if hasattr(self, "web_view") and self.web_view:
            self.web_view.page().setWebChannel(None)
            # deleteLater() 延迟至 Qt 事件循环空闲时销毁 C++ 层对象，
            # 从而终止 Chromium 渲染子进程并回收显存与内存。
            self.web_view.deleteLater()
            self.web_view = None
