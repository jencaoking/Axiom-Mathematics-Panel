# mathlab/plugins/plugin_3d_viewer/bridge.py
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal


class ThreeJSBridge(QObject):
    """
    负责 Python 与 Three.js 前端之间的双向通信。
    所有暴露给 JS 的槽函数必须使用 @pyqtSlot 装饰器。
    """
    # 当 JS 端报告渲染完成时触发（携带顶点数量）
    on_render_complete = pyqtSignal(int)

    def __init__(self, api):
        super().__init__()
        self.api = api

    @pyqtSlot(str)
    def js_log(self, message: str):
        """允许 JS 向 Python 控制台打印日志"""
        self.api.print_to_console(f"[3D Engine] {message}", "info")

    @pyqtSlot(str)
    def js_error(self, message: str):
        """允许 JS 向 Python 控制台打印错误信息"""
        self.api.print_to_console(f"[3D Engine ❌] {message}", "error")

    @pyqtSlot(int)
    def on_mesh_ready(self, vertex_count: int):
        """当 Three.js 网格构建完毕时，JS 会回调此方法"""
        self.api.print_to_console(
            f"[3D Engine ✅] 网格渲染完成，共 {vertex_count:,} 个顶点。", "info"
        )
        self.on_render_complete.emit(vertex_count)
