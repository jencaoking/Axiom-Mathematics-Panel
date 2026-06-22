from mathlab.core.ai_tools import GEOMETRY_DRAW_TOOL, VISUAL_HIGHLIGHT_TOOL, QUIZ_GENERATOR_SCHEMA

class AgentProfile:
    def __init__(self, id, name, icon, system_prompt, tools):
        self.id = id                      # 唯一标识符，如 'geometry'
        self.name = name                  # UI 显示名称
        self.icon = icon                  # UI 图标
        self.system_prompt = system_prompt
        self.tools = tools                # 这个专家专属的工具箱

# --- 预设的专家天团 ---
AGENTS = {
    "general": AgentProfile(
        id="general",
        name="全科助教",
        icon="🟢",
        system_prompt="你是 MathLab 首席助教，负责解答综合数学问题，引导思考。",
        tools=[] # 全科助教只动嘴，不动手
    ),
    "geometry": AgentProfile(
        id="geometry",
        name="几何专家",
        icon="📐",
        system_prompt="你是顶尖的几何学专家。只要用户涉及作图、证明、求面积/角度，你必须优先使用 execute_geometry_draw 或 highlight_geometry_elements 进行视觉化演示。",
        tools=[GEOMETRY_DRAW_TOOL, VISUAL_HIGHLIGHT_TOOL] # 独占画板控制权
    ),
    "quiz": AgentProfile(
        id="quiz",
        name="出题考官",
        icon="📝",
        system_prompt="你是一个严厉的出题考官。根据用户的对话上下文，生成针对性的测试题。",
        tools=[QUIZ_GENERATOR_SCHEMA] # 独占出题权
    )
}

def get_agent(agent_id: str) -> AgentProfile:
    return AGENTS.get(agent_id, AGENTS["general"])
