# mathlab/plugins/echarts_viewer/bridge.py
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
import json

class EChartsBridge(QObject):
    """
    负责 Python 与 JavaScript 之间的双向通信
    注意：暴露给 JS 的方法必须使用 @pyqtSlot 装饰器
    """
    # 定义一个 Qt 信号，当 JS 捕获到图表点击事件时触发
    on_data_clicked = pyqtSignal(str, float, float) 

    def __init__(self, api):
        super().__init__()
        self.api = api

    @pyqtSlot(str)
    def js_log(self, message):
        """允许 JS 调用 Python 的控制台打印日志"""
        self.api.print_to_console(f"[WebEngine] {message}", color="#aaaaaa")

    @pyqtSlot(str, float, float)
    def handle_chart_click(self, series_name, x, y):
        """当用户在网页中点击数据点时，JS 会调用此方法"""
        msg = f"图表交互: 选中了 '{series_name}' 的数据点 P({x:.2f}, {y:.2f})"
        self.api.print_to_console(msg, color="#00ffcc")
        # 这里你可以将获取到的 x, y 注入到沙盒变量中，供用户后续计算使用
        self.on_data_clicked.emit(series_name, x, y)
