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
            
            # 使用正则表达式精确匹配单个等号，排除 >=, <=, ==
            match = re.search(r'(?<![<>])=(?![<>=])', equation_str)
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
    
    def solve_intersection(self, obj1, obj2):
        """求解两个几何对象的交点"""
        try:
            x, y = symbols('x y')
            
            eq1 = self._object_to_equation(obj1, x, y)
            eq2 = self._object_to_equation(obj2, x, y)
            
            if eq1 is None or eq2 is None:
                return []
            
            solutions = solve((eq1, eq2), (x, y))
            
            points = []
            if isinstance(solutions, dict):
                if x in solutions and y in solutions:
                    try:
                        px = float(solutions[x])
                        py = float(solutions[y])
                        points.append((px, py))
                    except (TypeError, ValueError):
                        pass
            elif isinstance(solutions, list):
                for sol in solutions:
                    if isinstance(sol, dict) and x in sol and y in sol:
                        try:
                            px = float(sol[x])
                            py = float(sol[y])
                            points.append((px, py))
                        except (TypeError, ValueError):
                            pass
            
            return points
        except Exception:
            return []
    
    def _object_to_equation(self, obj, x, y):
        """将几何对象转换为 SymPy 方程"""
        obj_type = obj.type
        
        if obj_type == 'Line':
            return Eq(obj.a * x + obj.b * y + obj.c, 0)
        elif obj_type == 'Segment':
            x1, y1 = obj.coordinates.get('x1', 0), obj.coordinates.get('y1', 0)
            x2, y2 = obj.coordinates.get('x2', 0), obj.coordinates.get('y2', 0)
            a = y2 - y1
            b = x1 - x2
            c = x2 * y1 - x1 * y2
            return Eq(a * x + b * y + c, 0)
        elif obj_type == 'Circle':
            cx, cy = obj.coordinates.get('cx', 0), obj.coordinates.get('cy', 0)
            r = obj.coordinates.get('r', 1)
            return Eq((x - cx)**2 + (y - cy)**2, r**2)
        elif obj_type == 'Point':
            px, py = obj.coordinates.get('x', 0), obj.coordinates.get('y', 0)
            return Eq(x, px)
        
        return None
    
    def extract_line_control_points(self, equation_str):
        """从直线方程中提取两个控制点坐标"""
        try:
            from sympy.parsing.sympy_parser import parse_expr, standard_transformations
            
            x, y = symbols('x y')
            
            match = re.search(r'(?<![<>])=(?![<>=])', equation_str)
            if match:
                left_str = equation_str[:match.start()]
                right_str = equation_str[match.end():]
                left_expr = parse_expr(left_str.strip(), local_dict={'x': x, 'y': y}, transformations=standard_transformations)
                right_expr = parse_expr(right_str.strip(), local_dict={'x': x, 'y': y}, transformations=standard_transformations)
                eq = left_expr - right_expr
            else:
                eq = parse_expr(equation_str.strip(), local_dict={'x': x, 'y': y}, transformations=standard_transformations)
            
            eq = simplify(eq)
            
            coeffs = eq.as_coefficients_dict()
            coeff_x = float(coeffs.get(x, 0))
            coeff_y = float(coeffs.get(y, 0))
            const = float(coeffs.get(1, 0))
            
            points = []
            
            if abs(coeff_y) > 1e-10:
                x1, y1 = 0.0, -const / coeff_y
                x2, y2 = 10.0, (-const - coeff_x * 10) / coeff_y
                points.append((x1, y1))
                points.append((x2, y2))
            elif abs(coeff_x) > 1e-10:
                x1, y1 = -const / coeff_x, 0.0
                x2, y2 = (-const - coeff_y * 10) / coeff_x, 10.0
                points.append((x1, y1))
                points.append((x2, y2))
            
            return points
        except Exception:
            return []
    
    def latex_to_text(self, latex_str):
        try:
            return {"success": True, "text": latex_str}
        except:
            return {"success": False, "error": "Failed to convert"}
