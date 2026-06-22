from mathlab.core.ai_tools import GEOMETRY_DRAW_TOOL, VISUAL_HIGHLIGHT_TOOL, QUIZ_GENERATOR_SCHEMA, AGENT_TRANSFER_TOOL, SUBMIT_TEACHING_PLAN_TOOL

class AgentProfile:
    def __init__(self, id, name, icon, system_prompt, specific_tools):
        self.id = id                      
        self.name = name                  
        self.icon = icon                  
        self.system_prompt = system_prompt
        # ✨ 魔法注入：每个专家不仅有自己的专属工具，还标配了移交对讲机
        self.tools = specific_tools + [AGENT_TRANSFER_TOOL]

# --- 预设的专家天团 ---
AGENTS = {
    "general": AgentProfile(
        id="general",
        name="全科助教",
        icon="🟢",
        system_prompt="你是首席前台。如果用户要画图或做几何证明，立即 transfer_to_agent 给 geometry；如果要考试测验，立即 transfer_to_agent 给 quiz。",
        specific_tools=[] 
    ),
    "geometry": AgentProfile(
        id="geometry",
        name="几何专家",
        icon="📐",
        system_prompt="你是顶尖的几何学专家。只要用户涉及作图、证明、求面积/角度，你必须优先使用 execute_geometry_draw 或 highlight_geometry_elements 进行视觉化演示。如果用户突然让你出题，请 transfer_to_agent 交给出题考官。",
        specific_tools=[GEOMETRY_DRAW_TOOL, VISUAL_HIGHLIGHT_TOOL] 
    ),
    "quiz": AgentProfile(
        id="quiz",
        name="出题考官",
        icon="📝",
        system_prompt="你是严厉的出题考官。如果你的题目需要配一张几何图，请先构思好题目，然后 transfer_to_agent 把画图需求交给几何专家。",
        specific_tools=[QUIZ_GENERATOR_SCHEMA] 
    ),
    "planner": AgentProfile(
        id="planner",
        name="教研组长",
        icon="🧠",
        system_prompt="你是 MathLab 的教研组长。你的唯一职责是制定教学规划。你必须且只能调用 `submit_teaching_plan` 工具提交大纲。绝对禁止输出任何普通的文本聊天内容！",
        specific_tools=[SUBMIT_TEACHING_PLAN_TOOL]
    )
}

def get_agent(agent_id: str) -> AgentProfile:
    return AGENTS.get(agent_id, AGENTS["general"])
