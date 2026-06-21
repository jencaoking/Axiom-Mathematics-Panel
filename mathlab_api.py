import json
import socket
import threading

class MathLabEngine:
    def __init__(self, send_port=45678, recv_port=45679):
        self.send_port = send_port
        self.recv_port = recv_port
        
        # 发送通道
        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # 🌟 接收通道：开启后台守护线程监听 Qt 传来的变量
        self._listener_thread = threading.Thread(target=self._listen_to_qt, daemon=True)
        self._listener_thread.start()
        print(f"[MathLab] 🚀 双向跨进程通信已建立 (Tx:{self.send_port}, Rx:{self.recv_port})")

    def _send(self, cmd: str, **kwargs):
        payload = {"cmd": cmd}
        payload.update(kwargs)
        self.sock_send.sendto(json.dumps(payload).encode('utf-8'), ('127.0.0.1', self.send_port))

    def _listen_to_qt(self):
        """后台静默运行的雷达，接收并解析 Qt 的指令"""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('127.0.0.1', self.recv_port))
            while True:
                try:
                    data, _ = sock.recvfrom(4096)
                    msg = json.loads(data.decode('utf-8'))
                    self._handle_qt_msg(msg)
                except Exception:
                    pass # 守护线程，忽略异常防止崩溃

    def _handle_qt_msg(self, msg: dict):
        """🌟 核心黑科技：直接篡改 IPython 内存变量 🌟"""
        if msg.get("cmd") == "sync_var":
            var_name = msg["name"]
            val = msg["val"]
            try:
                import IPython
                ipython = IPython.get_ipython()
                if ipython is not None:
                    # 强行将变量注入或更新到用户的 Jupyter 全局环境中！
                    ipython.user_ns[var_name] = val
            except Exception:
                pass

    def draw_point(self, name: str, x: float, y: float):
        self._send("draw_point", name=name, x=x, y=y)
        # 初始化时，也在本地内存里存一份
        self._handle_qt_msg({"cmd": "sync_var", "name": f"{name}_x", "val": x})
        self._handle_qt_msg({"cmd": "sync_var", "name": f"{name}_y", "val": y})
        return f"[MathLab] 已生成控制点 {name}({x}, {y})"

    def draw_line(self, name: str, p1_name: str, p2_name: str):
        self._send("draw_line", name=name, p1=p1_name, p2=p2_name)
        return f"[MathLab] 已发送连线指令: {name} ({p1_name} -> {p2_name})"
        
    def clear(self):
        self._send("clear")
        return "[MathLab] 画布已清空"

mlab = MathLabEngine()
