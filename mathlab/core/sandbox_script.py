import sys
import builtins
import io

ALLOWED_MODULES = {
    'math',
    'random',
    'numpy',
    'sympy',
    'matplotlib',
    'scipy',
    'sklearn',
}

ALLOWED_BUILTINS = {
    'abs', 'all', 'any', 'bool', 'callable', 'chr', 'complex', 'dict',
    'dir', 'divmod', 'enumerate', 'float', 'hash', 'hex', 'id', 'int',
    'isinstance', 'issubclass', 'iter', 'len', 'list', 'map', 'max',
    'min', 'next', 'oct', 'ord', 'pow', 'range', 'repr', 'reversed',
    'round', 'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type',
    'zip', 'print', '__import__'
}

def restricted_import(name, *args, **kwargs):
    if name not in ALLOWED_MODULES:
        raise ImportError(f"Module '{name}' is not allowed")
    return __import__(name, *args, **kwargs)

def forbidden_func(name):
    def wrapper(*args, **kwargs):
        raise RuntimeError(f"Function '{name}' is not allowed in sandbox")
    return wrapper

DANGEROUS_BUILTINS = {'open', 'eval', 'exec', 'compile'}

def execute_code(code):
    output_buffer = io.StringIO()
    
    def safe_print(*args, **kwargs):
        kwargs.setdefault('file', output_buffer)
        builtins.print(*args, **kwargs)
    
    safe_builtins_dict = {name: getattr(builtins, name) for name in ALLOWED_BUILTINS}
    safe_builtins_dict['print'] = safe_print
    safe_builtins_dict['__import__'] = restricted_import
    
    for func_name in DANGEROUS_BUILTINS:
        safe_builtins_dict[func_name] = forbidden_func(func_name)
    
    safe_globals = {
        '__builtins__': safe_builtins_dict,
        '__name__': '__sandbox__',
        '__doc__': None,
        '__package__': None,
        '__loader__': None,
        '__spec__': None,
    }
    
    try:
        exec(code, safe_globals)
        output = output_buffer.getvalue()
        return {'success': True, 'output': output, 'error': '', 'result': None}
    except Exception as e:
        output = output_buffer.getvalue()
        return {'success': False, 'output': output, 'error': str(e), 'result': None}

if __name__ == '__main__':
    if len(sys.argv) > 1:
        code_file = sys.argv[1]
        try:
            with open(code_file, 'r', encoding='utf-8') as f:
                code = f.read()
            result = execute_code(code)
            if result['output']:
                print(result['output'], end='')
            if result['error']:
                print(result['error'], file=sys.stderr)
            sys.exit(0 if result['success'] else 1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: No code file provided", file=sys.stderr)
        sys.exit(1)