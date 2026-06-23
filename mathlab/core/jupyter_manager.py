import queue
import threading
from typing import Dict, Any, List
from jupyter_client import KernelManager
from mathlab.core.sandbox_security import is_code_safe

class JupyterSandbox:
    """
    进程级隔离的 Jupyter 执行沙盒
    支持状态保持、超时中断、以及富文本/图像输出捕获
    """
    def __init__(self) -> None:
        self.km = KernelManager(kernel_name='python3')
        self.km.start_kernel()
        self.kc = self.km.client()
        self.kc.start_channels()
        
        # 等待内核启动
        try:
            self.kc.wait_for_ready(timeout=10)
            print("Jupyter 内核已成功启动并在后台待命。")
        except RuntimeError:
            print("警告: Jupyter 内核启动超时。")

    def execute_code(self, code: str, timeout: int = 5) -> Dict[str, Any]:
        """
        同步执行代码并收集所有输出
        """
        # 1. 静态安全检查
        safe, msg = is_code_safe(code)
        if not safe:
            return {"status": "error", "traceback": [msg], "text": "", "images": []}

        # 2. 发送给后台 Jupyter 内核执行
        msg_id = self.kc.execute(code)
        
        output_text = []
        output_images = []
        error_traceback = []
        status = "ok"

        # 3. 阻塞等待并捕获输出 (具备超时熔断机制)
        try:
            while True:
                # 从 iopub 频道获取执行结果
                msg = self.kc.get_iopub_msg(timeout=timeout)
                msg_type = msg['header']['msg_type']
                content = msg['content']

                if msg_type == 'stream':
                    # 捕获 print() 输出
                    output_text.append(content['text'])
                
                elif msg_type == 'execute_result' or msg_type == 'display_data':
                    # 捕获表达式结果或图片 (例如 matplotlib 输出)
                    if 'text/plain' in content['data']:
                        output_text.append(content['data']['text/plain'])
                    if 'image/png' in content['data']:
                        output_images.append(content['data']['image/png']) # 这是一个 Base64 字符串
                
                elif msg_type == 'error':
                    # 捕获代码报错信息
                    status = "error"
                    error_traceback.extend(content['traceback'])
                
                elif msg_type == 'status' and content['execution_state'] == 'idle':
                    # 内核执行完毕并回到空闲状态
                    break
                    
        except queue.Empty:
            status = "timeout"
            error_traceback.append(f"执行超时 (超过 {timeout} 秒被强制中断)。已防止陷入死循环。")
            # 发生严重超时（死循环）时，直接强杀并重启内核
            self.restart_kernel()

        return {
            "status": status,
            "text": "".join(output_text),
            "images": output_images, # 可以直接传给 QPixmap 加载
            "traceback": error_traceback
        }

    def restart_kernel(self) -> None:
        """强杀并重启内核（用于清理内存或打破死循环）"""
        print("正在重启 Jupyter 内核...")
        self.km.restart_kernel(now=True)
        self.kc = self.km.client()
        self.kc.start_channels()
        self.kc.wait_for_ready(timeout=10)

    def shutdown(self) -> None:
        self.kc.stop_channels()
        self.km.shutdown_kernel(now=True)

# 全局单例沙盒引擎
jupyter_sandbox = JupyterSandbox()
