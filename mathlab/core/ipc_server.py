import json
import socket
from PySide6.QtCore import QThread, Signal
from mathlab.utils.logger import get_logger

logger = get_logger(__name__)

class JupyterIPCServer(QThread):
    """
    接收来自 Jupyter 内核跨进程指令的 UDP 服务器
    改进：扩充接收缓冲、丢弃过期乱序包、细化异常捕获
    """
    command_received = Signal(dict)

    def __init__(self, port=45678, parent=None):
        super().__init__(parent)
        self.port = port
        self.is_running = True
        
        # 记录每个变量名对应的最新序列号，防止状态回滚
        self._var_sequence_tracker = {}

    def run(self):
        """后台线程循环监听端口"""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('127.0.0.1', self.port))
            
            # 细节优化 1：扩大 UDP 系统接收缓冲区（如 1MB），防止突发高频指令导致系统底层丢包
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
            sock.settimeout(1.0) 
            
            logger.info(f"📡 MathLab IPC Server 正在监听端口 {self.port}...")
            
            while self.is_running:
                try:
                    # 细节优化 2：适度扩大单词接收容量（从4096到8192），适应大数组变量
                    data, addr = sock.recvfrom(8192)
                    message = json.loads(data.decode('utf-8'))
                    
                    # 细节优化 3：拦截乱序数据包
                    if message.get("cmd") == "sync_var":
                        var_name = message.get("name")
                        seq = message.get("seq", 0)
                        
                        last_seq = self._var_sequence_tracker.get(var_name, -1)
                        if seq <= last_seq:
                            # 这是一个迟到的旧数据包，直接丢弃，防止变量状态回退
                            continue
                        # 更新最新序列号
                        self._var_sequence_tracker[var_name] = seq
                    
                    # 只有最新的合法包才交给主线程
                    self.command_received.emit(message)
                    
                except socket.timeout:
                    continue
                except json.JSONDecodeError as e:
                    logger.warning(f"IPC 收到了无法解析的非 JSON 数据: {e}")
                except Exception as e:
                    logger.error(f"IPC 服务器运行时错误: {e}")

    def stop(self):
        self.is_running = False
        self.wait()
