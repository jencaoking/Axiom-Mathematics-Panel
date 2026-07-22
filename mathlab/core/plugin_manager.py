# mathlab/core/plugin_manager.py
import importlib
import inspect
import os
from typing import Dict

from mathlab.core.extension_api import MathLabAPI
from mathlab.core.plugin_base import MathLabPlugin
from mathlab.utils.logger import get_logger

logger = get_logger(__name__)


class PluginManager:
    def __init__(self, api_context: MathLabAPI, plugin_dir: str = None):
        self.api = api_context
        if plugin_dir is None:
            self.plugin_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
        else:
            self.plugin_dir = plugin_dir
        self.active_plugins: Dict[str, MathLabPlugin] = {}
        self.plugin_apis: Dict[str, MathLabAPI] = {}

        # 确保插件目录存在
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            # 创建 __init__.py 使其成为包
            with open(os.path.join(self.plugin_dir, "__init__.py"), "w") as _:
                pass

    def load_all_plugins(self):
        """扫描插件目录并加载所有符合规范的插件"""
        plugin_base_module = "mathlab.plugins"

        if not os.path.exists(self.plugin_dir):
            return

        for item in os.listdir(self.plugin_dir):
            item_path = os.path.join(self.plugin_dir, item)

            # 我们假设每个插件是一个独立的文件夹，且内部有一个 main.py
            if os.path.isdir(item_path) and not item.startswith("__") and not item.startswith("."):
                main_py_path = os.path.join(item_path, "main.py")
                if os.path.exists(main_py_path):
                    try:
                        module_name = f"{plugin_base_module}.{item}.main"
                        module = importlib.import_module(module_name)

                        # 在模块中寻找继承自 MathLabPlugin 的类
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if issubclass(obj, MathLabPlugin) and obj is not MathLabPlugin:
                                self._activate_plugin(obj())

                    except Exception as e:
                        logger.error("插件 [%s] 加载失败: %s", item, e, exc_info=True)

    def _activate_plugin(self, plugin_instance: MathLabPlugin):
        plugin_id = (
            plugin_instance.name if plugin_instance.name != "Unnamed Plugin" else plugin_instance.__class__.__name__
        )
        if plugin_id in self.active_plugins:
            logger.warning("插件 [%s] 已加载，跳过重复激活。", plugin_id)
            return

        try:
            # 为每个插件创建一个专属的 API 实例，从而隔离注册的组件
            plugin_api = MathLabAPI(self.api._main_window, self.api._cmd_manager, self.api._console)
            plugin_instance.on_activate(plugin_api)
            self.active_plugins[plugin_id] = plugin_instance
            self.plugin_apis[plugin_id] = plugin_api
            logger.info("插件 [%s] v%s 激活成功。", plugin_id, plugin_instance.version)
        except Exception as e:
            logger.error("激活插件 [%s] 时出错: %s", plugin_id, e, exc_info=True)

    def unload_all(self):
        for plugin_name, plugin in list(self.active_plugins.items()):
            try:
                plugin.on_deactivate()
                logger.info("插件 [%s] 已停用。", plugin_name)
            except Exception as e:
                logger.error("停用插件 [%s] 时出错: %s", plugin_name, e, exc_info=True)

            # 清理该插件分配的 API 注册的命令/UI 面板
            if plugin_name in self.plugin_apis:
                try:
                    self.plugin_apis[plugin_name].cleanup()
                except Exception as e:
                    logger.error("清理插件 [%s] API 时出错: %s", plugin_name, e, exc_info=True)
                del self.plugin_apis[plugin_name]

        self.active_plugins.clear()
