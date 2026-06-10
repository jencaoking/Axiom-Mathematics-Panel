import code
import io
import sys
import re
import contextlib
import builtins
import time
import threading
import jedi
from collections import deque

class PythonREPL:
    def __init__(self, namespace=None):
        self.namespace = namespace if namespace is not None else {}
        self.namespace['__name__'] = '__console__'
        self.namespace['__doc__'] = None
        
        self.console = code.InteractiveConsole(self.namespace)
        self.history = deque(maxlen=100)
        self.running = False
        
        self._setup_shortcuts()
    
    def _setup_shortcuts(self):
        def clear_history():
            self.history.clear()
            return 'History cleared'
        
        def list_vars():
            public_vars = [k for k in self.namespace.keys() if not k.startswith('_')]
            return '\n'.join(public_vars)
        
        def clear_namespace():
            keys_to_remove = [k for k in list(self.namespace.keys()) 
                              if not k.startswith('_') and not k.startswith('%')]
            for k in keys_to_remove:
                del self.namespace[k]
            return 'Namespace cleared'
        
        self.namespace['%clear'] = clear_namespace
        self.namespace['%history'] = lambda: '\n'.join(self.history)
        self.namespace['%vars'] = list_vars
    
    def _capture_output(self, func):
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(error_buffer):
            result = func()
        
        output = output_buffer.getvalue()
        error = error_buffer.getvalue()
        
        return result, output, error
    
    def execute(self, code_str, timeout=5):
        self.running = True
        
        if code_str.strip():
            self.history.append(code_str)
        
        if code_str.strip().startswith('%'):
            return self._execute_command(code_str)
        
        result_container = {'more': None, 'output': '', 'error': '', 'success': False}
        timer = None
        
        def run_code():
            try:
                more, output, error = self._capture_output(lambda: self.console.push(code_str))
                result_container.update({'more': more, 'output': output, 'error': error, 'success': not more})
            except Exception as e:
                result_container['error'] = str(e)
        
        thread = threading.Thread(target=run_code)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            result_container['error'] = f"Execution timed out after {timeout} seconds"
            # Note: We can't easily kill the thread in Python, but we mark it as failed.
            # For true isolation, use SandboxProcess.
        
        self.running = False
        
        return {
            'success': result_container['success'],
            'output': result_container['output'],
            'error': result_container['error'],
            'more': result_container['more']
        }
    
    def _execute_command(self, cmd):
        parts = cmd.strip().split()
        command = parts[0]
        args = parts[1:]
        
        try:
            if command == '%clear':
                result = self.namespace['%clear']()
                return {'success': True, 'output': result, 'error': '', 'more': False}
            elif command == '%history':
                result = self.namespace['%history']()
                return {'success': True, 'output': result, 'error': '', 'more': False}
            elif command == '%vars':
                result = self.namespace['%vars']()
                return {'success': True, 'output': result, 'error': '', 'more': False}
            else:
                return {'success': False, 'output': '', 'error': f'Unknown command: {command}', 'more': False}
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e), 'more': False}
    
    def complete(self, text):
        matches = []
        
        for name in self.namespace:
            if name.startswith(text):
                matches.append(name)
        
        for name in dir(builtins):
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
            interpreter = jedi.Interpreter(code_str, namespaces=[self.namespace])
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
        self.running = False
    
    def set_variable(self, name, value):
        self.namespace[name] = value
    
    def get_variable(self, name):
        return self.namespace.get(name)
    
    def update_namespace(self, updates):
        self.namespace.update(updates)
    
    def get_history(self):
        return list(self.history)
    
    def clear_history(self):
        self.history.clear()
