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
