# mathlab/plugins/plugin_3d_viewer/bridge.py
from PySide6.QtCore import QObject, Slot, Signal


class ThreeJSBridge(QObject):
    """
    负责 Python 与 Three.js 前端之间的双向通信。
    所有暴露给 JS 的槽函数必须使用 @Slot 装饰器。
    """
    # 当 JS 端报告渲染完成时触发（携带顶点数量）
    on_render_complete = Signal(int)

    def __init__(self, api):
        super().__init__()
        self.api = api

    @Slot(str)
    def js_log(self, message: str):
        """允许 JS 向 Python 控制台打印日志"""
        self.api.print_to_console(f"[3D Engine] {message}", "info")

    @Slot(str)
    def js_error(self, message: str):
        """允许 JS 向 Python 控制台打印错误信息"""
        self.api.print_to_console(f"[3D Engine ❌] {message}", "error")

    @Slot(int)
    def on_mesh_ready(self, vertex_count: int):
        """当 Three.js 网格构建完毕时，JS 会回调此方法"""
        self.api.print_to_console(
            f"[3D Engine ✅] 网格渲染完成，共 {vertex_count:,} 个顶点。", "info"
        )
        self.on_render_complete.emit(vertex_count)

    # 👇 新增：接收 Three.js 中鼠标拖拽点的实时坐标
    @Slot(str, float, float, float)
    def update_point_from_js(self, obj_id: str, x: float, y: float, z: float):
        """当用户在 3D 画布中拖动点时，更新核心引擎"""
        self._is_syncing_from_js = True
        try:
            if hasattr(self.api, 'geometry_engine'):
                # 阻塞信号防止循环触发 (Python->JS->Python)
                self.api.geometry_engine.block_signals(True)
                self.api.geometry_engine.update_point(obj_id, x=x, y=y, z=z)
                self.api.geometry_engine.block_signals(False)

                # 拖拽结束后，让引擎通知所有监听者刷新 (包括代数面板和 2D 画布)
                # 因为引擎的 update_point 内部会自动触发下游物体的更新
                updated_obj = self.api.geometry_engine.get_object(obj_id)
                if updated_obj:
                    self.api.geometry_engine._notify('object_updated', updated_obj.serialize())
        finally:
            self._is_syncing_from_js = False
