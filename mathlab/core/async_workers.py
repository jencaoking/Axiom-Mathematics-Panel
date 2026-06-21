import traceback
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from mathlab.utils.logger import get_logger

logger = get_logger(__name__)

class WorkerSignals(QObject):
    """定义通用异步任务的信号 (QRunnable 本身不能发信号，必须借由 QObject)"""
    finished = Signal(object)  # 任务成功完成，返回结果字典/对象
    error = Signal(str)        # 任务失败，返回错误堆栈
    progress = Signal(int)     # (预留) 任务进度 0-100

class TaskWorker(QRunnable):
    """
    统一的底层执行单元
    你可以将任何阻塞函数抛给它，无需再为每个功能写单独的 QThread
    """
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        # 设置自动删除，执行完后释放内存
        self.setAutoDelete(True)

    def run(self):
        try:
            # 动态执行传入的阻塞型函数
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            err_msg = traceback.format_exc()
            logger.exception(f"异步任务 {self.fn.__name__} 执行异常:\n{err_msg}")
            self.signals.error.emit(str(e))


class TaskManager(QObject):
    """
    全局异步任务调度中心 (单例模式)
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance._init_pool()
        return cls._instance

    def _init_pool(self):
        self.thread_pool = QThreadPool.globalInstance()
        # 获取系统 CPU 核心数，保留一个核心给主 UI 线程，防止机器整体卡顿
        import multiprocessing
        max_threads = max(1, multiprocessing.cpu_count() - 1)
        self.thread_pool.setMaxThreadCount(max_threads)
        logger.info(f"TaskManager 启动，最大并发线程数: {max_threads}")

    def submit(self, fn, on_success=None, on_error=None, *args, **kwargs):
        """
        核心 API：将阻塞任务提交至后台线程池
        
        :param fn: 需要执行的阻塞函数 (如 cas_provider.integrate)
        :param on_success: 成功后的回调槽函数 (UI 更新操作应放这里)
        :param on_error: 失败后的回调槽函数
        :param args/kwargs: 传递给 fn 的参数
        """
        worker = TaskWorker(fn, *args, **kwargs)
        
        if on_success:
            worker.signals.finished.connect(on_success)
        if on_error:
            worker.signals.error.connect(on_error)
            
        self.thread_pool.start(worker)
        logger.debug(f"已提交任务 [{fn.__name__}] 至线程池，当前活动线程: {self.thread_pool.activeThreadCount()}")