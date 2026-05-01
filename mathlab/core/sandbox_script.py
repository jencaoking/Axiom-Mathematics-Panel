import sys
import builtins
import types
import importlib
import traceback
from io import StringIO

SAFE_MODULES = {
    'math',
    'sympy',
    'sympy.core',
    'sympy.functions',
    'sympy.solvers',
    'sympy.integrals',
    'sympy.series',
    'sympy.matrices',
    'sympy.geometry',
}

SAFE_BUILTINS = {
    'abs', 'all', 'any', 'bool', 'callable', 'chr', 'complex', 'dict',
    'float', 'hash', 'help', 'hex', 'int', 'isinstance', 'issubclass',
    'iter', 'len', 'list', 'map', 'max', 'min', 'next', 'oct', 'ord',
    'pow', 'range', 'repr', 'reversed', 'round', 'set', 'slice', 'sorted',
    'str', 'sum', 'tuple', 'type', 'zip', 'print'
}

def create_safe_builtins():
    safe_builtins = {}
    for name in SAFE_BUILTINS:
        if hasattr(builtins, name):
            safe_builtins[name] = getattr(builtins, name)
    return safe_builtins

class SafeModuleLoader:
    def __init__(self):
        self.loaded_modules = {}
    
    def __getattr__(self, name):
        full_name = name
        if full_name in self.loaded_modules:
            return self.loaded_modules[full_name]
        
        if full_name not in SAFE_MODULES:
            raise ImportError(f"Module '{full_name}' is not allowed")
        
        module = importlib.import_module(full_name)
        self.loaded_modules[full_name] = module
        return module

class SandboxExecutionError(Exception):
    pass

def execute_sandboxed(code, timeout=5):
    safe_globals = {
        '__builtins__': create_safe_builtins(),
        '__name__': '__sandbox__',
        '__doc__': None,
        '__package__': None,
        '__spec__': None,
        '__loader__': None,
        '__annotations__': {},
    }
    
    top_level_modules = {m.split('.')[0] for m in SAFE_MODULES}
    for module_name in top_level_modules:
        try:
            module = importlib.import_module(module_name)
            safe_globals[module_name] = module
        except ImportError:
            pass
    
    captured_output = StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_output
    
    try:
        exec(code, safe_globals, {})
        return {
            'success': True,
            'output': captured_output.getvalue(),
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'output': captured_output.getvalue(),
            'error': str(e),
            'traceback': traceback.format_exc()
        }
    finally:
        sys.stdout = old_stdout

if __name__ == '__main__':
    test_code = '''
print("Sandbox test: Safe execution environment")
'''
    result = execute_sandboxed(test_code)
    print("Execution Result:", result)