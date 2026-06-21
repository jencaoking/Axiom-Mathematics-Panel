import sys
import builtins
import io
import json
import ast

ALLOWED_MODULES = {
    'math', 'random', 'numpy', 'sympy', 'matplotlib', 'scipy', 'sklearn',
}
DENIED_MODULES = {'importlib', 'os', 'sys', 'subprocess', 'ctypes'}
ALLOWED_BUILTINS = {
    'abs', 'all', 'any', 'bool', 'callable', 'chr', 'complex', 'dict',
    'dir', 'divmod', 'enumerate', 'float', 'hash', 'hex', 'id', 'int',
    'isinstance', 'issubclass', 'iter', 'len', 'list', 'map', 'max',
    'min', 'next', 'oct', 'ord', 'pow', 'range', 'repr', 'reversed',
    'round', 'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type',
    'zip', 'print', '__import__'
}
DANGEROUS_BUILTINS = {'open', 'eval', 'exec', 'compile'}

def restricted_import(name, *args, **kwargs):
    base = name.split('.')[0]
    if base in DENIED_MODULES:
        raise ImportError(f"Module '{name}' is strictly forbidden")
    if base not in ALLOWED_MODULES:
        raise ImportError(f"Module '{name}' is not allowed")
    return __import__(name, *args, **kwargs)

def forbidden_func(name):
    def wrapper(*args, **kwargs):
        raise RuntimeError(f"Function '{name}' is not allowed in sandbox")
    return wrapper

# Initialize safe environment
safe_builtins_dict = {name: getattr(builtins, name) for name in ALLOWED_BUILTINS}
safe_builtins_dict['__import__'] = restricted_import
for func_name in DANGEROUS_BUILTINS:
    safe_builtins_dict[func_name] = forbidden_func(func_name)

safe_globals = {
    '__builtins__': safe_builtins_dict,
    '__name__': '__main__',
}

def execute_code(code):
    output_buffer = io.StringIO()
    def safe_print(*args, **kwargs):
        kwargs.setdefault('file', output_buffer)
        builtins.print(*args, **kwargs)
    safe_globals['__builtins__']['print'] = safe_print

    try:
        # Parse AST to handle expressions automatically like a REPL
        tree = ast.parse(code, mode='exec')
        if not tree.body:
            return {'success': True, 'output': '', 'error': ''}

        last_node = tree.body[-1]
        
        if isinstance(last_node, ast.Expr):
            # If the last statement is an expression, evaluate it and print its repr
            # First, execute everything except the last node
            tree.body = tree.body[:-1]
            if tree.body:
                exec(compile(tree, '<string>', 'exec'), safe_globals)
            
            # Then evaluate the last expression
            val = eval(compile(ast.Expression(last_node.value), '<string>', 'eval'), safe_globals)
            if val is not None:
                builtins.print(repr(val), file=output_buffer)
        else:
            # Execute the whole thing
            exec(compile(tree, '<string>', 'exec'), safe_globals)
            
        output = output_buffer.getvalue()
        return {'success': True, 'output': output, 'error': ''}
    except BaseException as e:
        output = output_buffer.getvalue()
        return {'success': False, 'output': output, 'error': str(e)}

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line)
            code = req.get('code', '')
            res = execute_code(code)
            out_str = json.dumps(res) + '\n'
            sys.stdout.write(out_str)
            sys.stdout.flush()
        except BaseException as e:
            sys.stdout.write(json.dumps({'success': False, 'output': '', 'error': str(e)}) + '\n')
            sys.stdout.flush()

if __name__ == '__main__':
    main()