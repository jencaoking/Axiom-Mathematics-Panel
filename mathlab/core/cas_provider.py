import sympy
import re
from sympy import (
    symbols, Symbol, Eq, solve, simplify, expand, factor,
    diff, integrate, limit, latex, sin, cos, tan, log, exp,
    sqrt, pi, Rational, Function, Derivative, Integral, sympify
)

class CASProvider:
    def __init__(self):
        self.symbols_cache = {}
    
    def _get_symbol(self, name):
        if name in self.symbols_cache:
            return self.symbols_cache[name]
        
        if hasattr(sympy, name):
            return getattr(sympy, name)
        
        self.symbols_cache[name] = Symbol(name)
        return self.symbols_cache[name]
    
    def parse_expression(self, expr_str):
        try:
            result = sympify(expr_str, locals=self.symbols_cache)
            for symbol in result.free_symbols:
                sym_name = str(symbol)
                if not hasattr(sympy, sym_name):
                    self.symbols_cache[sym_name] = symbol
            return result
        except Exception:
            return None
    
    def simplify(self, expr_str):
        expr = self.parse_expression(expr_str)
        if expr is None:
            return {"success": False, "error": "Invalid expression"}
        result = simplify(expr)
        return {
            "success": True,
            "latex": latex(result),
            "result": str(result)
        }
    
    def expand(self, expr_str):
        expr = self.parse_expression(expr_str)
        if expr is None:
            return {"success": False, "error": "Invalid expression"}
        result = expand(expr)
        return {
            "success": True,
            "latex": latex(result),
            "result": str(result)
        }
    
    def factor(self, expr_str):
        expr = self.parse_expression(expr_str)
        if expr is None:
            return {"success": False, "error": "Invalid expression"}
        result = factor(expr)
        return {
            "success": True,
            "latex": latex(result),
            "result": str(result)
        }
    
    def solve_equation(self, equation_str, variable='x'):
        try:
            x = self._get_symbol(variable)
            
            # 使用正则表达式精确匹配单个等号，避免误截断 >= 或 <=
            match = re.search(r'(?<!>)=(?!>)', equation_str)
            if match:
                left_str = equation_str[:match.start()]
                right_str = equation_str[match.end():]
                left_expr = sympify(left_str.strip(), locals=self.symbols_cache)
                right_expr = sympify(right_str.strip(), locals=self.symbols_cache)
                eq = Eq(left_expr, right_expr)
            else:
                left_expr = sympify(equation_str, locals=self.symbols_cache)
                eq = Eq(left_expr, 0)
            
            solutions = solve(eq, x)
            for symbol in left_expr.free_symbols:
                sym_name = str(symbol)
                if not hasattr(sympy, sym_name):
                    self.symbols_cache[sym_name] = symbol
            return {
                "success": True,
                "solutions": [latex(s) for s in solutions],
                "raw_solutions": solutions
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def differentiate(self, expr_str, variable='x'):
        x = self._get_symbol(variable)
        expr = self.parse_expression(expr_str)
        if expr is None:
            return {"success": False, "error": "Invalid expression"}
        result = diff(expr, x)
        return {
            "success": True,
            "latex": latex(result),
            "result": str(result)
        }
    
    def integrate(self, expr_str, variable='x'):
        x = self._get_symbol(variable)
        expr = self.parse_expression(expr_str)
        if expr is None:
            return {"success": False, "error": "Invalid expression"}
        result = integrate(expr, x)
        return {
            "success": True,
            "latex": latex(result),
            "result": str(result)
        }
    
    def definite_integral(self, expr_str, variable='x', lower=0, upper=1):
        x = self._get_symbol(variable)
        expr = self.parse_expression(expr_str)
        if expr is None:
            return {"success": False, "error": "Invalid expression"}
        result = integrate(expr, (x, lower, upper))
        return {
            "success": True,
            "latex": latex(result),
            "result": str(result),
            "numeric": float(result) if result.is_number else None
        }
    
    def limit(self, expr_str, variable='x', point=0):
        x = self._get_symbol(variable)
        expr = self.parse_expression(expr_str)
        if expr is None:
            return {"success": False, "error": "Invalid expression"}
        result = limit(expr, x, point)
        return {
            "success": True,
            "latex": latex(result),
            "result": str(result)
        }
    
    def evaluate(self, expr_str):
        expr = self.parse_expression(expr_str)
        if expr is None:
            return {"success": False, "error": "Invalid expression"}
        try:
            result = expr.evalf()
            return {
                "success": True,
                "latex": latex(result),
                "result": str(result),
                "numeric": float(result) if result.is_number else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_symbol(self, name):
        sym = self._get_symbol(name)
        return {"success": True, "symbol": str(sym)}
    
    def clear_symbols(self):
        self.symbols_cache.clear()
        return {"success": True}
    
    def latex_to_text(self, latex_str):
        try:
            return {"success": True, "text": latex_str}
        except:
            return {"success": False, "error": "Failed to convert"}
