import subprocess
import sys
import os
import json
import threading
import time
import tempfile
import signal
from queue import Queue
from mathlab.utils.logger import get_logger

logger = get_logger(__name__)

# 强烈建议在环境依赖中添加 psutil 库（pip install psutil）
# 如果没有安装，我们将使用降级方案，但 psutil 是跨平台精准监控内存的最佳手段
try:
    import psutil
except ImportError:
    psutil = None

class SandboxProcess:
    def __init__(self):
        self.process = None
        self.running = False
        self.output_queue = Queue()
        self.error_queue = Queue()
        self.result_queue = Queue()
        self.max_memory_mb = 512        # 严格限制 512MB 内存
        self.max_time_seconds = 60      # 严格限制 60秒 执行时间
        self._watchdog_triggered = False
        self._watchdog_error_msg = ""
    
    def _read_output(self, pipe, queue):
        try:
            while True:
                line = pipe.readline()
                if not line:
                    break
                queue.put(line.decode('utf-8', errors='replace'))
        except:
            pass

    def _monitor_watchdog(self, timeout):
        """
        核心看门狗线程：主动轮询子进程的 CPU 时间与物理内存开销
        一旦超过阈值，立刻从外部施加硬核毁灭（SIGKILL / taskkill），彻底解决任何死循环
        """
        start_time = time.time()
        while self.running and self.process and self.process.poll() is None:
            current_time = time.time()
            elapsed_time = current_time - start_time
            
            # 1. 检查时间超时（防止任何级别的 CPU 死循环）
            if elapsed_time > timeout:
                self._watchdog_triggered = True
                self._watchdog_error_msg = f"Execution timed out after {timeout} seconds."
                self.terminate()
                break
            
            # 2. 检查内存占用（防止旨在撑爆内存的死循环）
            if psutil:
                try:
                    # 获取该子进程及其所有派生子进程的总内存
                    parent = psutil.Process(self.process.pid)
                    total_memory = parent.memory_info().rss
                    for child in parent.children(recursive=True):
                        total_memory += child.memory_info().rss
                    
                    total_memory_mb = total_memory / (1024 * 1024)
                    if total_memory_mb > self.max_memory_mb:
                        self._watchdog_triggered = True
                        self._watchdog_error_msg = f"Memory limit exceeded: Used {total_memory_mb:.1f}MB / Max {self.max_memory_mb}MB."
                        self.terminate()
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            time.sleep(0.1)  # 高频轮询，兼顾性能
    
    def _start_process(self):
        sandbox_script_path = os.path.join(os.path.dirname(__file__), 'sandbox_script.py')
        env = os.environ.copy()
        extra_paths = ';'.join(sys.path) if sys.platform == 'win32' else ':'.join(sys.path)
        env['PYTHONPATH'] = f"{env.get('PYTHONPATH', '')}{';' if sys.platform == 'win32' else ':'}{extra_paths}".strip(';:')
        
        creation_flags = 0
        preexec_fn = None
        if sys.platform == 'win32':
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            preexec_fn = os.setsid
            
        self.process = subprocess.Popen(
            [sys.executable, sandbox_script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            creationflags=creation_flags,
            preexec_fn=preexec_fn,
            text=True
        )
        self.running = True

    def run_code(self, code, timeout=None):
        if timeout is None:
            timeout = self.max_time_seconds
        
        if not self.process or self.process.poll() is not None:
            self._start_process()
            
        self._watchdog_triggered = False
        self._watchdog_error_msg = ""
        
        req = json.dumps({'code': code})
        self.process.stdin.write(req + '\n')
        self.process.stdin.flush()
        
        result_queue = Queue()
        
        def read_response():
            try:
                line = self.process.stdout.readline()
                if line:
                    result_queue.put(json.loads(line))
            except Exception as e:
                pass
                
        reader_thread = threading.Thread(target=read_response, daemon=True)
        reader_thread.start()
        
        # Watchdog logic
        start_time = time.time()
        while reader_thread.is_alive():
            elapsed = time.time() - start_time
            if elapsed > timeout:
                self._watchdog_triggered = True
                self._watchdog_error_msg = f"Execution timed out after {timeout} seconds."
                self.terminate()
                break
                
            if psutil and self.process:
                try:
                    parent = psutil.Process(self.process.pid)
                    total_memory = parent.memory_info().rss
                    for child in parent.children(recursive=True):
                        total_memory += child.memory_info().rss
                    if (total_memory / (1024 * 1024)) > self.max_memory_mb:
                        self._watchdog_triggered = True
                        self._watchdog_error_msg = f"Memory limit exceeded."
                        self.terminate()
                        break
                except Exception:
                    pass
            time.sleep(0.05)
            
        if self._watchdog_triggered:
            return {'success': False, 'output': '', 'error': self._watchdog_error_msg, 'result': None}
            
        if not result_queue.empty():
            res = result_queue.get()
            return {'success': res.get('success', False), 'output': res.get('output', ''), 'error': res.get('error', ''), 'result': None}
            
        return {'success': False, 'output': '', 'error': 'Sandbox process died unexpectedly', 'result': None}

    
    def terminate(self):
        """
        毁灭级终止：不论是多级进程树、C层死循环，全部连根拔起
        """
        if self.process and self.running:
            try:
                if sys.platform == 'win32':
                    # Windows下使用 /T 杀死进程树，/F 强制杀死
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.process.pid)], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    # Unix下通过向进程组 ID（负的 PID）发送 SIGKILL，全组连带子进程瞬间清除
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # 进程可能已经退出
            except Exception as e:
                logger.warning("终止沙箱子进程时出错: %s", e)
            finally:
                self.running = False
    
    def is_running(self):
        return self.running

class SandboxManager:
    def __init__(self):
        self.sandboxes = {}
        self.sandbox_counter = 0
    
    def create_sandbox(self):
        sandbox_id = f'sandbox_{self.sandbox_counter}'
        self.sandbox_counter += 1
        self.sandboxes[sandbox_id] = SandboxProcess()
        return sandbox_id
    
    def run_in_sandbox(self, sandbox_id, code, timeout=None):
        if sandbox_id not in self.sandboxes:
            return {'success': False, 'error': 'Sandbox not found'}
        
        sandbox = self.sandboxes[sandbox_id]
        return sandbox.run_code(code, timeout)
    
    def terminate_sandbox(self, sandbox_id):
        if sandbox_id in self.sandboxes:
            self.sandboxes[sandbox_id].terminate()
    
    def destroy_sandbox(self, sandbox_id):
        if sandbox_id in self.sandboxes:
            self.terminate_sandbox(sandbox_id)
            del self.sandboxes[sandbox_id]
    
    def get_sandbox_status(self, sandbox_id):
        if sandbox_id not in self.sandboxes:
            return None
        return {
            'running': self.sandboxes[sandbox_id].is_running()
        }
