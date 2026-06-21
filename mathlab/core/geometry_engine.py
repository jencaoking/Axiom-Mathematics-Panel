import uuid
import warnings
import numpy as np
from collections import defaultdict
from sympy import symbols, Eq, solve, latex, sympify, parse_expr, sqrt, sin, cos, tan, pi, exp, log, Abs, Symbol, nsolve, lambdify
from sympy.parsing.sympy_parser import standard_transformations


def _build_general_quadratic_latex(A, B, C, D, E, F, threshold=1e-10):
    """将一般二次方程系数 Ax²+Bxy+Cy²+Dx+Ey+F=0 渲染为 LaTeX 字符串。

    用于圆锥曲线（椭圆、双曲线）在发生旋转后展开坐标旋转公式得到的
    通用二次形式。绝对值小于 threshold 的系数视为 0 略去。
    """
    def fmt_num(v):
        """将 |v| 格式化为可读字符串，整数省略小数部分。"""
        av = abs(v)
        if abs(av - round(av)) < threshold:
            return str(int(round(av)))
        return f'{av:.4g}'

    coeffs = [(A, 'x^2'), (B, 'xy'), (C, 'y^2'), (D, 'x'), (E, 'y'), (F, '')]
    items = []
    for c, var in coeffs:
        if abs(c) < threshold:
            continue
        coef_str = fmt_num(c)
        sign = '+' if c >= 0 else '-'
        items.append((sign, coef_str, var))

    if not items:
        return '0 = 0'

    parts = []
    for i, (sign, coef_str, var) in enumerate(items):
        # 系数为 1 时省略数字
        if var and coef_str == '1':
            content = var
        elif var:
            content = f'{coef_str}{var}'
        else:
            content = coef_str

        if i == 0:
            parts.append(content if sign == '+' else f'-{content}')
        else:
            # 不在前面加空格，由 join(' ') 统一处理分隔
            parts.append(f'{sign} {content}')

    return ' '.join(parts) + ' = 0'


class GeometricObject:
    TYPES = ['Point', 'Line', 'Segment', 'Circle', 'Polygon', 'Ray', 'Angle', 
             'Ellipse', 'Hyperbola', 'Parabola', 'ConicSection', 'FunctionPlot', 'ImplicitPlot', 'PolarPlot', 'Locus', 'Intersection']
    
    def __init__(self, obj_id, name, obj_type):
        self.id = obj_id
        self.name = name
        self.type = obj_type
        self.coordinates = {}
        self.symbolic_expr = None
        self.constraints = []
        self.depends_on = []
    
    def update_coordinates(self, engine=None):
        pass
    
    def to_latex(self):
        if self.type == 'Point':
            x, y = self.coordinates.get('x', 0), self.coordinates.get('y', 0)
            return rf'{self.name} = ({x}, {y})'
        return self.name
    
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'coordinates': self.coordinates,
            'symbolic_expr': str(self.symbolic_expr) if self.symbolic_expr else None,
            'constraints': [str(c) for c in self.constraints],
            'depends_on': self.depends_on
        }
    
    @classmethod
    def deserialize(cls, data):
        obj_type = data.get('type')
        obj = None
        
        if obj_type == 'Polygon':
            obj = Polygon.deserialize(data)
        elif obj_type == 'Ellipse':
            coords = data.get('coordinates', {})
            obj = Ellipse(data['id'], data['name'], data.get('center_id', ''), 
                         coords.get('a', 2.0), coords.get('b', 1.0), coords.get('rotation', 0))
        elif obj_type == 'Hyperbola':
            coords = data.get('coordinates', {})
            obj = Hyperbola(data['id'], data['name'], data.get('center_id', ''),
                           coords.get('a', 1.0), coords.get('b', 1.0), coords.get('rotation', 0))
        elif obj_type == 'Parabola':
            coords = data.get('coordinates', {})
            obj = Parabola(data['id'], data['name'], data.get('vertex_id', ''),
                          coords.get('p', 1.0), coords.get('direction', 'up'))
        elif obj_type == 'ConicSection':
            obj = ConicSection.deserialize(data)
        elif obj_type == 'FunctionPlot':
            obj = FunctionPlot.deserialize(data)
        elif obj_type == 'ImplicitPlot':
            obj = ImplicitPlot.deserialize(data)
        elif obj_type == 'PolarPlot':
            obj = PolarPlot.deserialize(data)
        elif obj_type == 'Locus':
            obj = Locus.deserialize(data)
        elif obj_type == 'Point':
            coords = data.get('coordinates', {})
            obj = Point(data['id'], data['name'], coords.get('x', 0), coords.get('y', 0))
        elif obj_type == 'Segment':
            obj = Segment(data['id'], data['name'], data.get('point1_id', ''), data.get('point2_id', ''))
        elif obj_type == 'Line':
            obj = Line(data['id'], data['name'], data.get('point1_id', ''), data.get('point2_id', ''))
        elif obj_type == 'Circle':
            coords = data.get('coordinates', {})
            obj = Circle(data['id'], data['name'], data.get('center_id', ''), coords.get('r', 1.0))
        elif obj_type == 'Intersection':
            obj = Intersection(data['id'], data['name'], 
                              data.get('obj1_id', ''), data.get('obj2_id', ''),
                              data.get('index', 0))
        else:
            obj = cls(data['id'], data['name'], obj_type)
        
        if obj:
            obj.coordinates = data.get('coordinates', {})
            obj.constraints = data.get('constraints', [])
            obj.depends_on = data.get('depends_on', [])
        
        return obj

class Point(GeometricObject):
    def __init__(self, obj_id, name, x=0, y=0):
        super().__init__(obj_id, name, 'Point')
        self.coordinates = {'x': x, 'y': y}
        self.symbolic_expr = (symbols(f'x_{name}'), symbols(f'y_{name}'))
    
    def update_coordinates(self, x=None, y=None):
        if x is not None:
            self.coordinates['x'] = x
        if y is not None:
            self.coordinates['y'] = y
    
    def to_latex(self):
        x, y = self.coordinates['x'], self.coordinates['y']
        return rf'{self.name} = ({latex(x)}, {latex(y)})'

class Line(GeometricObject):
    """无限长直线：通过两个点定义，支持符号表达式"""
    def __init__(self, obj_id, name, point1_id, point2_id):
        super().__init__(obj_id, name, 'Line')
        self.point1_id = point1_id
        self.point2_id = point2_id
        self.depends_on = [point1_id, point2_id]
        self.a = None  # 直线方程 ax + by + c = 0 的系数
        self.b = None
        self.c = None
    
    def update_coordinates(self, engine):
        p1 = engine.objects.get(self.point1_id)
        p2 = engine.objects.get(self.point2_id)
        if p1 and p2:
            x1, y1 = p1.coordinates['x'], p1.coordinates['y']
            x2, y2 = p2.coordinates['x'], p2.coordinates['y']
            
            self.a = y2 - y1
            self.b = x1 - x2
            self.c = x2 * y1 - x1 * y2
            
            self.coordinates = {
                'x1': x1, 'y1': y1,
                'x2': x2, 'y2': y2,
                'a': self.a, 'b': self.b, 'c': self.c
            }
    
    def to_latex(self):
        if self.a is None or self.b is None or self.c is None:
            return rf'Line({self.name})'
        
        parts = []
        if self.a != 0:
            if self.a == 1:
                parts.append('x')
            elif self.a == -1:
                parts.append('-x')
            else:
                parts.append(f'{self.a}x')
        
        if self.b != 0:
            if self.b == 1:
                sign = '+' if parts else ''
                parts.append(f'{sign}y')
            elif self.b == -1:
                parts.append('-y')
            else:
                sign = '+' if (parts and self.b > 0) else ''
                parts.append(f'{sign}{self.b}y')
        
        if self.c != 0:
            sign = '+' if (parts and self.c > 0) else ''
            parts.append(f'{sign}{self.c}')
        
        if not parts:
            return '0 = 0'
        
        return ' '.join(parts) + ' = 0'
    
    def serialize(self):
        data = super().serialize()
        data['point1_id'] = self.point1_id
        data['point2_id'] = self.point2_id
        data['a'] = self.a
        data['b'] = self.b
        data['c'] = self.c
        return data
    
    @classmethod
    def deserialize(cls, data):
        obj = cls(data['id'], data['name'], 
                  data.get('point1_id', ''), data.get('point2_id', ''))
        obj.coordinates = data.get('coordinates', {})
        obj.constraints = data.get('constraints', [])
        obj.depends_on = data.get('depends_on', [])
        obj.a = data.get('a')
        obj.b = data.get('b')
        obj.c = data.get('c')
        return obj

class Intersection(GeometricObject):
    """动态交点：实时追踪两个几何对象的相交位置"""
    def __init__(self, obj_id, name, obj1_id, obj2_id, index=0):
        super().__init__(obj_id, name, 'Intersection')
        self.obj1_id = obj1_id
        self.obj2_id = obj2_id
        self.index = index
        self.depends_on = [obj1_id, obj2_id]
    
    def update_coordinates(self, engine):
        obj1 = engine.objects.get(self.obj1_id)
        obj2 = engine.objects.get(self.obj2_id)
        
        if not obj1 or not obj2:
            return
        
        if hasattr(engine, 'cas_provider') and engine.cas_provider:
            points = engine.cas_provider.solve_intersection(obj1, obj2)
        else:
            points = self._solve_intersection(obj1, obj2)
        
        if points and len(points) > self.index:
            self.coordinates['x'] = float(points[self.index][0])
            self.coordinates['y'] = float(points[self.index][1])
    
    def _solve_intersection(self, obj1, obj2):
        """回退的几何求交算法"""
        try:
            if obj1.type in ['Segment', 'Line'] and obj2.type in ['Segment', 'Line']:
                return self._line_line_intersection(obj1, obj2)
            elif obj1.type in ['Segment', 'Line'] and obj2.type == 'Circle':
                return self._line_circle_intersection(obj1, obj2)
            elif obj2.type in ['Segment', 'Line'] and obj1.type == 'Circle':
                return self._line_circle_intersection(obj2, obj1)
            elif obj1.type == 'Circle' and obj2.type == 'Circle':
                return self._circle_circle_intersection(obj1, obj2)
        except Exception:
            pass
        return []
    
    def _line_line_intersection(self, line1, line2):
        """求解两条直线的交点"""
        if line1.type == 'Segment':
            x1, y1 = line1.coordinates.get('x1', 0), line1.coordinates.get('y1', 0)
            x2, y2 = line1.coordinates.get('x2', 0), line1.coordinates.get('y2', 0)
            a1, b1, c1 = y2 - y1, x1 - x2, x2 * y1 - x1 * y2
        else:
            a1, b1, c1 = line1.a, line1.b, line1.c
        
        if line2.type == 'Segment':
            x1, y1 = line2.coordinates.get('x1', 0), line2.coordinates.get('y1', 0)
            x2, y2 = line2.coordinates.get('x2', 0), line2.coordinates.get('y2', 0)
            a2, b2, c2 = y2 - y1, x1 - x2, x2 * y1 - x1 * y2
        else:
            a2, b2, c2 = line2.a, line2.b, line2.c
        
        det = a1 * b2 - a2 * b1
        if abs(det) < 1e-10:
            return []
        
        x = (b1 * c2 - b2 * c1) / det
        y = (a2 * c1 - a1 * c2) / det
        return [(x, y)]
    
    def _line_circle_intersection(self, line, circle):
        """求解直线与圆的交点（垂足+切向量法）"""
        if line.type == 'Segment':
            x1, y1 = line.coordinates.get('x1', 0), line.coordinates.get('y1', 0)
            x2, y2 = line.coordinates.get('x2', 0), line.coordinates.get('y2', 0)
            a, b, c = y2 - y1, x1 - x2, x2 * y1 - x1 * y2
        else:
            a, b, c = line.a, line.b, line.c

        cx, cy = circle.coordinates.get('cx', 0), circle.coordinates.get('cy', 0)
        r = circle.coordinates.get('r', 1)
        n2 = a**2 + b**2
        if n2 < 1e-10:
            return []

        # 圆心到直线的有符号距离分子 k = a*cx + b*cy + c
        k = a * cx + b * cy + c
        n = np.sqrt(n2)
        d = abs(k) / n  # 圆心到直线的距离

        if d > r + 1e-10:
            return []

        # 垂足坐标
        fx = cx - a * k / n2
        fy = cy - b * k / n2

        if abs(d - r) < 1e-10:
            # 相切：唯一交点即为垂足
            return [(fx, fy)]

        # 半弦长，沿直线切向量 (-b, a)/n 偏移
        h = np.sqrt(max(r**2 - d**2, 0.0))
        x1_r, y1_r = fx - h * b / n, fy + h * a / n
        x2_r, y2_r = fx + h * b / n, fy - h * a / n
        return [(x1_r, y1_r), (x2_r, y2_r)]
    
    def _circle_circle_intersection(self, circle1, circle2):
        """求解两个圆的交点"""
        cx1, cy1 = circle1.coordinates.get('cx', 0), circle1.coordinates.get('cy', 0)
        r1 = circle1.coordinates.get('r', 1)
        cx2, cy2 = circle2.coordinates.get('cx', 0), circle2.coordinates.get('cy', 0)
        r2 = circle2.coordinates.get('r', 1)
        
        dx = cx2 - cx1
        dy = cy2 - cy1
        d = np.sqrt(dx**2 + dy**2)
        
        if d > r1 + r2 or d < abs(r1 - r2):
            return []
        
        if abs(d) < 1e-10 and abs(r1 - r2) < 1e-10:
            return []
        
        a = (r1**2 - r2**2 + d**2) / (2 * d)
        h = np.sqrt(r1**2 - a**2)
        
        xm = cx1 + a * dx / d
        ym = cy1 + a * dy / d
        
        x1 = xm - h * dy / d
        y1 = ym + h * dx / d
        x2 = xm + h * dy / d
        y2 = ym - h * dx / d
        
        if abs(h) < 1e-10:
            return [(x1, y1)]
        return [(x1, y1), (x2, y2)]
    
    def to_latex(self):
        x, y = self.coordinates.get('x', 0), self.coordinates.get('y', 0)
        return rf'{self.name} = ({latex(x)}, {latex(y)})'

class Segment(GeometricObject):
    def __init__(self, obj_id, name, point1_id, point2_id):
        super().__init__(obj_id, name, 'Segment')
        self.depends_on = [point1_id, point2_id]
        self.point1_id = point1_id
        self.point2_id = point2_id
    
    def update_coordinates(self, engine):
        p1 = engine.objects.get(self.point1_id)
        p2 = engine.objects.get(self.point2_id)
        if p1 and p2:
            self.coordinates = {
                'x1': p1.coordinates['x'],
                'y1': p1.coordinates['y'],
                'x2': p2.coordinates['x'],
                'y2': p2.coordinates['y']
            }
    
    def to_latex(self):
        return rf'\overline{{{self.name}}}'
    
    def serialize(self):
        data = super().serialize()
        data['point1_id'] = self.point1_id
        data['point2_id'] = self.point2_id
        return data

class Circle(GeometricObject):
    def __init__(self, obj_id, name, center_id, radius=1.0):
        super().__init__(obj_id, name, 'Circle')
        self.center_id = center_id
        self.radius = radius
        self.depends_on = [center_id]
    
    def update_coordinates(self, engine):
        center = engine.objects.get(self.center_id)
        if center:
            self.coordinates = {
                'cx': center.coordinates['x'],
                'cy': center.coordinates['y'],
                'r': self.radius
            }
    
    def to_latex(self):
        return rf'Circle({self.name})'
    
    def serialize(self):
        data = super().serialize()
        data['center_id'] = self.center_id
        data['radius'] = self.radius
        return data

class Polygon(GeometricObject):
    def __init__(self, obj_id, name, point_ids):
        super().__init__(obj_id, name, 'Polygon')
        self.point_ids = point_ids
        self.depends_on = point_ids.copy()
        self.points = []
    
    def update_coordinates(self, engine):
        self.points = []
        for point_id in self.point_ids:
            point = engine.objects.get(point_id)
            if point:
                self.points.append((point.coordinates['x'], point.coordinates['y']))
        self.coordinates = {'points': self.points}
    
    def to_latex(self):
        return rf'Polygon({self.name})'
    
    def serialize(self):
        data = super().serialize()
        data['point_ids'] = self.point_ids
        data['points'] = self.points
        return data
    
    @classmethod
    def deserialize(cls, data):
        obj = cls(data['id'], data['name'], data.get('point_ids', []))
        obj.coordinates = data['coordinates']
        obj.constraints = data.get('constraints', [])
        obj.depends_on = data.get('depends_on', [])
        obj.points = data.get('points', [])
        return obj

class Ellipse(GeometricObject):
    """椭圆：支持中心点、长轴、短轴定义"""
    def __init__(self, obj_id, name, center_id, a=2.0, b=1.0, rotation=0):
        super().__init__(obj_id, name, 'Ellipse')
        self.center_id = center_id
        self.a = a  # 半长轴
        self.b = b  # 半短轴
        self.rotation = rotation  # 旋转角度（弧度）
        self.depends_on = [center_id]
    
    def update_coordinates(self, engine):
        center = engine.objects.get(self.center_id)
        if center:
            self.coordinates = {
                'cx': center.coordinates['x'],
                'cy': center.coordinates['y'],
                'a': self.a,
                'b': self.b,
                'rotation': self.rotation
            }
    
    def to_latex(self):
        cx = self.coordinates.get('cx', 0)
        cy = self.coordinates.get('cy', 0)
        if self.rotation == 0:
            return rf'\frac{{(x-{cx})^2}}{{{self.a}^2}} + \frac{{(y-{cy})^2}}{{{self.b}^2}} = 1'
        # 旋转 θ 后，将标准方程展开为一般二次方程 Ax²+Bxy+Cy²+Dx+Ey+F=0
        # 推导：令 u=x-cx, v=y-cy，则 x'=u·cosθ+v·sinθ, y'=-u·sinθ+v·cosθ
        cos_t = np.cos(self.rotation)
        sin_t = np.sin(self.rotation)
        a2 = self.a ** 2
        b2 = self.b ** 2
        A = cos_t ** 2 / a2 + sin_t ** 2 / b2
        B = 2 * sin_t * cos_t * (1 / a2 - 1 / b2)
        C = sin_t ** 2 / a2 + cos_t ** 2 / b2
        D = -2 * A * cx - B * cy
        E = -B * cx - 2 * C * cy
        F = A * cx ** 2 + B * cx * cy + C * cy ** 2 - 1
        return _build_general_quadratic_latex(A, B, C, D, E, F)
    
    def serialize(self):
        data = super().serialize()
        data['center_id'] = self.center_id
        data['a'] = self.a
        data['b'] = self.b
        data['rotation'] = self.rotation
        return data

class Hyperbola(GeometricObject):
    """双曲线：支持中心点、实轴、虚轴定义"""
    def __init__(self, obj_id, name, center_id, a=1.0, b=1.0, rotation=0):
        super().__init__(obj_id, name, 'Hyperbola')
        self.center_id = center_id
        self.a = a  # 实半轴
        self.b = b  # 虚半轴
        self.rotation = rotation  # 旋转角度（弧度）
        self.depends_on = [center_id]
    
    def update_coordinates(self, engine):
        center = engine.objects.get(self.center_id)
        if center:
            self.coordinates = {
                'cx': center.coordinates['x'],
                'cy': center.coordinates['y'],
                'a': self.a,
                'b': self.b,
                'rotation': self.rotation
            }
    
    def to_latex(self):
        cx = self.coordinates.get('cx', 0)
        cy = self.coordinates.get('cy', 0)
        if self.rotation == 0:
            return rf'\frac{{(x-{cx})^2}}{{{self.a}^2}} - \frac{{(y-{cy})^2}}{{{self.b}^2}} = 1'
        # 旋转 θ 后展开为一般二次方程。注意双曲线 a²/b² 前的符号相反。
        cos_t = np.cos(self.rotation)
        sin_t = np.sin(self.rotation)
        a2 = self.a ** 2
        b2 = self.b ** 2
        A = cos_t ** 2 / a2 - sin_t ** 2 / b2
        B = 2 * sin_t * cos_t * (1 / a2 + 1 / b2)
        C = sin_t ** 2 / a2 - cos_t ** 2 / b2
        D = -2 * A * cx - B * cy
        E = -B * cx - 2 * C * cy
        F = A * cx ** 2 + B * cx * cy + C * cy ** 2 - 1
        return _build_general_quadratic_latex(A, B, C, D, E, F)
    
    def serialize(self):
        data = super().serialize()
        data['center_id'] = self.center_id
        data['a'] = self.a
        data['b'] = self.b
        data['rotation'] = self.rotation
        return data

class Parabola(GeometricObject):
    """抛物线：支持顶点、焦点或标准方程定义"""
    def __init__(self, obj_id, name, vertex_id, p=1.0, direction='up'):
        super().__init__(obj_id, name, 'Parabola')
        self.vertex_id = vertex_id
        self.p = p  # 焦距参数
        self.direction = direction  # 'up', 'down', 'left', 'right'
        self.depends_on = [vertex_id]
    
    def update_coordinates(self, engine):
        vertex = engine.objects.get(self.vertex_id)
        if vertex:
            self.coordinates = {
                'vx': vertex.coordinates['x'],
                'vy': vertex.coordinates['y'],
                'p': self.p,
                'direction': self.direction
            }
    
    def to_latex(self):
        vx = self.coordinates.get('vx', 0)
        vy = self.coordinates.get('vy', 0)
        if self.direction in ['up', 'down']:
            sign = 1 if self.direction == 'up' else -1
            return rf'(x-{vx})^2 = {4*self.p*sign}(y-{vy})'
        else:
            sign = 1 if self.direction == 'right' else -1
            return rf'(y-{vy})^2 = {4*self.p*sign}(x-{vx})'
    
    def serialize(self):
        data = super().serialize()
        data['vertex_id'] = self.vertex_id
        data['p'] = self.p
        data['direction'] = self.direction
        return data

class ConicSection(GeometricObject):
    """一般圆锥曲线：通过一般方程 Ax²+Bxy+Cy²+Dx+Ey+F=0 定义"""
    def __init__(self, obj_id, name, A=1, B=0, C=1, D=0, E=0, F=-1, x_range=(-10, 10), y_range=(-10, 10)):
        super().__init__(obj_id, name, 'ConicSection')
        self.A = A
        self.B = B
        self.C = C
        self.D = D
        self.E = E
        self.F = F
        self.x_range = x_range
        self.y_range = y_range
        self.equation_str = f'{A}*x**2 + {B}*x*y + {C}*y**2 + {D}*x + {E}*y + {F}'
        self.points_data = []  # 存储离散点用于绘制
    
    def generate_points(self, num_points=500):
        """通过隐函数求解生成离散点"""
        try:
            x_sym, y_sym = symbols('x y')
            eq = self.A * x_sym**2 + self.B * x_sym * y_sym + self.C * y_sym**2 + self.D * x_sym + self.E * y_sym + self.F
            
            points = []
            x_vals = np.linspace(self.x_range[0], self.x_range[1], num_points)
            
            for x_val in x_vals:
                # 对于每个 x，解关于 y 的二次方程
                a_coeff = float(self.C)
                b_coeff = float(self.B * x_val + self.E)
                c_coeff = float(self.A * x_val**2 + self.D * x_val + self.F)
                
                if abs(a_coeff) < 1e-10:
                    # 退化为线性方程
                    if abs(b_coeff) > 1e-10:
                        y_val = -c_coeff / b_coeff
                        if self.y_range[0] <= y_val <= self.y_range[1]:
                            points.append((float(x_val), float(y_val)))
                else:
                    discriminant = b_coeff**2 - 4*a_coeff*c_coeff
                    if discriminant >= 0:
                        sqrt_disc = np.sqrt(discriminant)
                        y1 = (-b_coeff + sqrt_disc) / (2*a_coeff)
                        y2 = (-b_coeff - sqrt_disc) / (2*a_coeff)
                        
                        if self.y_range[0] <= y1 <= self.y_range[1]:
                            points.append((float(x_val), float(y1)))
                        if self.y_range[0] <= y2 <= self.y_range[1] and abs(y2 - y1) > 1e-6:
                            points.append((float(x_val), float(y2)))
            
            self.points_data = points
            self.coordinates = {'points': points}
            return points
        except Exception as e:
            print(f'Error generating conic section points: {e}')
            return []
    
    def to_latex(self):
        terms = []
        if self.A != 0:
            terms.append(f'{self.A}x^2')
        if self.B != 0:
            terms.append(f'{self.B}xy')
        if self.C != 0:
            terms.append(f'{self.C}y^2')
        if self.D != 0:
            terms.append(f'{self.D}x')
        if self.E != 0:
            terms.append(f'{self.E}y')
        if self.F != 0:
            terms.append(f'{self.F}')
        return ' + '.join(terms) + ' = 0' if terms else '0 = 0'
    
    def serialize(self):
        data = super().serialize()
        data['A'] = self.A
        data['B'] = self.B
        data['C'] = self.C
        data['D'] = self.D
        data['E'] = self.E
        data['F'] = self.F
        data['x_range'] = self.x_range
        data['y_range'] = self.y_range
        data['equation_str'] = self.equation_str
        data['points_data'] = self.points_data
        return data
    
    @classmethod
    def deserialize(cls, data):
        obj = cls(
            data['id'], data['name'],
            data.get('A', 1), data.get('B', 0), data.get('C', 1),
            data.get('D', 0), data.get('E', 0), data.get('F', -1),
            data.get('x_range', (-10, 10)), data.get('y_range', (-10, 10))
        )
        obj.coordinates = data.get('coordinates', {})
        obj.constraints = data.get('constraints', [])
        obj.depends_on = data.get('depends_on', [])
        obj.points_data = data.get('points_data', [])
        obj.equation_str = data.get('equation_str', '')
        return obj

class FunctionPlot(GeometricObject):
    """显函数绘图：y = f(x)"""
    def __init__(self, obj_id, name, expression, x_range=(-10, 10), num_points=500):
        super().__init__(obj_id, name, 'FunctionPlot')
        self.expression = expression
        self.x_range = x_range
        self.num_points = num_points
        self.points_data = []
        self._generate_points()
    
    def _generate_points(self):
        """生成离散点用于绘制（使用 lambdify 矢量化加速）"""
        try:
            x_sym = symbols('x')
            expr = parse_expr(self.expression, local_dict={'x': x_sym})
            
            x_vals = np.linspace(self.x_range[0], self.x_range[1], self.num_points)
            
            try:
                # 矢量化：将 SymPy 表达式转为 NumPy 函数
                func = lambdify(x_sym, expr, "numpy")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    y_vals = func(x_vals)
            except Exception:
                self.points_data = []
                self.coordinates = {'points': []}
                return
            
            # 过滤掉 NaN/Inf
            mask = np.isfinite(y_vals)
            points = list(zip(x_vals[mask].tolist(), y_vals[mask].astype(float).tolist()))
            
            self.points_data = points
            self.coordinates = {'points': points}
        except Exception as e:
            print(f'Error generating function plot points: {e}')
            self.points_data = []
    
    def to_latex(self):
        return rf'y = {self.expression}'
    
    def serialize(self):
        data = super().serialize()
        data['expression'] = self.expression
        data['x_range'] = self.x_range
        data['num_points'] = self.num_points
        data['points_data'] = self.points_data
        return data
    
    @classmethod
    def deserialize(cls, data):
        obj = cls(data['id'], data['name'], data.get('expression', 'x'), 
                  data.get('x_range', (-10, 10)), data.get('num_points', 500))
        obj.coordinates = data.get('coordinates', {})
        obj.constraints = data.get('constraints', [])
        obj.depends_on = data.get('depends_on', [])
        obj.points_data = data.get('points_data', [])
        return obj

class ImplicitPlot(GeometricObject):
    """隐函数绘图：f(x,y) = 0"""
    def __init__(self, obj_id, name, expression, x_range=(-10, 10), y_range=(-10, 10), resolution=400):
        super().__init__(obj_id, name, 'ImplicitPlot')
        self.expression = expression
        self.x_range = x_range
        self.y_range = y_range
        self.resolution = resolution
        self.points_data = []
        self._generate_points()
    
    def _generate_points(self):
        """使用网格采样和等值线提取生成点（使用 lambdify 矢量化加速）"""
        try:
            x_sym, y_sym = symbols('x y')
            expr = parse_expr(self.expression, local_dict={'x': x_sym, 'y': y_sym})
            
            # 创建网格
            x_vals = np.linspace(self.x_range[0], self.x_range[1], self.resolution)
            y_vals = np.linspace(self.y_range[0], self.y_range[1], self.resolution)
            X, Y = np.meshgrid(x_vals, y_vals)
            
            # 矢量化计算函数值（一次 C 级别运算替代 160000 次 subs）
            try:
                func = lambdify((x_sym, y_sym), expr, "numpy")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    Z = func(X, Y)
            except Exception:
                Z = np.full_like(X, np.nan)
            
            # 使用简单的等值线提取（Marching Squares 简化版）
            points = []
            threshold = 0.0
            for i in range(self.resolution - 1):
                for j in range(self.resolution - 1):
                    # 检查四个角点
                    vals = [Z[i,j], Z[i,j+1], Z[i+1,j+1], Z[i+1,j]]
                    
                    # 如果存在符号变化，说明有等值线穿过
                    if any(v * threshold <= 0 for v in vals if not np.isnan(v)):
                        # 简单插值找到近似点
                        for di in [0, 1]:
                            for dj in [0, 1]:
                                if not np.isnan(Z[i+di, j+dj]) and abs(Z[i+di, j+dj]) < 0.1:
                                    points.append((float(X[i+di, j+dj]), float(Y[i+di, j+dj])))
            
            self.points_data = points
            self.coordinates = {'points': points}
        except Exception as e:
            print(f'Error generating implicit plot points: {e}')
            self.points_data = []
    
    def to_latex(self):
        return rf'{self.expression} = 0'
    
    def serialize(self):
        data = super().serialize()
        data['expression'] = self.expression
        data['x_range'] = self.x_range
        data['y_range'] = self.y_range
        data['resolution'] = self.resolution
        data['points_data'] = self.points_data
        return data
    
    @classmethod
    def deserialize(cls, data):
        obj = cls(data['id'], data['name'], data.get('expression', 'x**2 + y**2 - 1'),
                  data.get('x_range', (-10, 10)), data.get('y_range', (-10, 10)),
                  data.get('resolution', 400))
        obj.coordinates = data.get('coordinates', {})
        obj.constraints = data.get('constraints', [])
        obj.depends_on = data.get('depends_on', [])
        obj.points_data = data.get('points_data', [])
        return obj

class PolarPlot(GeometricObject):
    """极坐标绘图：r = f(θ)"""
    def __init__(self, obj_id, name, expression, theta_range=(0, 2*np.pi), num_points=500):
        super().__init__(obj_id, name, 'PolarPlot')
        self.expression = expression
        self.theta_range = theta_range
        self.num_points = num_points
        self.points_data = []
        self._generate_points()
    
    def _generate_points(self):
        """将极坐标转换为直角坐标并生成点（使用 lambdify 矢量化加速）"""
        try:
            theta_sym = symbols('theta')
            expr = parse_expr(self.expression, local_dict={'theta': theta_sym})
            
            theta_vals = np.linspace(self.theta_range[0], self.theta_range[1], self.num_points)
            
            try:
                # 矢量化计算 r 值
                func = lambdify(theta_sym, expr, "numpy")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    r_vals = func(theta_vals)
            except Exception:
                self.points_data = []
                self.coordinates = {'points': []}
                return
            
            # 过滤 NaN/Inf 后一次性转换为直角坐标
            mask = np.isfinite(r_vals)
            r_valid = r_vals[mask]
            t_valid = theta_vals[mask]
            x = r_valid * np.cos(t_valid)
            y = r_valid * np.sin(t_valid)
            points = list(zip(x.astype(float).tolist(), y.astype(float).tolist()))
            
            self.points_data = points
            self.coordinates = {'points': points}
        except Exception as e:
            print(f'Error generating polar plot points: {e}')
            self.points_data = []
    
    def to_latex(self):
        return rf'r = {self.expression}'
    
    def serialize(self):
        data = super().serialize()
        data['expression'] = self.expression
        data['theta_range'] = self.theta_range
        data['num_points'] = self.num_points
        data['points_data'] = self.points_data
        return data
    
    @classmethod
    def deserialize(cls, data):
        import math
        obj = cls(data['id'], data['name'], data.get('expression', 'theta'),
                  tuple(data.get('theta_range', [0, 2*math.pi])), data.get('num_points', 500))
        obj.coordinates = data.get('coordinates', {})
        obj.constraints = data.get('constraints', [])
        obj.depends_on = data.get('depends_on', [])
        obj.points_data = data.get('points_data', [])
        return obj

class Locus(GeometricObject):
    """动点轨迹：追踪依赖点的运动轨迹"""
    def __init__(self, obj_id, name, tracer_point_id, driver_point_id, max_points=1000):
        super().__init__(obj_id, name, 'Locus')
        self.tracer_point_id = tracer_point_id  # 被追踪的点
        self.driver_point_id = driver_point_id  # 驱动运动的点
        self.max_points = max_points
        self.trail_points = []  # 轨迹点历史
        self.points_data = []
        self.depends_on = [tracer_point_id, driver_point_id]
    
    def add_trail_point(self, x, y):
        """添加一个轨迹点"""
        self.trail_points.append((x, y))
        if len(self.trail_points) > self.max_points:
            self.trail_points.pop(0)
        self.points_data = self.trail_points.copy()
        self.coordinates = {'points': self.points_data}
    
    def clear_trail(self):
        """清除轨迹"""
        self.trail_points.clear()
        self.points_data.clear()
        self.coordinates = {'points': []}
    
    def to_latex(self):
        return rf'Locus of {self.name}'
    
    def serialize(self):
        data = super().serialize()
        data['tracer_point_id'] = self.tracer_point_id
        data['driver_point_id'] = self.driver_point_id
        data['max_points'] = self.max_points
        data['trail_points'] = self.trail_points
        data['points_data'] = self.points_data
        return data
    
    @classmethod
    def deserialize(cls, data):
        obj = cls(data['id'], data['name'], 
                  data.get('tracer_point_id', ''), data.get('driver_point_id', ''),
                  data.get('max_points', 1000))
        obj.coordinates = data.get('coordinates', {})
        obj.constraints = data.get('constraints', [])
        obj.depends_on = data.get('depends_on', [])
        obj.trail_points = data.get('trail_points', [])
        obj.points_data = data.get('points_data', [])
        return obj

class DAG:
    def __init__(self):
        self.graph = defaultdict(list)
        self.reverse_graph = defaultdict(list)
    
    def add_edge(self, from_node, to_node):
        if to_node not in self.graph[from_node]:
            self.graph[from_node].append(to_node)
        if from_node not in self.reverse_graph[to_node]:
            self.reverse_graph[to_node].append(from_node)
    
    def remove_node(self, node):
        for child in self.graph.get(node, []):
            if node in self.reverse_graph.get(child, []):
                self.reverse_graph[child].remove(node)
        
        for parent in self.reverse_graph.get(node, []):
            if node in self.graph.get(parent, []):
                self.graph[parent].remove(node)
                
        self.graph.pop(node, None)
        self.reverse_graph.pop(node, None)
    
    def get_dependencies(self, node):
        visited = set()
        result = []
        def dfs(n):
            if n in visited:
                return
            visited.add(n)
            for dep in self.reverse_graph[n]:
                dfs(dep)
                result.append(dep)
        dfs(node)
        return result
    
    def get_dependents(self, node):
        """返回所有依赖节点，按拓扑顺序排列（父节点在子节点之前）。

        使用后序遍历的逆序实现严格拓扑排序，确保任意节点都先于
        其下游节点被返回，从而 update_point 中可以安全地按顺序
        更新依赖图，不会出现读取到脏数据的情况。
        """
        visited = set()
        result = []

        def dfs(n):
            if n in visited:
                return
            visited.add(n)
            for dep in self.graph.get(n, []):
                dfs(dep)  # 先深入到底
            result.append(n)  # 后序收集

        dfs(node)
        # 逆序得到正确的拓扑顺序
        result.reverse()
        # 移除起始节点自身，调用方只需要依赖项
        return [x for x in result if x != node]

class GeometryEngine:
    def __init__(self):
        self.objects = {}
        self.name_counter = defaultdict(int)
        self.dependencies = DAG()
        self.listeners = []
        self._signals_blocked = False
        self.cas_provider = None
    
    def set_cas_provider(self, cas_provider):
        self.cas_provider = cas_provider
    
    def block_signals(self, blocked):
        self._signals_blocked = blocked
    
    def signals_blocked(self):
        return self._signals_blocked
    
    def _generate_id(self):
        return str(uuid.uuid4())
    
    def _generate_name(self, obj_type):
        prefix = obj_type[0].upper()
        # 基于当前该类型对象的数量生成名称，防止重名
        count = len([obj for obj in self.objects.values() if obj.type == obj_type]) + 1
        # 确保生成的名称在当前环境中是唯一的
        while True:
            name = f'{prefix}{count}'
            if not any(obj.name == name for obj in self.objects.values()):
                return name
            count += 1
    
    def add_listener(self, listener):
        self.listeners.append(listener)
    
    def _notify(self, event_type, data):
        if self._signals_blocked:
            return
        for listener in self.listeners:
            listener(event_type, data)
    
    def add_point(self, x=0, y=0, name=None):
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Point')
        point = Point(obj_id, name, x, y)
        self.objects[obj_id] = point
        self._notify('object_added', point.serialize())
        return obj_id
    
    def add_segment(self, point1_id, point2_id, name=None):
        if point1_id not in self.objects or point2_id not in self.objects:
            raise ValueError('Points not found')
        
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Segment')
        segment = Segment(obj_id, name, point1_id, point2_id)
        self.objects[obj_id] = segment
        self.dependencies.add_edge(point1_id, obj_id)
        self.dependencies.add_edge(point2_id, obj_id)
        segment.update_coordinates(self)
        self._notify('object_added', segment.serialize())
        return obj_id
    
    def add_line(self, point1_id, point2_id, name=None):
        if point1_id not in self.objects or point2_id not in self.objects:
            raise ValueError('Points not found')
        
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Line')
        line = Line(obj_id, name, point1_id, point2_id)
        self.objects[obj_id] = line
        self.dependencies.add_edge(point1_id, obj_id)
        self.dependencies.add_edge(point2_id, obj_id)
        line.update_coordinates(self)
        self._notify('object_added', line.serialize())
        return obj_id
    
    def add_intersection(self, obj1_id, obj2_id, index=0, name=None):
        if obj1_id not in self.objects or obj2_id not in self.objects:
            raise ValueError('Objects not found')
        
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Intersection')
        intersection = Intersection(obj_id, name, obj1_id, obj2_id, index)
        self.objects[obj_id] = intersection
        self.dependencies.add_edge(obj1_id, obj_id)
        self.dependencies.add_edge(obj2_id, obj_id)
        intersection.update_coordinates(self)
        self._notify('object_added', intersection.serialize())
        return obj_id
    
    def add_circle(self, center_id, radius=1.0, name=None):
        if center_id not in self.objects:
            raise ValueError('Center point not found')
        
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Circle')
        circle = Circle(obj_id, name, center_id, radius)
        self.objects[obj_id] = circle
        self.dependencies.add_edge(center_id, obj_id)
        circle.update_coordinates(self)
        self._notify('object_added', circle.serialize())
        return obj_id
    
    def add_polygon(self, point_ids, name=None):
        for point_id in point_ids:
            if point_id not in self.objects:
                raise ValueError(f'Point {point_id} not found')
        
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Polygon')
        polygon = Polygon(obj_id, name, point_ids)
        self.objects[obj_id] = polygon
        for point_id in point_ids:
            self.dependencies.add_edge(point_id, obj_id)
        polygon.update_coordinates(self)
        self._notify('object_added', polygon.serialize())
        return obj_id
    
    def add_ellipse(self, center_id, a=2.0, b=1.0, rotation=0, name=None):
        """添加椭圆"""
        if center_id not in self.objects:
            raise ValueError('Center point not found')
        
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Ellipse')
        ellipse = Ellipse(obj_id, name, center_id, a, b, rotation)
        self.objects[obj_id] = ellipse
        self.dependencies.add_edge(center_id, obj_id)
        ellipse.update_coordinates(self)
        self._notify('object_added', ellipse.serialize())
        return obj_id
    
    def add_hyperbola(self, center_id, a=1.0, b=1.0, rotation=0, name=None):
        """添加双曲线"""
        if center_id not in self.objects:
            raise ValueError('Center point not found')
        
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Hyperbola')
        hyperbola = Hyperbola(obj_id, name, center_id, a, b, rotation)
        self.objects[obj_id] = hyperbola
        self.dependencies.add_edge(center_id, obj_id)
        hyperbola.update_coordinates(self)
        self._notify('object_added', hyperbola.serialize())
        return obj_id
    
    def add_parabola(self, vertex_id, p=1.0, direction='up', name=None):
        """添加抛物线"""
        if vertex_id not in self.objects:
            raise ValueError('Vertex point not found')
        
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Parabola')
        parabola = Parabola(obj_id, name, vertex_id, p, direction)
        self.objects[obj_id] = parabola
        self.dependencies.add_edge(vertex_id, obj_id)
        parabola.update_coordinates(self)
        self._notify('object_added', parabola.serialize())
        return obj_id
    
    def add_conic_section(self, A=1, B=0, C=1, D=0, E=0, F=-1, x_range=(-10, 10), y_range=(-10, 10), name=None):
        """添加一般圆锥曲线"""
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('ConicSection')
        conic = ConicSection(obj_id, name, A, B, C, D, E, F, x_range, y_range)
        conic.generate_points()  # 生成离散点
        self.objects[obj_id] = conic
        self._notify('object_added', conic.serialize())
        return obj_id
    
    def add_function_plot(self, expression, x_range=(-10, 10), num_points=500, name=None):
        """添加显函数绘图 y=f(x)"""
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('FunctionPlot')
        func_plot = FunctionPlot(obj_id, name, expression, x_range, num_points)
        self.objects[obj_id] = func_plot
        self._notify('object_added', func_plot.serialize())
        return obj_id
    
    def add_implicit_plot(self, expression, x_range=(-10, 10), y_range=(-10, 10), resolution=400, name=None):
        """添加隐函数绘图 f(x,y)=0"""
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('ImplicitPlot')
        impl_plot = ImplicitPlot(obj_id, name, expression, x_range, y_range, resolution)
        self.objects[obj_id] = impl_plot
        self._notify('object_added', impl_plot.serialize())
        return obj_id
    
    def add_polar_plot(self, expression, theta_range=(0, 2*np.pi), num_points=500, name=None):
        """添加极坐标绘图 r=f(θ)"""
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('PolarPlot')
        polar_plot = PolarPlot(obj_id, name, expression, theta_range, num_points)
        self.objects[obj_id] = polar_plot
        self._notify('object_added', polar_plot.serialize())
        return obj_id
    
    def add_locus(self, tracer_point_id, driver_point_id, max_points=1000, name=None):
        """添加动点轨迹追踪器"""
        if tracer_point_id not in self.objects or driver_point_id not in self.objects:
            raise ValueError('Tracer or driver point not found')
        
        obj_id = self._generate_id()
        if name is None:
            name = self._generate_name('Locus')
        locus = Locus(obj_id, name, tracer_point_id, driver_point_id, max_points)
        self.objects[obj_id] = locus
        self.dependencies.add_edge(tracer_point_id, obj_id)
        self.dependencies.add_edge(driver_point_id, obj_id)
        self._notify('object_added', locus.serialize())
        return obj_id
    
    def update_locus(self, locus_id):
        """更新轨迹：添加当前追踪点位置"""
        if locus_id not in self.objects:
            return
        
        locus = self.objects[locus_id]
        if locus.type != 'Locus':
            return
        
        tracer = self.objects.get(locus.tracer_point_id)
        if tracer:
            locus.add_trail_point(tracer.coordinates['x'], tracer.coordinates['y'])
            self._notify('object_updated', locus.serialize())
    
    def remove_object(self, obj_id):
        if obj_id not in self.objects:
            return
        
        dependents = self.dependencies.get_dependents(obj_id)
        for dep_id in dependents:
            if dep_id in self.objects:
                self.dependencies.remove_node(dep_id)
                self._notify('object_removed', dep_id)
                del self.objects[dep_id]
        
        obj = self.objects[obj_id]
        
        self.dependencies.remove_node(obj_id)
        self._notify('object_removed', obj_id)
        del self.objects[obj_id]
    
    def update_point(self, obj_id, x=None, y=None):
        if obj_id not in self.objects:
            return
        
        point = self.objects[obj_id]
        if x is not None:
            point.coordinates['x'] = x
        if y is not None:
            point.coordinates['y'] = y
        
        dependents = self.dependencies.get_dependents(obj_id)
        for dep_id in dependents:
            dep_obj = self.objects[dep_id]
            dep_obj.update_coordinates(self)
            self._notify('object_updated', dep_obj.serialize())
        
        self._notify('object_updated', point.serialize())
    
    def get_object(self, obj_id):
        return self.objects.get(obj_id)
    
    def get_all_objects(self):
        return list(self.objects.values())
    
    def get_objects_by_type(self, obj_type):
        return [obj for obj in self.objects.values() if obj.type == obj_type]
    
    def solve_constraints(self):
        from scipy.optimize import least_squares
        import numpy as np
        
        variables = []
        var_to_idx = {}
        equations = []
        
        points = self.get_objects_by_type('Point')
        
        for point in points:
            safe_id = point.id.replace('-', '_')
            x_sym = symbols(f'x_{safe_id}')
            y_sym = symbols(f'y_{safe_id}')
            var_to_idx[(point.id, 'x')] = len(variables)
            var_to_idx[(point.id, 'y')] = len(variables) + 1
            variables.extend([x_sym, y_sym])
        
        for obj in self.objects.values():
            for constraint in obj.constraints:
                if isinstance(constraint, str):
                    try:
                        allowed_symbols = {
                            'Eq': Eq,
                            'sqrt': sqrt,
                            'sin': sin,
                            'cos': cos,
                            'tan': tan,
                            'pi': pi,
                            'exp': exp,
                            'log': log,
                            'Abs': Abs,
                            'pow': pow
                        }
                        for point in points:
                            safe_id = point.id.replace('-', '_')
                            allowed_symbols[f'x_{safe_id}'] = symbols(f'x_{safe_id}')
                            allowed_symbols[f'y_{safe_id}'] = symbols(f'y_{safe_id}')
                        eq = parse_expr(constraint, local_dict=allowed_symbols, transformations=standard_transformations)
                        equations.append(eq)
                    except Exception:
                        pass
                else:
                    equations.append(constraint)
        
        if not equations or not variables:
            return None
        
        def objective(x):
            """返回残差向量。least_squares 允许方程数与变量数不等，
            即使系统欠约束（方程 < 变量）或过约束（方程 > 变量），
            也能返回最小二乘意义上的最优解，而 fsolve 在这种情况下
            会直接抛出 shape mismatch 异常导致崩溃。"""
            result = []
            var_dict = {}
            for i, var in enumerate(variables):
                var_dict[var] = x[i]
            
            for eq in equations:
                try:
                    eq_expr = eq.lhs - eq.rhs if isinstance(eq, Eq) else eq
                    val = float(eq_expr.subs(var_dict).evalf())
                    result.append(val)
                except Exception:
                    # 求值失败时残差记为 0，避免优化器被异常打断
                    result.append(0.0)
            
            return np.array(result, dtype=float)
        
        initial_guess = []
        for point in points:
            initial_guess.append(point.coordinates.get('x', 0.0))
            initial_guess.append(point.coordinates.get('y', 0.0))
        
        try:
            # 自动选择 least_squares 算法：
            # - 'lm' (Levenberg-Marquardt)：要求方程数 ≥ 变量数，适合过约束/适定
            # - 'trf' (Trust Region Reflective)：兼容欠约束（方程数 < 变量数）
            n_eq = len(equations)
            n_var = len(variables)
            method = 'lm' if n_eq >= n_var else 'trf'
            result_obj = least_squares(objective, np.array(initial_guess), method=method)
            if not result_obj.success:
                return {'success': False, 'error': result_obj.message}
            
            result = result_obj.x
            
            for point in points:
                x_idx = var_to_idx.get((point.id, 'x'))
                y_idx = var_to_idx.get((point.id, 'y'))
                if x_idx is not None and y_idx is not None:
                    self.update_point(point.id, x=result[x_idx], y=result[y_idx])
            
            return {'success': True, 'solution': result.tolist()}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_constraint(self, obj_id, constraint):
        if obj_id not in self.objects:
            return {'success': False, 'error': 'Object not found'}
        
        obj = self.objects[obj_id]
        obj.constraints.append(constraint)
        return {'success': True}
    
    def remove_constraint(self, obj_id, constraint):
        if obj_id not in self.objects:
            return {'success': False, 'error': 'Object not found'}
        
        obj = self.objects[obj_id]
        if constraint in obj.constraints:
            obj.constraints.remove(constraint)
            return {'success': True}
        return {'success': False, 'error': 'Constraint not found'}
    
    def serialize_all(self):
        return {
            'objects': {obj_id: obj.serialize() for obj_id, obj in self.objects.items()},
            'name_counter': dict(self.name_counter)
        }
    
    def deserialize_all(self, data):
        self.objects.clear()
        self.name_counter = defaultdict(int, data.get('name_counter', {}))
        self.dependencies = DAG()
        
        for obj_id, obj_data in data.get('objects', {}).items():
            obj = GeometricObject.deserialize(obj_data)
            self.objects[obj_id] = obj
            for dep in obj.depends_on:
                self.dependencies.add_edge(dep, obj_id)
        
        for obj in self.objects.values():
            if hasattr(obj, 'update_coordinates'):
                # 所有依赖其他节点（点）的几何对象都需要刷新坐标，
                # 否则反序列化时这些对象会停留在初始默认值。
                if type(obj).__name__ in ('Segment', 'Circle', 'Polygon',
                                          'Ellipse', 'Hyperbola', 'Parabola', 'Locus'):
                    obj.update_coordinates(self)
            self._notify('object_added', obj.serialize())
    
    def clear(self):
        self.objects.clear()
        self.name_counter.clear()
        self.dependencies = DAG()
        self._notify('canvas_cleared', None)
