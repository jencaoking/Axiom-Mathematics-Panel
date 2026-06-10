import sys
import time
import threading
import jedi
from collections import deque

# 支持相对导入和绝对导入两种方式
try:
    from .sandbox import SandboxProcess
except ImportError:
    from sandbox import SandboxProcess

class PythonREPL:
    def __init__(self, namespace=None, session_mode=True):
        """
        初始化 Python REPL
        :param namespace: 保留参数（沙箱模式下不使用）
        :param session_mode: 是否启用会话模式（自动拼接历史代码实现变量持久化）
        """
        self.history = deque(maxlen=100)  # 存储用户输入的历史代码
        self.running = False
        self._sandbox = SandboxProcess()  # 单例沙箱实例
        self._session_mode = session_mode  # 会话模式开关
        self._session_context = []  # 累积的会话上下文（所有成功执行的代码）
    

    
    def execute(self, code_str, timeout=5):
        """
        在独立沙箱中执行代码，确保主程序永不卡死
        
        会话模式：自动将历史代码拼接后重新执行，实现变量持久化
        隔离模式：每次执行都是独立环境（默认更安全）
        """
        self.running = True
        
        if code_str.strip():
            self.history.append(code_str)
        
        # 根据模式构建执行代码
        if self._session_mode:
            # 会话模式：拼接历史上下文 + 当前代码
            execution_code = self._build_session_code(code_str)
        else:
            # 隔离模式：仅执行当前代码
            execution_code = code_str
        
        # 委托给沙箱进程执行
        sandbox_result = self._sandbox.run_code(execution_code, timeout=timeout)
        
        # 如果执行成功且是会话模式，将当前代码加入上下文
        if sandbox_result['success'] and self._session_mode:
            self._session_context.append(code_str)
        
        self.running = False
        
        return {
            'success': sandbox_result['success'],
            'output': sandbox_result['output'],
            'error': sandbox_result['error'],
            'more': False  # 沙箱模式下不支持多行交互
        }
    
    def _build_session_code(self, current_code):
        """
        构建会话代码：将历史上下文与当前代码拼接
        策略：将所有成功执行的代码按顺序拼接，形成完整的执行环境
        """
        if not self._session_context:
            return current_code
        
        # 拼接所有历史代码 + 当前代码
        # 使用 '\n' 分隔，确保每段代码独立成行
        full_code = '\n'.join(self._session_context) + '\n' + current_code
        return full_code
    
    def complete(self, text):
        """
        简单的内置函数补全（沙箱模式下无法访问运行时命名空间）
        """
        matches = []
        
        # 仅补全 Python 内置函数
        builtin_names = [
            'abs', 'all', 'any', 'bool', 'callable', 'chr', 'complex', 'dict',
            'dir', 'divmod', 'enumerate', 'float', 'hash', 'hex', 'id', 'int',
            'isinstance', 'issubclass', 'iter', 'len', 'list', 'map', 'max',
            'min', 'next', 'oct', 'ord', 'pow', 'range', 'repr', 'reversed',
            'round', 'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type',
            'zip', 'print', 'input', 'open', 'file', 'True', 'False', 'None'
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
        try:
            # 沙箱模式下传入空命名空间，仅提供基础补全
            interpreter = jedi.Interpreter(code_str, namespaces=[{'__builtins__': __builtins__}])
            completions = interpreter.complete(line, column)
            return [{
                'name': c.name,
                'type': c.type,
                'description': c.description
            } for c in completions]
        except Exception as e:
            print(f"Jedi Error: {e}")
            return []
    
    def stop(self):
        """停止当前执行的沙箱进程"""
        self.running = False
        self._sandbox.terminate()
    
    def set_session_mode(self, enabled=True):
        """
        动态切换会话模式
        :param enabled: True 启用会话模式（变量持久化），False 禁用（完全隔离）
        """
        self._session_mode = enabled
        if not enabled:
            # 禁用时清空会话上下文
            self._session_context.clear()
    
    def clear_session(self):
        """
        清空会话上下文（保留历史记录）
        用于重置变量状态，但保留用户的输入历史
        """
        self._session_context.clear()
    
    def get_session_context_length(self):
        """
        获取当前会话上下文的代码行数
        """
        return len(self._session_context)
    
    def get_history(self):
        return list(self.history)
    
    def clear_history(self):
        self.history.clear()
