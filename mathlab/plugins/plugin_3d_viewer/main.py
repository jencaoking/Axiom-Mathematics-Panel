# mathlab/plugins/plugin_3d_viewer/main.py
import os
import json
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl
from mathlab.core.plugin_base import MathLabPlugin
from .bridge import ThreeJSBridge

class ThreeJSViewerPlugin(MathLabPlugin):
    name = "3D Geometry Viewer"
    version = "2.0.0"
    author = "MathLab Team"
    description = "原生支持 MathLab 3D 拓扑约束的动态空间几何画板。"

    def on_activate(self, api):
        self.api = api
        self.web_view = QWebEngineView()
        
        self.channel = QWebChannel()
        self.bridge = ThreeJSBridge(api)
        self.channel.registerObject("py_bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        html_path = os.path.join(os.path.dirname(__file__), "web", "index.html")
        self.web_view.load(QUrl.fromLocalFile(html_path))
        
        # 核心：将 3D 面板挂载到主窗口
        self.dock = api.main_window.add_dynamic_panel("3D 画板", self.web_view)
        
        # 核心：监听底层几何引擎的拓扑变化！
        if hasattr(self.api, 'geometry_engine'):
            self.api.geometry_engine.add_listener(self.on_geometry_event)

    def on_geometry_event(self, event_type, data):
        """当引擎中添加、移动或删除物体时，立即同步给 Three.js"""
        # 如果是 JS 本身发起的拖拽更新，则不要再推回去（防止无限踢皮球）
        if hasattr(self, 'bridge') and getattr(self.bridge, '_is_syncing_from_js', False):
            return
            
        # 无论发生什么事件，直接把整棵依赖树的所有坐标打包发给前端
        self.sync_scene()

    def sync_scene(self):
        """序列化当前 GeometryEngine 中的所有对象，推送到 JS"""
        if not hasattr(self.api, 'geometry_engine'):
            return
            
        objects = self.api.geometry_engine.get_all_objects()
        payload = [obj.serialize() for obj in objects]
        
        # 将 JSON 转为字符串并转义，防止 JS 解析报错
        json_str = json.dumps(payload).replace("\\", "\\\\").replace("'", "\\'")
        js_code = f"if (window.updateScene) window.updateScene('{json_str}');"
        
        self.web_view.page().runJavaScript(js_code)

    def on_deactivate(self):
        if hasattr(self, 'dock'):
            self.dock.close()
