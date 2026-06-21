import io
from functools import lru_cache

try:
    import matplotlib
    # 强制使用无头后端(Agg)，防止 Matplotlib 弹窗与 Qt 主线程冲突
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from sympy import latex as sympy_latex
from PySide6.QtCore import QByteArray
from PySide6.QtSvg import QSvgRenderer

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

# ==========================================
# 混合渲染核心：SVG 生成与 LRU 缓存池
# ==========================================
@lru_cache(maxsize=256)
def generate_latex_svg(latex_str, color='#0b1c30', font_size=12):
    """
    将 LaTeX 字符串静默渲染为无损的 SVG 字节流。
    若 matplotlib 未安装，返回空 QByteArray（只影响代数公式渲染功能）。
    """
    if not MATPLOTLIB_AVAILABLE:
        return QByteArray()

    # 过滤掉首尾多余的 $ 符号，防止重复
    latex_str = latex_str.strip('$')

    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f'${latex_str}$', fontsize=font_size, color=color, ha='left', va='center')

    buf = io.BytesIO()
    fig.savefig(buf, format='svg', transparent=True, bbox_inches='tight', pad_inches=0.0)
    plt.close(fig)

    return QByteArray(buf.getvalue())

class SharedSvgRendererCache:
    """
    复用 QSvgRenderer 实例，大幅降低画布放大缩小时的显存开销
    """
    _cache = {}

    @classmethod
    def get_renderer(cls, latex_str, color='#0b1c30'):
        cache_key = f"{latex_str}_{color}"
        if cache_key not in cls._cache:
            svg_data = generate_latex_svg(latex_str, color)
            renderer = QSvgRenderer(svg_data)
            cls._cache[cache_key] = renderer
        return cls._cache[cache_key]