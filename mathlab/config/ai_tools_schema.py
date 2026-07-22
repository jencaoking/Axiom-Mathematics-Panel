# filepath: mathlab/config/ai_tools_schema.py

# 1. 魔法画笔工具：允许 AI 操作画板
GEOMETRY_DRAW_TOOL = {
    "type": "function",
    "function": {
        "name": "execute_geometry_draw",
        "description": "当用户在聊天中明确要求【画图、绘制、添加】某种几何图形，或在讲解错题需要视觉辅助时，调用此函数在用户的画板上执行绘制操作。",
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
                                "enum": [
                                    "add_point",
                                    "add_circle",
                                    "add_polygon",
                                    "add_segment",
                                ],
                            },
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "name": {
                                "type": "string",
                                "description": "图形标签，如 'A'",
                            },
                            "radius": {"type": "number"},
                            "center": {"type": "string"},
                            "points": {"type": "array", "items": {"type": "string"}},
                            "p1": {"type": "string"},
                            "p2": {"type": "string"},
                        },
                        "required": ["cmd"],
                    },
                }
            },
            "required": ["commands"],
        },
    },
}

# 2. 测验卡片生成器：允许 AI 弹出互动考题
QUIZ_GENERATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "generate_math_quiz",
        "description": "根据当前的知识点或用户的画布状态，生成一道针对性的数学测试题并发送给用户作答。",
        "parameters": {
            "type": "object",
            "properties": {
                "knowledge_point": {
                    "type": "string",
                    "description": "本题考查的核心知识点",
                },
                "question_text": {
                    "type": "string",
                    "description": "题目正文，支持 LaTeX",
                },
                "question_type": {
                    "type": "string",
                    "enum": ["multiple_choice", "fill_in_blank"],
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "选择题的4个选项，填空题为空",
                },
                "correct_answer": {
                    "type": "string",
                    "description": "标准答案（如 'A' 或具体数值）",
                },
                "explanation": {
                    "type": "string",
                    "description": "后台保留的详细解题步骤",
                },
            },
            "required": [
                "knowledge_point",
                "question_text",
                "question_type",
                "correct_answer",
                "explanation",
            ],
        },
    },
}

# 3. 空间发言工具：在画板特定元素旁显示讲解气泡
SPATIAL_SPEAK_TOOL = {
    "type": "function",
    "function": {
        "name": "speak_at_location",
        "description": "空间发言：当你讲解某个具体的几何元素时，调用此工具将你的讲解文字以气泡的形式贴在该元素旁边。",
        "parameters": {
            "type": "object",
            "properties": {
                "target_element": {
                    "type": "string",
                    "description": "画板上的目标元素名称（例如 'A', 'BC', 'Circle_O'）",
                },
                "text": {
                    "type": "string",
                    "description": "要显示在气泡里的简短讲解文字（建议控制在 50 字以内）",
                },
            },
            "required": ["target_element", "text"],
        },
    },
}

# 导出工具集字典，方便按需加载
TOOLS_REGISTRY = {
    "draw": GEOMETRY_DRAW_TOOL,
    "quiz": QUIZ_GENERATOR_TOOL,
    "speak": SPATIAL_SPEAK_TOOL,
}


# 获取完整工具列表的快捷方法
def get_all_tools() -> list:
    return list(TOOLS_REGISTRY.values())
