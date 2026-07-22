# mathlab/core/extension_api.py
import logging


class MathLabAPI:
    """提供给插件的安全接口集合"""

    def __init__(self, main_window, cmd_manager, console):
        self._main_window = main_window
        self._cmd_manager = cmd_manager
        self._console = console
        self._registered_commands = []
        self._dynamic_panels = []

    def register_command(self, id: str, title: str, action, category: str = "Plugin"):
        """允许插件向系统的命令面板注册新指令"""
        from mathlab.core.command_manager import Command

        cmd = Command(id, title, action, category)
        self._cmd_manager.register(cmd)
        self._registered_commands.append(id)
        logging.info(f"[MathLabAPI] Registered command: {id}")

    def add_sidebar_panel(self, panel_name: str, widget, icon=None):
        """允许插件添加一个新的 UI 面板到主窗口侧边栏"""
        dock = self._main_window.add_dynamic_panel(panel_name, widget, icon)
        self._dynamic_panels.append(dock)
        logging.info(f"[MathLabAPI] Added sidebar panel: {panel_name}")
        return dock

    def print_to_console(self, text: str, color_or_level: str = "info"):
        """允许插件向控制台输出信息"""
        # 兼容 level 和 color 格式。如果是 '#...' 开头的十六进制颜色，我们就按 'info' 级输出，并在前缀带上颜色（或者直接按 info 处理）
        level = "info"
        if color_or_level.startswith("#"):
            # 颜色参数，我们可以统一作为 info 消息显示
            level = "info"
        else:
            level = color_or_level
        self._console.display_system_message(text, level)

    def execute_script(self, script: str):
        """允许插件在 REPL (沙箱) 中运行代码"""
        if self._console.python_repl:
            return self._console.python_repl.execute(script)
        return {"success": False, "error": "REPL not initialized"}

    def cleanup(self):
        """插件注销时，清理它注册的所有命令和面板"""
        # 注销所有命令
        for cmd_id in self._registered_commands:
            self._cmd_manager.unregister(cmd_id)
            logging.info(f"[MathLabAPI] Unregistered command: {cmd_id}")
        self._registered_commands.clear()

        # 移除所有面板
        for dock in self._dynamic_panels:
            self._main_window.removeDockWidget(dock)
            dock.deleteLater()
            logging.info(
                f"[MathLabAPI] Removed sidebar panel dock: {dock.objectName()}"
            )
        self._dynamic_panels.clear()
