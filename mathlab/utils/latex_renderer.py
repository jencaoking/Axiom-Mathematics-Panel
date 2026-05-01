from sympy import latex as sympy_latex

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
