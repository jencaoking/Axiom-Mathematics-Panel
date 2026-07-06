
from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QShortcut, QKeySequence

from .omni_bar import OmniBar

# ── JupyterLab 嵌入组件（软依赖：WebEngine 不存在时降级为占位面板） ──────────
try:
    from .jupyter_panel import JupyterPanel
    from core.jupyter_manager import JupyterManager
except ImportError:
    try:
        from .jupyter_panel import JupyterPanel
        from ..core.jupyter_manager import JupyterManager
    except ImportError:
        JupyterPanel = None
        JupyterManager = None

try:
    from core.geometry_engine import GeometryEngine
    from core.python_repl import PythonREPL
    from core.ai_manager import AIManager
    from core.cas_provider import CASProvider
    from core.async_workers import TaskManager, AIFitWorker, AIClusterWorker, AIRecognizeWorker, AIGeneratePointsWorker
    from core.command_manager import CommandManager, Command
    from core.ipc_server import JupyterIPCServer
    from core.ipc_client import JupyterIPCClient
    from core.error_manager import AutoSaver
except ImportError:
    from ..core.geometry_engine import GeometryEngine
    from ..core.python_repl import PythonREPL
    from ..core.ai_manager import AIManager
    from ..core.cas_provider import CASProvider
    from ..core.ipc_server import JupyterIPCServer
    from ..core.ipc_client import JupyterIPCClient
    from ..core.error_manager import AutoSaver

try:
    from .preferences_dialog import PreferencesDialog
except ImportError:
    PreferencesDialog = None



try:
    from ..utils.theme_manager import get_current_theme
except ImportError:
    from utils.theme_manager import get_current_theme

try:
    from ..utils.i18n_manager import t, get_i18n
except ImportError:
    from utils.i18n_manager import t, get_i18n

try:
    from ..utils.logger import get_logger
except ImportError:
    from utils.logger import get_logger

logger = get_logger(__name__)


from ._mixin_ui_setup import UISetupMixin
from ._mixin_menus import MenusMixin
from ._mixin_signals import SignalsMixin
from ._mixin_commands import CommandsMixin
from ._mixin_ai import AIMixin
from ._mixin_file_io import FileIOMixin
from ._mixin_dialogs import DialogsMixin

class MainWindow(
    UISetupMixin,
    MenusMixin,
    SignalsMixin,
    CommandsMixin,
    AIMixin,
    FileIOMixin,
    DialogsMixin,
    QMainWindow
):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t('main_window.title'))
        self.setGeometry(100, 100, 1200, 800)

        self._objects_data: dict = {}
        self.current_function_id = None  # 跟踪当前正在编辑的函数ID

        self.geometry_engine = GeometryEngine()
        self.cas_provider = CASProvider()
        self.geometry_engine.set_cas_provider(self.cas_provider)
        self.python_repl = PythonREPL()
        self.ai_manager = AIManager()

        # 将 ai_manager 注入给代码编辑器
        from mathlab.ui.code_editor import AutocompleteTextEdit
        self.code_editor = AutocompleteTextEdit(ai_manager=self.ai_manager)

        # 命令管理器（必须在 setup_ui 前创建，供各面板注册命令）
        self.cmd_manager = CommandManager()

        # 🌟 1. 启动跨进程监听服务 🌟
        self.ipc_server = JupyterIPCServer(port=45678, parent=self)
        self.ipc_server.command_received.connect(self.handle_kernel_command)
        self.ipc_server.start()

        # 🌟 2. 实例化发送器 (发给 Jupyter) 🌟
        self.ipc_client = JupyterIPCClient(port=45679)

        self.setup_ui()
        
        # 将客户端挂载到画板上，供画板使用
        self.central_widget.ipc_client = self.ipc_client
        self.setup_menus()
        self.setup_toolbar()
        self.setup_docks()

        self.load_stylesheet()

        self.current_project = None

        self.active_workers = set()
        self.fit_worker = None
        self.cluster_worker = None
        self.recognize_worker = None
        self.generate_points_worker = None

        self.connect_signals()
        self._register_commands()  # 注册命令面板命令

        get_i18n().add_language_change_listener(self._on_language_changed)
        self.apply_theme(get_current_theme())
        
        # 初始化自动存档与恢复神机
        self.autosaver = AutoSaver(self)
        self.autosaver.check_and_recover()
        
        # 1. 挂载画板追踪器
        from mathlab.core.canvas_tracker import CanvasShadowTracker
        self.canvas_tracker = CanvasShadowTracker(self.geometry_engine)
        
        # 实例化 Omni-Bar，保证生命周期绑定
        self.omni_bar = OmniBar(self)
        
        # 注册全局快捷键 (Ctrl+K 或 Cmd+K)
        self.shortcut_summon = QShortcut(QKeySequence("Ctrl+K"), self)
        self.shortcut_summon.activated.connect(self.toggle_omni_bar)
        
        # 启动 AI 全局交互集成
        self._setup_ai_integration()
        
        # 启动 ECharts 集成
        self._setup_echarts_integration()

    def toggle_omni_bar(self):
        if self.omni_bar.isVisible() and self.omni_bar.windowOpacity() > 0:
            self.omni_bar.dismiss()
        else:
            # 传入当前主窗口的几何数据，用于 Omni-Bar 计算居中位置
            self.omni_bar.summon(self.geometry())
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'omni_bar') and self.omni_bar.isVisible():
            self.omni_bar.dismiss()

    def closeEvent(self, event):
        """在窗口关闭时卸载所有插件，释放资源"""
        if hasattr(self, 'autosaver'):
            self.autosaver.clean_up()
            
        if hasattr(self, 'plugin_manager'):
            try:
                self.plugin_manager.unload_all()
            except Exception as e:
                print(f"Error unloading plugins on close: {e}")
        # 清理所有活动的异步线程
        for worker in list(self.active_workers):
            try:
                worker.quit()
                worker.wait(1000)
            except Exception:
                pass
                
        if hasattr(self, 'ipc_server') and self.ipc_server is not None:
            self.ipc_server.stop()
            
        # 🛑 优雅关闭 JupyterLab 后台进程
        if hasattr(self, 'jupyter_mgr') and self.jupyter_mgr is not None:
            try:
                self.jupyter_mgr.stop()
            except Exception as e:
                logger.warning("关闭 JupyterLab 后台时出错：%s", e)
        super().closeEvent(event)

