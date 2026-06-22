import json
import socket
import time
from mathlab.utils.logger import get_logger

# 引入项目中已有的 logger
logger = get_logger(__name__)

class JupyterIPCClient:
    """
    负责将 Qt 画布的数据单向发送给 Jupyter 内核
    改进：增加了序列号防乱序，移除了静默 pass
    """
    def __init__(self, port=45679):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 为高频高并发场景增加序列号生成器
        self._seq_counter = 0

    def sync_variable(self, name: str, value: float):
        """向 Jupyter 发送变量同步指令"""
        self._seq_counter += 1
        
        payload = {
            "cmd": "sync_var", 
            "name": name, 
            "val": value,
            "seq": self._seq_counter,  # 注入序列号
            "timestamp": time.time()   # 可选：注入时间戳供服务器做延迟分析
        }
        
        try:
            # 尽可能序列化紧凑的 json 减少 UDP 包体积
            data = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            self.sock.sendto(data, ('127.0.0.1', self.port))
        except BlockingIOError:
            logger.warning(f"UDP 缓冲区已满，变量 {name} 同步指令被丢弃")
        except Exception as e:
            logger.error(f"Jupyter IPC 同步变量失败: {e}")
