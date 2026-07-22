import ast
from typing import Tuple, List


class SecurityException(Exception):
    pass


class CodeSecurityScanner(ast.NodeVisitor):
    """
    基于 AST (抽象语法树) 的代码安全扫描器
    """

    # 黑名单：严禁在沙盒中导入的系统级和网络级模块
    BANNED_MODULES = {
        "os",
        "sys",
        "subprocess",
        "shutil",
        "socket",
        "urllib",
        "requests",
        "builtins",
        "multiprocessing",
        "threading",
        "pty",
        "ctypes",
        # [安全修复] 补充缺失的危险模块
        "io",
        "pickle",
        "marshal",
        "tempfile",
        "pathlib",
        "glob",
        "inspect",
        "importlib",
        "ast",
        "code",
        "codeop",
        "ptrace",
        "resource",
        "signal",
    }

    # 黑名单：严禁调用的高危内置函数
    BANNED_FUNCTIONS = {
        "eval",
        "exec",
        "open",
        "compile",
        "globals",
        "locals",
        "__import__",
    }

    # [安全修复] 黑名单：严禁访问的危险属性（用于逃逸沙箱）
    BANNED_ATTRIBUTES = {
        "__subclasses__",
        "__mro__",
        "__bases__",
        "__class__",
        "__globals__",
        "__builtins__",
        "__code__",
        "__func__",
        "__dict__",
        "__module__",
    }

    def __init__(self) -> None:
        super().__init__()
        self.errors: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            base_module = alias.name.split(".")[0]
            if base_module in self.BANNED_MODULES:
                self.errors.append(f"安全拦截: 禁止导入模块 '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            base_module = node.module.split(".")[0]
            if base_module in self.BANNED_MODULES:
                self.errors.append(f"安全拦截: 禁止从 '{node.module}' 导入")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # 拦截诸如 eval(), exec() 等直接调用
        if isinstance(node.func, ast.Name):
            if node.func.id in self.BANNED_FUNCTIONS:
                self.errors.append(f"安全拦截: 禁止调用高危函数 '{node.func.id}()'")
            # [安全修复] 拦截 type() 内置函数，防止通过 type() 创建新类逃逸
            if node.func.id == "type":
                self.errors.append("安全拦截: 禁止调用 'type()' 函数")
        # [安全修复] 拦截通过属性访问绕过的调用，如 obj.__import__()
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name in self.BANNED_FUNCTIONS or attr_name.startswith("__"):
                self.errors.append(f"安全拦截: 禁止通过属性访问 '{attr_name}'")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """[安全修复] 拦截危险属性访问，如 __subclasses__, __mro__ 等"""
        if node.attr in self.BANNED_ATTRIBUTES:
            self.errors.append(f"安全拦截: 禁止访问危险属性 '{node.attr}'")
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
