import json
import socket
from PySide6.QtCore import QThread, Signal

class JupyterIPCServer(QThread):
    """
    接收来自 Jupyter 内核跨进程指令的 UDP 服务器
    """
    # 定义信号：当收到指令时，向 Qt 主线程发射解析好的字典
    command_received = Signal(dict)

    def __init__(self, port=45678, parent=None):
        super().__init__(parent)
        self.port = port
        self.is_running = True

    def run(self):
        """后台线程循环监听端口"""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('127.0.0.1', self.port))
            sock.settimeout(1.0) # 设置超时，方便安全退出线程
            
            print(f"📡 MathLab IPC Server 正在监听端口 {self.port}...")
            
            while self.is_running:
                try:
                    data, _ = sock.recvfrom(4096)
                    message = json.loads(data.decode('utf-8'))
                    
                    # 收到数据包，通过信号抛给 Qt 主线程 (跨线程安全)
                    self.command_received.emit(message)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"IPC 解析错误: {e}")

    def stop(self):
        self.is_running = False
        self.wait()
