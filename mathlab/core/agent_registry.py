import re
import json

class AgentRegistry:
    def __init__(self, ai_manager):
        self.ai_manager = ai_manager
        self.agents = {}  # 存放所有已注册的专家 Agent

    def register_agent(self, name, description, agent_instance):
        """注册一个专家 Agent 及其能力描述"""
        self.agents[name] = {
            "description": description,
            "instance": agent_instance
        }
        print(f"🔌 [Agent Registry] 已挂载领域专家: {name}")

    def route_and_execute(self, user_prompt, on_thought_cb, on_code_cb, on_finish_cb):
        """
        核心路由逻辑：分类 -> 派发 -> 执行
        """
        if not self.agents:
            if on_thought_cb:
                on_thought_cb("❌ 系统中没有可用的专家 Agent。")
            if on_finish_cb:
                on_finish_cb(False, "")
            return

        # 1. 构建动态的路由 Prompt，列出所有可用专家
        agent_descriptions = "\n".join([f"- {name}: {info['description']}" for name, info in self.agents.items()])
        
        router_prompt = f"""你是一个高级任务调度路由大脑。
请分析用户的需求：“{user_prompt}”。
根据以下可用的专家 Agent，决定将任务派发给谁最合适：
{agent_descriptions}

规则：你必须且只能返回专家的名字，不要输出任何多余的字符或标点。"""

        if on_thought_cb:
            on_thought_cb("🧠 路由大脑正在分析意图，寻找最合适的专家...")

        try:
            # 2. 使用极低的 Temperature 获取稳定的分类结果
            response = self.ai_manager.client.chat.completions.create(
                model=self.ai_manager.current_model,
                messages=[{"role": "user", "content": router_prompt}],
                temperature=0.0,
                max_tokens=20
            )
            
            selected_agent_name = response.choices[0].message.content.strip()
            
            # 清理可能携带的标点符号
            selected_agent_name = re.sub(r'[^a-zA-Z0-9_]', '', selected_agent_name)

            # 3. 容错回退机制
            if selected_agent_name not in self.agents:
                if on_thought_cb:
                    on_thought_cb(f"⚠️ 路由识别为 {selected_agent_name} 但未找到该专家，默认回退给 GeometryAgent。")
                selected_agent_name = "GeometryAgent" # 默认兜底专家
            else:
                if on_thought_cb:
                    on_thought_cb(f"🎯 意图锁定！已将任务移交至领域专家：【{selected_agent_name}】")

            # 4. 真正移交控制权，启动该专家的 ReAct 推理闭环
            expert_agent = self.agents[selected_agent_name]["instance"]
            expert_agent.solve_problem(user_prompt, on_thought_cb, on_code_cb, on_finish_cb)

        except Exception as e:
            if on_thought_cb:
                on_thought_cb(f"❌ 路由中枢发生故障: {e}")
            if on_finish_cb:
                on_finish_cb(False, "")
