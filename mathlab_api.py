import json
import socket

class MathLabEngine:
    """
    MathLab 跨进程客户端 (供 Jupyter Notebook 使用)
    """
    def __init__(self, port=45678):
        self.port = port
        # 创建 UDP 客户端套接字
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _send(self, cmd: str, **kwargs):
        """打包并发送 JSON 指令"""
        payload = {"cmd": cmd}
        payload.update(kwargs)
        # 发送数据包到 Qt 监听的端口
        self.sock.sendto(json.dumps(payload).encode('utf-8'), ('127.0.0.1', self.port))

    def draw_point(self, name: str, x: float, y: float):
        """在 Qt 画布上画一个点"""
        self._send("draw_point", name=name, x=x, y=y)
        return f"[MathLab] 已发送坐标点: {name}({x}, {y})"

    def draw_line(self, name: str, p1_name: str, p2_name: str):
        """在 Qt 画布上连接两点"""
        self._send("draw_line", name=name, p1=p1_name, p2=p2_name)
        return f"[MathLab] 已发送连线指令: {name} ({p1_name} -> {p2_name})"
        
    def clear(self):
        """清空画布"""
        self._send("clear")
        return "[MathLab] 画布已清空"

# 实例化一个单例，方便用户直接导入使用
mlab = MathLabEngine()
