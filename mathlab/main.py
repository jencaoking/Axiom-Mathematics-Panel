import os
import platform
import sys
import traceback

# PyInstaller打包后路径处理
if getattr(sys, "frozen", False):
    # exe运行模式
    application_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    _CRASH_LOG_DIR = os.path.dirname(sys.executable)

    # 修复 QtWebEngineProcess 找不到 PySide6 内部 DLL 的系统错误弹窗
    pyside_dir = os.path.join(getattr(sys, "_MEIPASS", ""), "PySide6")
    os.environ["PATH"] = pyside_dir + os.pathsep + os.environ.get("PATH", "")
    os.environ["QTWEBENGINEPROCESS_PATH"] = os.path.join(pyside_dir, "QtWebEngineProcess.exe")
else:
    # 开发模式
    application_path = os.path.dirname(os.path.abspath(__file__))
    _CRASH_LOG_DIR = application_path

mathlab_dir = application_path
sys.path.insert(0, application_path)


def _write_crash_log(exc_type, exc_value, exc_tb):
    """将启动阶段的致命错误写入崩溃日志（exe 同级目录），确保 console=False 时也能看到错误"""
    crash_file = os.path.join(_CRASH_LOG_DIR, "crash.log")
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    from datetime import datetime

    with open(crash_file, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}]\n")
        f.write("=" * 60 + "\n")
        f.write("MathLab 启动崩溃报告\n")
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
    from mathlab.utils.logger import get_logger, setup_logger

    setup_logger()
    logger = get_logger(__name__)
    logger.info("日志系统初始化完毕，开始加载 MathLab 模块...")
except Exception:
    # 日志系统本身崩溃时，写崩溃日志并退出
    _write_crash_log(*sys.exc_info())
    sys.exit(1)

from mathlab.core.error_manager import install_error_handler  # noqa: E402

install_error_handler()
# ─────────────────────────────────────────────────────────────────────────────

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QFont, QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from mathlab.ui.main_window import MainWindow  # noqa: E402
from mathlab.utils.version import __version__  # noqa: E402


def main():
    logger.info("正在初始化 QApplication...")
    try:
        # 🚨 2. 开启高 DPI 缩放支持
        if hasattr(Qt, "AA_EnableHighDpiScaling"):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, "AA_UseHighDpiPixmaps"):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)

        # 🚨 修复字体环境：根据不同操作系统注入最完美的无衬线黑体
        sys_os = platform.system()
        if sys_os == "Windows":
            font_family = "Microsoft YaHei"
        elif sys_os == "Darwin":
            font_family = ".AppleSystemUIFont"
        else:
            font_family = "Microsoft YaHei, Noto Sans CJK SC, Ubuntu"

        font = QFont(font_family, 10)
        font.setStyleStrategy(QFont.PreferAntialias)
        app.setFont(font)

        app.setApplicationName("MathLab")
        app.setApplicationVersion(__version__)

        icon_path = os.path.join(mathlab_dir, "resources", "icons", "app_icon.png")
        app.setWindowIcon(QIcon(icon_path))

        try:
            stylesheet_path = os.path.join(mathlab_dir, "ui", "styles.qss")
            with open(stylesheet_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
            logger.debug("样式表加载完毕: %s", stylesheet_path)
        except FileNotFoundError:
            logger.warning("样式表文件未找到: %s", stylesheet_path)
        except Exception as e:
            logger.warning("样式表加载失败: %s", e)

        logger.info("正在创建主窗口...")
        # MainWindow.__init__ 内部完成所有引擎初始化、REPL 命名空间注入、
        # 事件监听注册和插件系统启动，消除双重初始化反模式
        window = MainWindow()
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


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()

    if multiprocessing.current_process().name != "MainProcess":
        sys.exit(0)  # 避免子进程进 GUI

    # ── 拦截子进程调用 (解决 PyInstaller 无限弹黑窗口闪退问题) ──
    if len(sys.argv) >= 2:
        # 拦截 JupyterLab 的启动 (-m jupyter)
        if sys.argv[1] == "-m" and len(sys.argv) >= 3 and sys.argv[2] == "jupyter":
            # 调整 sys.argv 为 jupyter 期望的格式
            sys.argv = ["jupyter"] + sys.argv[3:]
            from jupyterlab.labapp import main

            main()
            sys.exit(0)
        # 拦截 Jupyter kernel 的启动 (-m ipykernel_launcher)
        if sys.argv[1] == "-m" and len(sys.argv) >= 3 and sys.argv[2] == "ipykernel_launcher":
            from ipykernel import kernelapp

            kernelapp.launch_new_instance()
            sys.exit(0)
        # 拦截我们自己沙盒进程的启动 (sandbox_script.py)
        elif sys.argv[1].endswith("sandbox_script.py"):
            import runpy

            if getattr(sys, "frozen", False):
                runpy.run_module("mathlab.core.sandbox_script", run_name="__main__")
            else:
                runpy.run_path(sys.argv[1], run_name="__main__")
            sys.exit(0)

    # ── 最外层崩溃捕获：确保导入阶段或 main() 之前的错误也能被记录 ──
    try:
        main()
    except Exception:
        _write_crash_log(*sys.exc_info())
        sys.exit(1)
