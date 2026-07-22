from collections import deque
from mathlab.utils.logger import get_logger
from mathlab.core.sandbox import SandboxProcess

# jedi 用于代码补全，缺失时降级为无补全（不阻塞启动）
try:
    import jedi
except ImportError:
    jedi = None

logger = get_logger(__name__)


class PythonREPL:
    def __init__(self, namespace=None, session_mode=True):
        """
        初始化 Python REPL
        :param namespace: 保留参数（沙箱模式下不使用）
        :param session_mode: 是否启用会话模式（通过保持 Sandbox 进程存活实现）
        """
        self.history = deque(maxlen=100)  # 存储用户输入的历史代码
        self.running = False
        self._sandbox = SandboxProcess()  # 单例沙箱实例
        self._session_mode = session_mode  # 会话模式开关
        self.namespace = namespace or {}

    def update_namespace(self, vars_dict):
        """更新本地命名空间（用于向 REPL 环境中注入函数/变量）"""
        self.namespace.update(vars_dict)

    def get_namespace(self):
        """获取当前本地命名空间"""
        return self.namespace

    def execute(self, code_str, timeout=5):
        """
        在独立沙箱中执行代码，确保主程序永不卡死
        """
        self.running = True

        try:
            if code_str.strip():
                self.history.append(code_str)

            # 如果禁用了会话模式，强制重启沙箱进程
            if not self._session_mode:
                self._sandbox.terminate()

            # 委托给沙箱进程执行
            sandbox_result = self._sandbox.run_code(code_str, timeout=timeout)

            return {
                "success": sandbox_result["success"],
                "output": sandbox_result["output"],
                "error": sandbox_result["error"],
                "more": False,  # 沙箱模式下不支持多行交互
            }
        finally:
            self.running = False

    def complete(self, text):
        """
        简单的内置函数补全（沙箱模式下无法访问运行时命名空间）
        """
        matches = []

        # 仅补全 Python 内置函数
        builtin_names = [
            "abs",
            "all",
            "any",
            "bool",
            "callable",
            "chr",
            "complex",
            "dict",
            "dir",
            "divmod",
            "enumerate",
            "float",
            "hash",
            "hex",
            "id",
            "int",
            "isinstance",
            "issubclass",
            "iter",
            "len",
            "list",
            "map",
            "max",
            "min",
            "next",
            "oct",
            "ord",
            "pow",
            "range",
            "repr",
            "reversed",
            "round",
            "set",
            "slice",
            "sorted",
            "str",
            "sum",
            "tuple",
            "type",
            "zip",
            "print",
            "input",
            "open",
            "file",
            "True",
            "False",
            "None",
        ]

        for name in builtin_names:
            if name.startswith(text):
                matches.append(name)

        return matches

    def get_completions(self, code_str: str, line: int, column: int) -> list:
        """
        获取代码补全建议
        :param code_str: 当前输入框的完整代码
        :param line: 光标所在行号 (从 1 开始)
        :param column: 光标所在列号 (从 0 开始)
        """
        if jedi is None:
            return []
        try:
            # 沙箱模式下传入空命名空间，仅提供基础补全
            interpreter = jedi.Interpreter(
                code_str, namespaces=[{"__builtins__": __builtins__}]
            )
            completions = interpreter.complete(line, column)
            return [
                {"name": c.name, "type": c.type, "description": c.description}
                for c in completions
            ]
        except Exception as e:
            logger.debug("Jedi 代码补全异常: %s", e)
            return []

    def stop(self):
        """停止当前执行的沙箱进程"""
        self.running = False
        self._sandbox.terminate()

    def set_session_mode(self, enabled=True):
        """
        动态切换会话模式
        :param enabled: True 启用会话模式（变量持久化），False 禁用（每次重启沙箱）
        """
        self._session_mode = enabled
        if not enabled:
            # 禁用时重启沙箱进程以清空状态
            self._sandbox.terminate()

    def clear_session(self):
        """清空会话上下文"""
        self._sandbox.terminate()
        self.history.clear()

    def get_session_context_length(self):
        return len(self.history)

    def get_history(self):
        return list(self.history)

    def clear_history(self):
        self.history.clear()
