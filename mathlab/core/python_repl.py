import sys
import time
import threading
import jedi
from collections import deque
from .sandbox import SandboxProcess

class PythonREPL:
    def __init__(self, namespace=None):
        # 沙箱模式下不再维护持久化命名空间
        self.history = deque(maxlen=100)
        self.running = False
        self._sandbox = SandboxProcess()  # 单例沙箱实例
    

    
    def execute(self, code_str, timeout=5):
        """
        在独立沙箱中执行代码，确保主程序永不卡死
        注意：沙箱模式下不支持变量持久化，每次执行都是独立环境
        """
        self.running = True
        
        if code_str.strip():
            self.history.append(code_str)
        
        # 直接委托给沙箱进程执行
        sandbox_result = self._sandbox.run_code(code_str, timeout=timeout)
        
        self.running = False
        
        return {
            'success': sandbox_result['success'],
            'output': sandbox_result['output'],
            'error': sandbox_result['error'],
            'more': False  # 沙箱模式下不支持多行交互
        }
    
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
    
    def set_variable(self, name, value):
        raise NotImplementedError("沙箱模式下不支持持久化变量。每次执行都是独立环境。")
    
    def get_variable(self, name):
        raise NotImplementedError("沙箱模式下不支持持久化变量。每次执行都是独立环境。")
    
    def update_namespace(self, updates):
        raise NotImplementedError("沙箱模式下不支持持久化变量。每次执行都是独立环境。")
    
    def get_history(self):
        return list(self.history)
    
    def clear_history(self):
        self.history.clear()
