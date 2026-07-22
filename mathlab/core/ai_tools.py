# filepath: mathlab/core/ai_tools.py
import ast
import json
from mathlab.core.jupyter_manager import get_jupyter_sandbox

try:
    from mathlab.utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# ============================================================
#  沙箱画板桥接 (Geometry Canvas Bridge)
#  在 Jupyter 沙箱中注入下列函数，使 Agent 生成的代码能直接
#  调用 draw_point / draw_segment / draw_circle 等 API，
#  在交互几何画板上作图。所有命令收集到 __gbcmds 列表，
#  执行结束后由 execute_math_task 提取并传回 UI 层执行。
# ============================================================
_GEOM_BRIDGE_INJECT = r"""
# === Injected Geometry Canvas Bridge ===
__gbcmds = []

def draw_point(x, y, name=None):
    '''在画板上绘制一个点，返回命令字典。'''
    cmd = {"action": "add_point", "x": float(x), "y": float(y)}
    if name is not None:
        cmd["name"] = str(name)
    __gbcmds.append(cmd)
    return cmd

def draw_segment(p1, p2):
    '''用两点的坐标或 draw_point 返回值绘制线段。'''
    x1, y1 = _extract_xy(p1)
    x2, y2 = _extract_xy(p2)
    cmd = {"action": "add_segment_auto", "x1": x1, "y1": y1, "x2": x2, "y2": y2}
    __gbcmds.append(cmd)
    return cmd

def draw_circle(cx, cy, r):
    '''以 (cx,cy) 为圆心、r 为半径画圆。'''
    cmd = {"action": "add_circle_auto", "cx": float(cx), "cy": float(cy), "r": float(r)}
    __gbcmds.append(cmd)
    return cmd

def draw_line(x1, y1, x2, y2):
    '''过两点画一条无限直线（区别于线段）。'''
    cmd = {"action": "add_line_auto", "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}
    __gbcmds.append(cmd)
    return cmd

def draw_ellipse(cx, cy, rx, ry):
    '''以 (cx,cy) 为中心, rx/ry 为半轴画椭圆。'''
    cmd = {"action": "add_ellipse_auto", "cx": float(cx), "cy": float(cy), "rx": float(rx), "ry": float(ry)}
    __gbcmds.append(cmd)
    return cmd

def draw_polygon(points):
    '''用坐标列表 [(x1,y1),(x2,y2),...] 画多边形。'''
    pts = [(float(p[0]), float(p[1])) for p in points]
    cmd = {"action": "add_polygon_auto", "coords": pts}
    __gbcmds.append(cmd)
    return cmd

def clear_canvas():
    '''清空当前画板。'''
    __gbcmds.append({"action": "clear"})

def _extract_xy(pt):
    if isinstance(pt, dict) and "x" in pt:
        return float(pt["x"]), float(pt["y"])
    return float(pt[0]), float(pt[1])

# 与文档 API 保持一致的别名
add_point = draw_point
add_segment = draw_segment
add_circle = draw_circle
add_line = draw_line
add_ellipse = draw_ellipse
add_polygon = draw_polygon
"""

# 几何画板操控工具的说明书
GEOMETRY_DRAW_TOOL = {
    "type": "function",
    "function": {
        "name": "execute_geometry_draw",
        "description": "当用户在聊天中明确要求【画图、绘制、添加】某种几何图形时，调用此函数在用户的画板上执行绘制操作。注意：如果没有给定坐标，请利用几何常识合理分配数值，使其居中且美观。add_point 必须带 x,y；add_circle 必须带 center 和 radius；add_segment 必须带 p1,p2",
        "parameters": {
            "type": "object",
            "properties": {
                "commands": {
                    "type": "array",
                    "description": "需要按顺序执行的绘图指令数组",
                    "items": {
                        "type": "object",
                        "properties": {
                            "cmd": {
                                "type": "string",
                                "enum": ["add_point", "add_circle", "add_polygon", "add_segment"],
                                "description": "操作类型",
                            },
                            "x": {"type": "number", "description": "点的 X 坐标"},
                            "y": {"type": "number", "description": "点的 Y 坐标"},
                            "name": {"type": "string", "description": "图形的字母标签，如 'A', 'B'"},
                            "radius": {"type": "number", "description": "圆的半径"},
                            "center": {"type": "string", "description": "圆心点的名称引用，如 'A'"},
                            "points": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "多边形顶点的名称列表，如 ['A', 'B', 'C']",
                            },
                            "p1": {"type": "string", "description": "线段起点名称"},
                            "p2": {"type": "string", "description": "线段终点名称"},
                        },
                        "required": ["cmd"],
                    },
                }
            },
            "required": ["commands"],
        },
    },
}

VISUAL_HIGHLIGHT_TOOL = {
    "type": "function",
    "function": {
        "name": "highlight_geometry_elements",
        "description": "苏格拉底教学专用工具：当你想引导用户关注画板上的特定图形（点、线、多边形）时，调用此工具让它们在画板上高亮闪烁，充当你的激光笔。",
        "parameters": {
            "type": "object",
            "properties": {
                "element_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "需要高亮的图形名称列表，例如 ['A', 'B', 'AB', 'Triangle_ABC']",
                },
                "color": {
                    "type": "string",
                    "enum": ["red", "blue", "green", "orange"],
                    "description": "高亮的颜色。如果是警告/纠错用红色，启发思考用橙色或蓝色",
                },
                "reason": {"type": "string", "description": "为什么要高亮这些元素（后台记录，不在 UI 显示）"},
            },
            "required": ["element_names", "color"],
        },
    },
}

QUIZ_GENERATOR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "generate_math_quiz",
        "description": "根据当前的知识点或用户的画布状态，生成一道针对性的数学测试题。",
        "parameters": {
            "type": "object",
            "properties": {
                "knowledge_point": {
                    "type": "string",
                    "description": "本题考查的核心知识点，如 '勾股定理' 或 '导数极值'",
                },
                "question_text": {"type": "string", "description": "题目正文，支持 LaTeX 公式（用 $$ 包裹）"},
                "question_type": {
                    "type": "string",
                    "enum": ["multiple_choice", "fill_in_blank"],
                    "description": "题目类型：选择题 或 填空题",
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "如果是选择题，提供4个选项数组；如果是填空题，此项传空数组",
                },
                "correct_answer": {"type": "string", "description": "标准答案（如 'A' 或具体的计算数值）"},
                "explanation": {"type": "string", "description": "详细的解题思路和步骤"},
            },
            "required": ["knowledge_point", "question_text", "question_type", "correct_answer", "explanation"],
        },
    },
}

AGENT_TRANSFER_TOOL = {
    "type": "function",
    "function": {
        "name": "transfer_to_agent",
        "description": "【核心调度工具】当用户的请求超出了你的专长，或者需要跨部门协作时（例如：你需要画图但没有画笔，你需要出题但你不是考官），必须调用此工具将任务移交给最合适的专家。",
        "parameters": {
            "type": "object",
            "properties": {
                "target_agent": {
                    "type": "string",
                    "enum": ["planner", "general", "geometry", "quiz", "dataviz"],
                    "description": "接手任务的目标专家 ID",
                },
                "handover_notes": {
                    "type": "string",
                    "description": "内部交接说明。请向下一个专家详细描述：当前的上下文是什么？你需要他具体执行什么操作？",
                },
            },
            "required": ["target_agent", "handover_notes"],
        },
    },
}


SUBMIT_TEACHING_PLAN_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_teaching_plan",
        "description": "【教研组长专用】分析用户的数学问题与画布状态，将其拆解为3-5个由浅入深、循序渐进的教学大纲步骤。禁止直接给出最终答案。",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "本次课题的总主题，如'探索圆锥曲线的切线性质'"},
                "steps": {
                    "type": "array",
                    "description": "大纲步骤列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "num": {"type": "integer", "description": "步骤序号 (1, 2, 3...)"},
                            "title": {
                                "type": "string",
                                "description": "本步骤的核心探讨点（如：观察直角边、添加直径辅助线、应用相似三角形定理）",
                            },
                            "hint_for_teacher": {"type": "string", "description": "给授课老师的后台提示，指导该步骤如何教学"},
                        },
                        "required": ["num", "title", "hint_for_teacher"],
                    },
                }
            },
            "required": ["topic", "steps"],
        },
    },
}

AVAILABLE_TOOLS = [
    GEOMETRY_DRAW_TOOL,
    VISUAL_HIGHLIGHT_TOOL,
    QUIZ_GENERATOR_SCHEMA,
    AGENT_TRANSFER_TOOL,
    SUBMIT_TEACHING_PLAN_TOOL,
]


def execute_math_task(code_snippet: str):
    """
    供 AI Agent 调用的沙箱执行入口。
    自动注入几何画板桥接函数（draw_point/section/circle 等），
    并把 Agent 代码中累积的绘图命令随返回值一起传出。
    """
    # 将画板桥接函数注入到用户代码中
    wrapped_code = (
        _GEOM_BRIDGE_INJECT + "\n"
        + code_snippet + "\n"
        + "print('__GEOBRIDGE_CMDS__' + repr(__gbcmds))"
    )
    result = get_jupyter_sandbox().execute_code(wrapped_code)

    # 从输出中分离绘图命令
    output_text = result.get("text", "")
    geom_commands = []
    _MARKER = "__GEOBRIDGE_CMDS__"
    if _MARKER in output_text:
        idx = output_text.index(_MARKER)
        cmds_str = output_text[idx + len(_MARKER):].strip()
        output_text = output_text[:idx].rstrip()
        result["text"] = output_text
        try:
            # BUG 4 修复：使用 ast.literal_eval 替代 eval，只允许字面量解析
            geom_commands = ast.literal_eval(cmds_str)
        except (ValueError, SyntaxError) as e:
            # SUGGESTION 14：添加错误日志
            logger.warning(f"解析几何命令失败: {cmds_str[:200]} - {e}")

    tb = result.get("traceback") or []
    error_text = "\n".join(tb) if isinstance(tb, list) else str(tb)
    return json.dumps({
        "status": result.get("status"),
        "output": output_text,
        "error": error_text if result.get("status") == "error" else None,
        "geom_commands": geom_commands,
    })
