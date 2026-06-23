import json

def append_to_file(filepath, content):
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write('\n' + content + '\n')

# 1. ai_tools.py
ai_tools_code = """
import json
from mathlab.core.jupyter_manager import jupyter_sandbox

def execute_math_task(code_snippet: str):
    \"\"\"
    这是一个供 AI Agent 调用的函数工具。
    Agent 会自动调用此函数来执行 Python 代码，并获取结果。
    \"\"\"
    # 将代码块交给 Jupyter 沙盒执行
    result = jupyter_sandbox.execute_code(code_snippet)
    
    # 将执行结果打包返回给 AI
    return json.dumps({
        "status": result["status"],
        "output": result["text"],
        "error": "\\n".join(result["traceback"]) if result["status"] == "error" else None
    })
"""
append_to_file('mathlab/core/ai_tools.py', ai_tools_code)

# 2. ai_manager.py
ai_manager_code = """
from mathlab.core.ai_tools import execute_math_task

class MathAgent:
    def __init__(self, model="gpt-4o"):
        self.model = model
        self.max_retries = 3

    def _llm_generate_code(self, prompt):
        # 这是一个供参考的占位符，实际可以调用全局的 AIManager.ask 进行同步等待
        # 此处使用简单的桩代码演示
        # 真正使用时可以通过 self.client 调用 openai 接口
        return \"\"\"
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 2, 100)
y = np.sin(x**2)
plt.plot(x, y)
plt.show()

# 计算面积
from scipy.integrate import quad
area, _ = quad(lambda x: np.sin(x**2), 0, 2)
print(f"面积为: {area}")
\"\"\"

    def solve_problem(self, user_prompt: str):
        print(f"Agent 思考中: {user_prompt}")
        
        # 初始 Prompt：设定 Agent 的角色为数学专家
        prompt = f\"\"\"你是一个高级数学科研助手。请编写 Python 代码解决以下问题: {user_prompt}
        规则: 
        1. 使用 sympy 和 matplotlib 库。
        2. 只返回可执行的代码块，不要包含 Markdown 解释。
        \"\"\"
        
        for attempt in range(self.max_retries):
            # 1. 向 LLM 请求代码
            code = self._llm_generate_code(prompt)
            
            # 2. 执行代码
            execution_result = json.loads(execute_math_task(code))
            
            if execution_result["status"] == "ok":
                print("任务执行成功！")
                return {"status": "ok", "code": code, "result": execution_result["output"]}
            else:
                # 3. 自我修正循环：将错误反馈给 AI，要求修正
                print(f"代码报错 (第 {attempt+1} 次尝试), 正在修正...")
                prompt = f"之前的代码报错了: {execution_result['error']}。请修正它并重新提供代码。"
        
        return {"status": "failed", "error": "超出最大重试次数"}
"""
append_to_file('mathlab/core/ai_manager.py', ai_manager_code)

print("Appended successfully.")
