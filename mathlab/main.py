import sys
import os
import platform
import traceback

# PyInstaller打包后路径处理
if getattr(sys, 'frozen', False):
    # exe运行模式
    application_path = sys._MEIPASS
    _CRASH_LOG_DIR = os.path.dirname(sys.executable)
    
    # 修复 QtWebEngineProcess 找不到 PySide6 内部 DLL 的系统错误弹窗
    pyside_dir = os.path.join(sys._MEIPASS, 'PySide6')
    os.environ['PATH'] = pyside_dir + os.pathsep + os.environ.get('PATH', '')
    os.environ['QTWEBENGINEPROCESS_PATH'] = os.path.join(pyside_dir, 'QtWebEngineProcess.exe')
else:
    # 开发模式
    application_path = os.path.dirname(os.path.abspath(__file__))
    _CRASH_LOG_DIR = application_path

mathlab_dir = application_path
sys.path.insert(0, os.path.dirname(mathlab_dir))


def _write_crash_log(exc_type, exc_value, exc_tb):
    """将启动阶段的致命错误写入崩溃日志（exe 同级目录），确保 console=False 时也能看到错误"""
    crash_file = os.path.join(_CRASH_LOG_DIR, "crash.log")
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    with open(crash_file, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"MathLab 启动崩溃报告\n")
        f.write(f"Python: {sys.version}\n")
        f.write(f"Platform: {sys.platform}\n")
        f.write(f"Executable: {sys.executable}\n")
        f.write("=" * 60 + "\n\n")
        f.write(tb_str)
    # 同时打印到 stderr（开发模式可见）
    print(tb_str, file=sys.stderr)


# ── 第一步：最早期初始化全局日志系统 ──────────────────────────────────────────
# 必须在任何其他 mathlab 模块导入之前完成，确保所有初始化过程都被记录
try:
    from mathlab.utils.logger import setup_logger, get_logger
    setup_logger()
    logger = get_logger(__name__)
    logger.info("日志系统初始化完毕，开始加载 MathLab 模块...")
except Exception:
    # 日志系统本身崩溃时，写崩溃日志并退出
    _write_crash_log(*sys.exc_info())
    sys.exit(1)

from mathlab.core.error_manager import install_error_handler
install_error_handler()
# ─────────────────────────────────────────────────────────────────────────────

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt

from mathlab.ui.main_window import MainWindow
from mathlab.core.geometry_engine import GeometryEngine
from mathlab.core.cas_provider import CASProvider
from mathlab.core.algo_animator import AlgoAnimator
from mathlab.core.python_repl import PythonREPL
from mathlab.core.ai_manager import AIManager
from mathlab.core.sandbox import SandboxManager
from mathlab.data.project import ProjectManager


def main():
    logger.info("正在初始化 QApplication...")
    try:
        app = QApplication(sys.argv)
        
        # 🚨 修复字体环境：根据不同操作系统注入最完美的无衬线黑体
        sys_os = platform.system()
        if sys_os == "Windows":
            # 强制使用微软雅黑，防宋体发虚
            font_family = "Microsoft YaHei" 
        elif sys_os == "Darwin":
            # macOS 原生苹方/SF字体
            font_family = ".AppleSystemUIFont" 
        else:
            # Linux 备选
            font_family = "Ubuntu" 
            
        font = QFont(font_family, 10)
        font.setStyleStrategy(QFont.PreferAntialias) # 开启抗锯齿
        app.setFont(font)
        
        # 🚨 2. 开启高 DPI 缩放支持
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app.setApplicationName('MathLab')
        app.setApplicationVersion('1.0')
        
        icon_path = os.path.join(mathlab_dir, 'resources', 'icons', 'app_icon.png')
        app.setWindowIcon(QIcon(icon_path))

        try:
            stylesheet_path = os.path.join(mathlab_dir, 'ui', 'styles.qss')
            with open(stylesheet_path, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())
            logger.debug("样式表加载完毕: %s", stylesheet_path)
        except FileNotFoundError:
            logger.warning('样式表文件未找到: %s', stylesheet_path)
        except Exception as e:
            logger.warning('样式表加载失败: %s', e)

        logger.info("正在创建主窗口...")
        window = MainWindow()

        window.geometry_engine = GeometryEngine()
        window.cas_provider = CASProvider()
        window.algo_animator = AlgoAnimator()
        window.python_repl = PythonREPL()
        window.ai_manager = AIManager()
        window.project_manager = ProjectManager()
        window.sandbox_manager = SandboxManager()
        logger.info("核心引擎初始化完毕。")

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
            if not hasattr(window, 'algebra_panel') or not hasattr(window, 'central_widget'):
                return
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
            if hasattr(window, 'algo_vis_panel'):
                window.algo_vis_panel.update_visualization(state)

        window.algo_animator.step_ready = on_algorithm_step

        # ── 初始化并启动插件化框架 ─────────────────────────────────────
        from mathlab.core.extension_api import MathLabAPI
        from mathlab.core.plugin_manager import PluginManager

        window.mathlab_api = MathLabAPI(
            main_window=window,
            cmd_manager=window.cmd_manager,
            console=window.console
        )
        window.plugin_manager = PluginManager(window.mathlab_api)
        window.plugin_manager.load_all_plugins()
        # ─────────────────────────────────────────────────────────────

        window.show()
        
        # ── 关闭 PyInstaller Splash Screen ──
        try:
            import pyi_splash
            if pyi_splash.is_alive():
                pyi_splash.close()
                logger.info("已关闭 PyInstaller 启动画面。")
        except ImportError:
            pass

        logger.info("主窗口加载完毕，进入 Qt 事件循环。")
        sys.exit(app.exec())

    except Exception as e:
        logger.critical("系统启动失败: %s", e, exc_info=True)
        _write_crash_log(*sys.exc_info())
        sys.exit(1)


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()

    # ── 拦截子进程调用 (解决 PyInstaller 无限弹黑窗口闪退问题) ──
    if len(sys.argv) >= 2:
        # 拦截 Jupyter kernel 的启动 (-m ipykernel_launcher)
        if sys.argv[1] == '-m' and len(sys.argv) >= 3 and sys.argv[2] == 'ipykernel_launcher':
            from ipykernel import kernelapp
            kernelapp.launch_new_instance()
            sys.exit(0)
        # 拦截我们自己沙盒进程的启动 (sandbox_script.py)
        elif sys.argv[1].endswith('sandbox_script.py'):
            import runpy
            runpy.run_path(sys.argv[1], run_name='__main__')
            sys.exit(0)

    # ── 最外层崩溃捕获：确保导入阶段或 main() 之前的错误也能被记录 ──
    try:
        main()
    except Exception:
        _write_crash_log(*sys.exc_info())
        sys.exit(1)
