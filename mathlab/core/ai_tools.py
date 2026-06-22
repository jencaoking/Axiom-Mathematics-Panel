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

AVAILABLE_TOOLS = [GEOMETRY_DRAW_TOOL, QUIZ_GENERATOR_SCHEMA]
