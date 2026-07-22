import json
import sys

from PySide6.QtCore import QObject, Slot, Signal


class EChartsBridge(QObject):
    """
    ECharts 插件的 Python <-> JavaScript 双向通信桥梁。
    参考 plugin_3d_viewer/bridge.py 中 ThreeJSBridge 的实现模式。
    """

    # 当 JS 端报告渲染完成时触发
    on_render_complete = Signal(str)

    def __init__(self, api):
        super().__init__()
        self.api = api

    @Slot(str)
    def js_log(self, message: str):
        """允许 JS 向 Python 控制台打印日志"""
        self.api.print_to_console(f"[ECharts] {message}", "info")

    @Slot(str)
    def js_error(self, message: str):
        """允许 JS 向 Python 控制台打印错误信息"""
        self.api.print_to_console(f"[ECharts ❌] {message}", "error")

    @Slot(str)
    def on_chart_ready(self, chart_type: str):
        """当 ECharts 图表渲染完毕时，JS 会回调此方法"""
        self.api.print_to_console(f"[ECharts ✅] 图表渲染完成: {chart_type}", "info")
        self.on_render_complete.emit(chart_type)


def render_chart(options: dict):
    """
    沙箱内调用的桥接函数。
    它将 Python 字典转为 JSON，并包装在特殊的边界符中打印到 stdout。
    主进程的沙箱看门狗会拦截这段字符串，而不会把它当作普通的 log 显示。
    """
    try:
        # 确保 numpy array 等特殊类型能被序列化（如果需要，可添加自定义编码器）
        payload = json.dumps(options, ensure_ascii=False)

        # 打印魔术边界符
        print(f"\n__ECHARTS_IPC_START__\n{payload}\n__ECHARTS_IPC_END__\n")

        # 强制刷新缓冲区，确保主进程立刻收到
        sys.stdout.flush()

    except Exception as e:
        print(f"ECharts 序列化失败: {e}", file=sys.stderr)
