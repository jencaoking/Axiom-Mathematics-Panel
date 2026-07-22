# mathlab/plugins/echarts_viewer/main.py
import os
import json
import numpy as np
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl
from mathlab.core.plugin_base import MathLabPlugin
from .bridge import EChartsBridge
from mathlab.utils.i18n_manager import t


class EChartsViewerPlugin(MathLabPlugin):
    name = "ECharts Data Viewer"
    version = "1.0.0"

    def on_activate(self, api):
        self.api = api

        # 1. 实例化浏览器内核组件
        self.web_view = QWebEngineView()

        # 2. 建立通信信道
        self.channel = QWebChannel()
        self.bridge = EChartsBridge(api)
        # "py_bridge" 必须与 HTML 中 channel.objects.py_bridge 保持一致
        self.channel.registerObject("py_bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # 3. 加载本地前端工程
        html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "index.html")
        self.web_view.load(QUrl.fromLocalFile(html_path))

        # 4. 添加到 MathLab 侧边栏
        api.add_sidebar_panel(t("plugins.echarts"), self.web_view)

        # 5. 注册控制台测试指令
        api.register_command(
            id="plot.demo_wave",
            title="渲染演示: 衰减正弦波 (Damped Sine Wave)",
            action=self._render_demo_data,
            category="Web图表"
        )
        api.print_to_console("[ECharts Plugin] Module activated.", color_or_level="#aaffaa")

    def _render_demo_data(self):
        """模拟 Python 后端计算大量数据，并推给前端渲染"""
        self.api.print_to_console("正在生成 1000 个采样点...", color_or_level="#cccccc")

        # 使用 numpy 生成 x 和 y 坐标 (模拟高强度计算)
        # f(x) = sin(x) * e^(-0.1x)
        x = np.linspace(0, 50, 1000)
        y = np.sin(x) * np.exp(-0.05 * x)

        # 组装我们定义好的 JSON Protocol
        payload = {
            "title": "衰减振荡曲线",
            "x_data": [round(val, 3) for val in x.tolist()],
            "y_data": [round(val, 3) for val in y.tolist()]
        }

        # 序列化并发送给 JavaScript 环境执行
        json_str = json.dumps(payload)
        js_script = f"window.renderChart('{json_str}');"
        self.web_view.page().runJavaScript(js_script)

    def on_deactivate(self):
        # 卸载时的资源清理逻辑
        pass
