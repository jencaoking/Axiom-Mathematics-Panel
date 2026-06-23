import ast
from typing import Tuple, List, Set

class SecurityException(Exception):
    pass

class CodeSecurityScanner(ast.NodeVisitor):
    """
    基于 AST (抽象语法树) 的代码安全扫描器
    """
    # 黑名单：严禁在沙盒中导入的系统级和网络级模块
    BANNED_MODULES = {
        'os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib', 'requests', 
        'builtins', 'multiprocessing', 'threading', 'pty', 'ctypes'
    }
    
    # 黑名单：严禁调用的高危内置函数
    BANNED_FUNCTIONS = {'eval', 'exec', 'open', 'compile', 'globals', 'locals', '__import__'}

    def __init__(self) -> None:
        super().__init__()
        self.errors: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            base_module = alias.name.split('.')[0]
            if base_module in self.BANNED_MODULES:
                self.errors.append(f"安全拦截: 禁止导入模块 '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            base_module = node.module.split('.')[0]
            if base_module in self.BANNED_MODULES:
                self.errors.append(f"安全拦截: 禁止从 '{node.module}' 导入")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # 拦截诸如 eval(), exec() 等调用
        if isinstance(node.func, ast.Name):
            if node.func.id in self.BANNED_FUNCTIONS:
                self.errors.append(f"安全拦截: 禁止调用高危函数 '{node.func.id}()'")
        self.generic_visit(node)

def is_code_safe(code_string: str) -> Tuple[bool, str]:
    """
    验证代码是否安全
    返回: (是否安全, 错误信息)
    """
    try:
        tree = ast.parse(code_string)
    except SyntaxError as e:
        return False, f"语法错误: {e}"

    scanner = CodeSecurityScanner()
    scanner.visit(tree)

    if scanner.errors:
        return False, "\n".join(scanner.errors)
    return True, "安全"
