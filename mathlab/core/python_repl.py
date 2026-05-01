import code
import io
import sys
import re
from collections import deque

class PythonREPL:
    def __init__(self, namespace=None):
        self.namespace = namespace if namespace is not None else {}
        self.namespace['__name__'] = '__console__'
        self.namespace['__doc__'] = None
        
        self.console = code.InteractiveConsole(self.namespace)
        self.history = deque(maxlen=100)
        self.running = False
        self.output_buffer = io.StringIO()
        self.error_buffer = io.StringIO()
        
        self._setup_shortcuts()
    
    def _setup_shortcuts(self):
        def clear_history():
            self.history.clear()
            return 'History cleared'
        
        def list_vars():
            public_vars = [k for k in self.namespace.keys() if not k.startswith('_')]
            return '\n'.join(public_vars)
        
        self.namespace['%clear'] = lambda: self.namespace.clear() or 'Namespace cleared'
        self.namespace['%history'] = lambda: '\n'.join(self.history)
        self.namespace['%vars'] = list_vars
    
    def _capture_output(self, func):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        sys.stdout = self.output_buffer
        sys.stderr = self.error_buffer
        
        try:
            result = func()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        output = self.output_buffer.getvalue()
        error = self.error_buffer.getvalue()
        
        self.output_buffer = io.StringIO()
        self.error_buffer = io.StringIO()
        
        return result, output, error
    
    def execute(self, code_str):
        self.running = True
        
        if code_str.strip():
            self.history.append(code_str)
        
        if code_str.strip().startswith('%'):
            return self._execute_command(code_str)
        
        def run_code():
            return self.console.push(code_str)
        
        more, output, error = self._capture_output(run_code)
        
        self.running = False
        
        return {
            'success': not more,
            'output': output,
            'error': error,
            'more': more
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
        
        for name in dir(__builtins__):
            if name.startswith(text):
                matches.append(name)
        
        return matches
    
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
