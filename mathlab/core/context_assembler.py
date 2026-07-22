import re
from mathlab.core.prompt_manager import PromptManager


class ContextAssembler:
    """
    动态上下文组装引擎：按需注入背景知识，保持大模型注意力极度专注
    """

    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
        # 获取 YAML 中的碎片库
        self.snippets = self.prompt_manager._prompts.get("snippets", {})

    def build_dynamic_system_prompt(self, base_system_prompt: str, user_text: str, canvas_tracker) -> str:
        addons = []

        # 规则 1：是否需要注入 LaTeX 规则？
        # 如果用户提问包含计算、证明、解释等字眼，大概率需要数学公式
        if re.search(r"(为什么|解释|证明|公式|计算|求|多大)", user_text):
            if "latex_rules" in self.snippets:
                addons.append(self.snippets["latex_rules"])

        # 规则 2：是否需要注入画板 JSON 状态？
        # 绝不盲目注入。只有当画板不是空的，且用户提及相关词汇时才注入。
        canvas_json = canvas_tracker.current_state_json if canvas_tracker else "{}"
        is_canvas_empty = canvas_json in [
            "{}",
            '{"points": {}, "lines": [], "circles": [], "polygons": []}',
        ]

        if not is_canvas_empty:
            # 宽泛的几何匹配词
            if re.search(r"(图|这|怎么画|面积|点|线|圆|三角形|角度|距离|相交)", user_text):
                snippet = self.snippets.get("canvas_state", "").replace("{canvas_json}", canvas_json)
                addons.append(snippet)

                # 规则 3：如果有高级的本地启发式结果（Insights），一并注入
                insights = getattr(canvas_tracker, "current_insights", "")
                if insights:
                    insight_snippet = self.snippets.get("local_insights", "").replace("{insights}", insights)
                    addons.append(insight_snippet)

        # 规则 4：是否需要注入软件操作指南？
        if re.search(r"(怎么操作|快捷键|帮助|怎么清空|能干嘛)", user_text):
            shortcuts = self.snippets.get("system_shortcuts", "")
            if shortcuts:
                addons.append(shortcuts)

        # 组装最终的 System Prompt
        if addons:
            return base_system_prompt + "\n\n" + "\n\n".join(addons)
        return base_system_prompt
