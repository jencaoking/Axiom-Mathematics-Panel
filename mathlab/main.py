import sys
import os

mathlab_dir = os.path.dirname(os.path.abspath(__file__))
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
        stylesheet_path = os.path.join(os.path.dirname(__file__), 'ui', 'styles.qss')
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
            window.algebra_panel.remove_object(data)
            window.central_widget.remove_object(data)
    
    window.geometry_engine.add_listener(on_geometry_event)
    
    def on_algorithm_step(state):
        window.algo_vis_panel.update_visualization(state)
    
    window.algo_animator.step_ready = on_algorithm_step
    
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
