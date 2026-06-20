import sys
import os

# PyInstaller打包后路径处理
if getattr(sys, 'frozen', False):
    # exe运行模式
    application_path = sys._MEIPASS
else:
    # 开发模式
    application_path = os.path.dirname(os.path.abspath(__file__))

mathlab_dir = application_path
sys.path.insert(0, mathlab_dir)
sys.path.insert(0, os.path.dirname(mathlab_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from ui.main_window import MainWindow
from core.geometry_engine import GeometryEngine
from core.cas_provider import CASProvider
from core.algo_animator import AlgoAnimator
from core.python_repl import PythonREPL
from core.ai_manager import AIManager

def main():
    app = QApplication(sys.argv)
    app.setApplicationName('MathLab')
    app.setApplicationVersion('1.0')
    
    try:
        stylesheet_path = os.path.join(mathlab_dir, 'ui', 'styles.qss')
        with open(stylesheet_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    except Exception:
        pass
    
    window = MainWindow()
    
    window.geometry_engine = GeometryEngine()
    window.cas_provider = CASProvider()
    window.algo_animator = AlgoAnimator()
    window.python_repl = PythonREPL()
    window.ai_manager = AIManager()
    
    window.python_repl.update_namespace({
        'draw_point': lambda x, y: window.geometry_engine.add_point(x, y),
        'draw_segment': lambda p1, p2: window.geometry_engine.add_segment(p1, p2),
        'draw_circle': lambda center, radius: window.geometry_engine.add_circle(center, radius),
        'clear_canvas': lambda: window.geometry_engine.objects.clear(),
        # 新增：圆锥曲线
        'draw_ellipse': lambda center_id, a=2.0, b=1.0: window.geometry_engine.add_ellipse(center_id, a, b),
        'draw_hyperbola': lambda center_id, a=1.0, b=1.0: window.geometry_engine.add_hyperbola(center_id, a, b),
        'draw_parabola': lambda vertex_id, p=1.0, direction='up': window.geometry_engine.add_parabola(vertex_id, p, direction),
        'draw_conic': lambda A=1, B=0, C=1, D=0, E=0, F=-1: window.geometry_engine.add_conic_section(A, B, C, D, E, F),
        # 新增：函数绘图
        'plot_function': lambda expr, x_range=(-10, 10): window.geometry_engine.add_function_plot(expr, x_range),
        'plot_implicit': lambda expr, x_range=(-10, 10), y_range=(-10, 10): window.geometry_engine.add_implicit_plot(expr, x_range, y_range),
        'plot_polar': lambda expr, theta_range=(0, 6.28318): window.geometry_engine.add_polar_plot(expr, theta_range),
        # 新增：轨迹追踪
        'create_locus': lambda tracer_id, driver_id: window.geometry_engine.add_locus(tracer_id, driver_id),
        'update_locus': lambda locus_id: window.geometry_engine.update_locus(locus_id),
        'solve': window.cas_provider.solve_equation,
        'simplify': window.cas_provider.simplify,
        'integrate': window.cas_provider.integrate,
        'differentiate': window.cas_provider.differentiate,
        'limit': window.cas_provider.limit,
        'app': window,
    })
    
    def on_geometry_event(event_type, data):
        if event_type == 'object_added':
            window.algebra_panel.add_object(data)
            window.central_widget.draw_object(data['id'], data)
        elif event_type == 'object_updated':
            window.algebra_panel.update_object(data)
            window.central_widget.update_object(data['id'], data)
        elif event_type == 'object_removed':
            obj_id = data['id'] if isinstance(data, dict) else data
            window.algebra_panel.remove_object(obj_id)
            window.central_widget.remove_object(obj_id)
    
    window.geometry_engine.add_listener(on_geometry_event)
    
    def on_algorithm_step(state):
        window.algo_vis_panel.update_visualization(state)
    
    window.algo_animator.step_ready = on_algorithm_step
    
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
