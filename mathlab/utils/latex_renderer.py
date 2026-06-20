import io
from functools import lru_cache
from sympy import latex as sympy_latex

# 尝试导入可选依赖
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from PySide6.QtCore import QByteArray
    from PySide6.QtSvg import QSvgRenderer
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False


# ----------------------------------------------------------------------
# 核心1：LRU 缓存，防止相同公式重复渲染消耗 CPU
# ----------------------------------------------------------------------
@lru_cache(maxsize=256)
def generate_latex_svg(latex_str: str, color: str = '#0b1c30', font_size: int = 12):
    """
    将 LaTeX 字符串渲染为无损 SVG 字节流
    
    Args:
        latex_str: LaTeX 公式字符串（不含 $ 符号）
        color: 文本颜色，默认深蓝色
        font_size: 字体大小
    
    Returns:
        QByteArray: SVG 字节流，可直接用于 QSvgRenderer
        None: 如果 matplotlib 不可用
    """
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    try:
        fig = plt.figure(figsize=(0.01, 0.01))
        # 确保 latex_str 包含 $ 符号
        if not latex_str.startswith('$'):
            latex_content = f'${latex_str}$'
        else:
            latex_content = latex_str
        
        fig.text(0, 0, latex_content, fontsize=font_size, color=color, 
                 ha='center', va='center')
        
        buf = io.BytesIO()
        fig.savefig(buf, format='svg', transparent=True, bbox_inches='tight', pad_inches=0.05)
        plt.close(fig)
        
        if PYSIDE_AVAILABLE:
            return QByteArray(buf.getvalue())
        return buf.getvalue()
    except Exception:
        return None


class SharedSvgRendererCache:
    """
    核心2：复用 QSvgRenderer 实例，降低显存开销
    
    使用类级别缓存，确保相同的 LaTeX 公式只创建一个 QSvgRenderer 实例，
    多个 MathGraphicsItem 可以共享同一个渲染器。
    """
    _cache = {}
    
    @classmethod
    def get_renderer(cls, latex_str: str, color: str = '#0b1c30'):
        """
        获取或创建 SVG 渲染器
        
        Args:
            latex_str: LaTeX 公式字符串
            color: 文本颜色
        
        Returns:
            QSvgRenderer: SVG 渲染器实例
            None: 如果 PySide6 或 matplotlib 不可用
        """
        if not PYSIDE_AVAILABLE or not MATPLOTLIB_AVAILABLE:
            return None
        
        cache_key = f"{latex_str}_{color}"
        if cache_key not in cls._cache:
            svg_data = generate_latex_svg(latex_str, color)
            if svg_data is not None:
                renderer = QSvgRenderer(svg_data)
                cls._cache[cache_key] = renderer
            else:
                return None
        return cls._cache.get(cache_key)
    
    @classmethod
    def clear_cache(cls):
        """清空渲染器缓存"""
        cls._cache.clear()
    
    @classmethod
    def cache_size(cls):
        """返回当前缓存大小"""
        return len(cls._cache)


def is_latex_rendering_available():
    """检查 LaTeX SVG 渲染是否可用"""
    return MATPLOTLIB_AVAILABLE and PYSIDE_AVAILABLE


# ----------------------------------------------------------------------
# 原有的 LaTeX 格式化函数
# ----------------------------------------------------------------------
def render_expression(expr):
    try:
        return sympy_latex(expr)
    except:
        return str(expr)

def format_point(name, x, y):
    return rf'{name} = ({x}, {y})'

def format_segment(name, p1_name, p2_name):
    return rf'\overline{{{p1_name}{p2_name}}}'

def format_circle(name, center_name, radius):
    return rf'Circle({center_name}, {radius})'

def format_line(name, p1_name, p2_name):
    return rf'\overleftrightarrow{{{p1_name}{p2_name}}}'

def format_angle(name, p1_name, vertex_name, p2_name):
    return rf'\angle {p1_name}{vertex_name}{p2_name}'

def format_polygon(name, point_names):
    return rf'{name} = {point_names}'

def format_equation(expr):
    return rf'${sympy_latex(expr)}$'

def format_solution(solutions):
    if not solutions:
        return 'No solution'
    return ', '.join([rf'${s}$' for s in solutions])

def export_canvas_to_latex(objects_data):
    latex_parts = []
    latex_parts.append(r'\documentclass[tikz]{standalone}')
    latex_parts.append(r'\usepackage{tikz}')
    latex_parts.append(r'\usepackage{amsmath}')
    latex_parts.append(r'\usepackage{pgfplots}')
    latex_parts.append(r'\pgfplotsset{compat=1.18}')
    latex_parts.append(r'\begin{document}')
    latex_parts.append(r'\begin{tikzpicture}[scale=0.5, every node/.style={font=\sffamily}]')
    
    for obj in objects_data:
        obj_type = obj.get('type', '')
        name = obj.get('name', '')
        coords = obj.get('coordinates', {})
        
        if obj_type == 'Point':
            x = coords.get('x', 0)
            y = coords.get('y', 0)
            latex_parts.append(rf'\fill[blue] ({x}, {y}) circle (3pt);')
            latex_parts.append(rf'\node[above] at ({x}, {y}) {{{name}}};')
        elif obj_type == 'Segment':
            x1 = coords.get('x1', 0)
            y1 = coords.get('y1', 0)
            x2 = coords.get('x2', 0)
            y2 = coords.get('y2', 0)
            latex_parts.append(rf'\draw[thick, blue] ({x1}, {y1}) -- ({x2}, {y2});')
        elif obj_type == 'Circle':
            cx = coords.get('cx', 0)
            cy = coords.get('cy', 0)
            r = coords.get('r', 1)
            latex_parts.append(rf'\draw[thick, teal] ({cx}, {cy}) circle ({r});')
        elif obj_type == 'Polygon':
            points = coords.get('points', [])
            if points:
                path = ' -- '.join([f'({p[0]}, {p[1]})' for p in points])
                latex_parts.append(rf'\draw[thick, purple, fill=purple!20] {path} -- cycle;')
    
    latex_parts.append(r'\end{tikzpicture}')
    latex_parts.append(r'\end{document}')
    
    return '\n'.join(latex_parts)
