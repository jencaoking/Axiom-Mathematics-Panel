# filepath: mathlab/core/ai_tools.py

# 几何画板操控工具的说明书
GEOMETRY_DRAW_TOOL = {
    "type": "function",
    "function": {
        "name": "execute_geometry_draw",
        "description": "当用户在聊天中明确要求【画图、绘制、添加】某种几何图形时，调用此函数在用户的画板上执行绘制操作。注意：如果没有给定坐标，请利用几何常识合理分配数值，使其居中且美观。",
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
                                "description": "操作类型"
                            },
                            "x": {"type": "number", "description": "点的 X 坐标"},
                            "y": {"type": "number", "description": "点的 Y 坐标"},
                            "name": {"type": "string", "description": "图形的字母标签，如 'A', 'B'"},
                            "radius": {"type": "number", "description": "圆的半径"},
                            "center": {"type": "string", "description": "圆心点的名称引用，如 'A'"},
                            "points": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "多边形顶点的名称列表，如 ['A', 'B', 'C']"
                            },
                            "p1": {"type": "string", "description": "线段起点名称"},
                            "p2": {"type": "string", "description": "线段终点名称"}
                        },
                        "required": ["cmd"]
                    }
                }
            },
            "required": ["commands"]
        }
    }
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
                    "description": "需要高亮的图形名称列表，例如 ['A', 'B', 'AB', 'Triangle_ABC']"
                },
                "color": {
                    "type": "string",
                    "enum": ["red", "blue", "green", "orange"],
                    "description": "高亮的颜色。如果是警告/纠错用红色，启发思考用橙色或蓝色"
                },
                "reason": {
                    "type": "string",
                    "description": "为什么要高亮这些元素（后台记录，不在 UI 显示）"
                }
            },
            "required": ["element_names", "color"]
        }
    }
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
                    "description": "本题考查的核心知识点，如 '勾股定理' 或 '导数极值'"
                },
                "question_text": {
                    "type": "string",
                    "description": "题目正文，支持 LaTeX 公式（用 $$ 包裹）"
                },
                "question_type": {
                    "type": "string",
                    "enum": ["multiple_choice", "fill_in_blank"],
                    "description": "题目类型：选择题 或 填空题"
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "如果是选择题，提供4个选项数组；如果是填空题，此项传空数组"
                },
                "correct_answer": {
                    "type": "string",
                    "description": "标准答案（如 'A' 或具体的计算数值）"
                },
                "explanation": {
                    "type": "string",
                    "description": "详细的解题思路和步骤"
                }
            },
            "required": ["knowledge_point", "question_text", "question_type", "correct_answer", "explanation"]
        }
    }
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
                    "enum": ["geometry", "quiz", "general"],
                    "description": "接手任务的目标专家 ID"
                },
                "handover_notes": {
                    "type": "string",
                    "description": "内部交接说明。请向下一个专家详细描述：当前的上下文是什么？你需要他具体执行什么操作？"
                }
            },
            "required": ["target_agent", "handover_notes"]
        }
    }
}

AVAILABLE_TOOLS = [GEOMETRY_DRAW_TOOL, QUIZ_GENERATOR_SCHEMA, VISUAL_HIGHLIGHT_TOOL, AGENT_TRANSFER_TOOL]

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
                            "title": {"type": "string", "description": "本步骤的核心探讨点（如：观察直角边、添加直径辅助线、应用相似三角形定理）"},
                            "hint_for_teacher": {"type": "string", "description": "给授课老师的后台提示，指导该步骤如何教学"}
                        },
                        "required": ["num", "title", "hint_for_teacher"]
                    }
                }
            },
            "required": ["topic", "steps"]
        }
    }
}
