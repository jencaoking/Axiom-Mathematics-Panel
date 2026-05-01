import subprocess
import sys
import os
import json
import threading
import time
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
        
        script_path = os.path.join(os.path.dirname(__file__), 'sandbox_script.py')
        
        with open(script_path, 'w') as f:
            f.write(code)
        
        env = os.environ.copy()
        env['PYTHONPATH'] = ':'.join(sys.path)
        
        self.process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )
        
        self.running = True
        
        stdout_thread = threading.Thread(
            target=self._read_output,
            args=(self.process.stdout, self.output_queue)
        )
        stderr_thread = threading.Thread(
            target=self._read_output,
            args=(self.process.stderr, self.error_queue)
        )
        
        stdout_thread.start()
        stderr_thread.start()
        
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
        
        output = ''.join([self.output_queue.get_nowait() for _ in range(self.output_queue.qsize())])
        error = ''.join([self.error_queue.get_nowait() for _ in range(self.error_queue.qsize())])
        
        result = None
        success = self.process.returncode == 0
        
        self.running = False
        
        return {
            'success': success,
            'output': output,
            'error': error,
            'result': result
        }
    
    def terminate(self):
        if self.process and self.running:
            try:
                if sys.platform == 'win32':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.process.pid)])
                else:
                    self.process.terminate()
                    self.process.wait(timeout=5)
            except:
                pass
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
