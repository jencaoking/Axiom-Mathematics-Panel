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
        # 用于防抖与任务覆盖：跟踪各组是否有任务运行及挂起的最新请求
        self._running_groups = set()
        self._pending_requests = {}
        
        logger.info(f"TaskManager 启动，最大并发线程数: {max_threads}")

    def submit(self, fn, on_success=None, on_error=None, group_id=None, *args, **kwargs):
        """
        核心 API：将阻塞任务提交至后台线程池
        
        :param fn: 需要执行的阻塞函数 (如 cas_provider.integrate)
        :param on_success: 成功后的回调槽函数 (UI 更新操作应放这里)
        :param on_error: 失败后的回调槽函数
        :param group_id: 任务分组 ID。提供此 ID 可防抖与抽搐拦截。
                         当同组任务正在执行时，新的请求会覆盖旧的排队请求，只执行最新一帧。
        :param args/kwargs: 传递给 fn 的参数
        """
        if group_id is not None:
            if group_id in self._running_groups:
                # 已有同组任务正在执行，覆盖挂起队列中的请求
                self._pending_requests[group_id] = {
                    'fn': fn,
                    'on_success': on_success,
                    'on_error': on_error,
                    'args': args,
                    'kwargs': kwargs
                }
                return
            else:
                self._running_groups.add(group_id)
                self._submit_internal(group_id, fn, on_success, on_error, *args, **kwargs)
        else:
            self._submit_internal(None, fn, on_success, on_error, *args, **kwargs)

    def _submit_internal(self, group_id, fn, on_success, on_error, *args, **kwargs):
        worker = TaskWorker(fn, *args, **kwargs)
        
        def success_interceptor(result):
            try:
                if on_success:
                    on_success(result)
            finally:
                self._check_pending(group_id)

        def error_interceptor(err):
            try:
                if on_error:
                    on_error(err)
            finally:
                self._check_pending(group_id)
            
        worker.signals.finished.connect(success_interceptor)
        worker.signals.error.connect(error_interceptor)
            
        self.thread_pool.start(worker)
        logger.debug(f"已提交任务 [{fn.__name__}] 至线程池，当前活动线程: {self.thread_pool.activeThreadCount()}")

    def _check_pending(self, group_id):
        if group_id is None:
            return
            
        if group_id in self._pending_requests:
            req = self._pending_requests.pop(group_id)
            self._submit_internal(
                group_id,
                req['fn'],
                req['on_success'],
                req['on_error'],
                *req['args'],
                **req['kwargs']
            )
        else:
            if group_id in self._running_groups:
                self._running_groups.remove(group_id)


# ──────────────────────────────────────────────────────────────────────────────
# AI 专用 Worker 占位类 (Stub)
# 待 AI 模块完整实现后，替换以下 stub 为真正的业务逻辑类。
# main_window.py 需要导入这些名字；这里先提供空实现防止 ImportError。
# ──────────────────────────────────────────────────────────────────────────────

class AIFitWorker(TaskWorker):
    """散点拟合 AI Worker（占位，待实现）"""
    pass


class AIClusterWorker(TaskWorker):
    """聚类分析 AI Worker（占位，待实现）"""
    pass


class AIRecognizeWorker(TaskWorker):
    """手写识别 AI Worker（占位，待实现）"""
    pass


class AIGeneratePointsWorker(TaskWorker):
    """AI 生成数据点 Worker（占位，待实现）"""
    pass