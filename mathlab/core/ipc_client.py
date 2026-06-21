import json
import socket

class JupyterIPCClient:
    """
    负责将 Qt 画布的数据单向发送给 Jupyter 内核
    """
    def __init__(self, port=45679):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def sync_variable(self, name: str, value: float):
        """向 Jupyter 发送变量同步指令"""
        payload = {
            "cmd": "sync_var", 
            "name": name, 
            "val": value
        }
        try:
            self.sock.sendto(json.dumps(payload).encode('utf-8'), ('127.0.0.1', self.port))
        except Exception:
            pass
