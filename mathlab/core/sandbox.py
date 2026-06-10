import subprocess
import sys
import os
import json
import threading
import time
import tempfile
from queue import Queue

class SandboxProcess:
    def __init__(self):
        self.process = None
        self.running = False
        self.output_queue = Queue()
        self.error_queue = Queue()
        self.result_queue = Queue()
        self.max_memory_mb = 512
        self.max_time_seconds = 60
    
    def _read_output(self, pipe, queue):
        try:
            while True:
                line = pipe.readline()
                if not line:
                    break
                queue.put(line.decode('utf-8', errors='replace'))
        except:
            pass
    
    def run_code(self, code, timeout=None):
        if timeout is None:
            timeout = self.max_time_seconds
        
        sandbox_script_path = os.path.join(os.path.dirname(__file__), 'sandbox_script.py')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            code_file_path = f.name
        
        env = os.environ.copy()
        current_pythonpath = env.get('PYTHONPATH', '')
        extra_paths = ';'.join(sys.path) if sys.platform == 'win32' else ':'.join(sys.path)
        
        if current_pythonpath:
            env['PYTHONPATH'] = f"{current_pythonpath}{';' if sys.platform == 'win32' else ':'}{extra_paths}"
        else:
            env['PYTHONPATH'] = extra_paths
        
        creation_flags = 0
        if sys.platform == 'win32':
            try:
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            except AttributeError:
                pass

        self.process = subprocess.Popen(
            [sys.executable, sandbox_script_path, code_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            creationflags=creation_flags
        )
        
        self.running = True
        
        stdout_thread = threading.Thread(
            target=self._read_output,
            args=(self.process.stdout, self.output_queue),
            daemon=True
        )
        stderr_thread = threading.Thread(
            target=self._read_output,
            args=(self.process.stderr, self.error_queue),
            daemon=True
        )
        
        stdout_thread.start()
        stderr_thread.start()
        
        try:
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.terminate()
                return {
                    'success': False,
                    'output': '',
                    'error': 'Execution timed out',
                    'result': None
                }
            
            stdout_thread.join()
            stderr_thread.join()
            
            output = ''
            while not self.output_queue.empty():
                try:
                    output += self.output_queue.get_nowait()
                except Exception:
                    pass
            
            error = ''
            while not self.error_queue.empty():
                try:
                    error += self.error_queue.get_nowait()
                except Exception:
                    pass
            
            result = None
            success = self.process.returncode == 0
            
            self.running = False
            
            return {
                'success': success,
                'output': output,
                'error': error,
                'result': result
            }
        finally:
            # 增加重试机制以应对 Windows 下的文件锁延迟
            for _ in range(3):
                try:
                    os.unlink(code_file_path)
                    break
                except OSError:
                    time.sleep(0.1)
    
    def terminate(self):
        if self.process and self.running:
            try:
                if sys.platform == 'win32':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.process.pid)])
                else:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait()
            except Exception as e:
                print(f"Warning: Failed to terminate process: {e}")
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
