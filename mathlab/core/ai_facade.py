"""统一 AI 范式门面 (AI Facade)。

将项目中两套 AI 交互范式统一到单一入口，明确职责边界：

范式 A — Function Calling (AIEngineWorker)：
    适用于简单工具调用场景（画图、出题、解释代码）。
    通过 OpenAI Function Calling 流式返回工具调用指令，
    由 UI 直接执行，延迟低、确定性高。

范式 B — Agent 代码生成 (BaseMathAgent / AgentRegistry)：
    适用于复杂多步推理场景（解题、证明、教学规划）。
    通过代码生成 + 沙箱执行 + RAG 技能检索循环完成，
    具备自我反思与纠错重试能力。

使用方式：
    facade = AIFacade(ai_manager, agent_registry)
    facade.route_request(user_prompt, context, callbacks...)
"""
from enum import Enum
from typing import Callable, Optional

from mathlab.utils.logger import get_logger

logger = get_logger(__name__)


class AITaskType(Enum):
    """AI 任务类型分类，决定使用哪种范式。"""
    SIMPLE_TOOL_CALL = "simple_tool_call"
    COMPLEX_REASONING = "complex_reasoning"


class AIFacade:
    """统一 AI 范式门面。

    根据用户意图自动路由到 Function Calling 或 Agent 代码生成范式，
    消除两套范式共存导致的架构混淆。
    """

    # 触发 Agent 代码生成范式的关键词
    _AGENT_KEYWORDS = frozenset({
        '证明', '求解', '推导', '计算', '化简', '积分', '微分',
        '极限', '方程组', '证明题', '教学', '讲解', '步骤',
        'prove', 'solve', 'derive', 'calculate', 'simplify',
        'integrate', 'differentiate', 'limit', 'teach', 'explain step',
    })

    # 触发 Function Calling 范式的关键词
    _TOOL_KEYWORDS = frozenset({
        '画', '绘制', '画图', '作图', '出题', '测验', ' quiz',
        '解释代码', '说明代码', 'draw', 'plot', 'render',
    })

    def __init__(self, ai_manager, agent_registry=None, student_model=None):
        self.ai_manager = ai_manager
        self.agent_registry = agent_registry
        self.student_model = student_model
        # [修复] 初始化时检查 agent_registry，提前发现问题
        if agent_registry is None:
            logger.warning("AIFacade 初始化时 agent_registry 为 None，复杂推理任务将不可用")

    def classify_intent(self, user_prompt: str) -> AITaskType:
        """根据用户输入分类任务类型。

        Args:
            user_prompt: 用户输入文本。

        Returns:
            AITaskType.COMPLEX_REASONING 或 AITaskType.SIMPLE_TOOL_CALL。
        """
        prompt_lower = user_prompt.lower()

        agent_score = sum(1 for kw in self._AGENT_KEYWORDS if kw in prompt_lower)
        tool_score = sum(1 for kw in self._TOOL_KEYWORDS if kw in prompt_lower)

        if agent_score > tool_score:
            return AITaskType.COMPLEX_REASONING
        return AITaskType.SIMPLE_TOOL_CALL

    def route_request(
        self,
        user_prompt: str,
        canvas_state: str = None,
        on_chunk: Optional[Callable] = None,
        on_tool: Optional[Callable] = None,
        on_state_change: Optional[Callable] = None,
        on_finish: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_thought: Optional[Callable] = None,
        on_code: Optional[Callable] = None,
        on_geom_commands: Optional[Callable] = None,
    ) -> AITaskType:
        """统一入口：根据用户意图自动路由到合适的 AI 范式。

        Args:
            user_prompt: 用户输入。
            canvas_state: 画板状态 JSON（可选）。
            on_chunk: 文本流式回调（范式 A）。
            on_tool: 工具调用回调（范式 A）。
            on_state_change: 状态变更回调（范式 A）。
            on_finish: 完成回调。
            on_error: 错误回调。
            on_thought: Agent 思考过程回调（范式 B）。
            on_code: Agent 代码生成回调（范式 B）。
            on_geom_commands: Agent 几何命令回调（范式 B）。

        Returns:
            实际使用的任务类型。
        """
        task_type = self.classify_intent(user_prompt)
        logger.info("AI 路由: prompt='%s...' → %s", user_prompt[:30], task_type.value)

        # 记录学生互动（自适应学习：即使是简单工具调用也记录）
        self._record_student_interaction(user_prompt)

        if task_type == AITaskType.SIMPLE_TOOL_CALL:
            self._run_function_calling(
                user_prompt, canvas_state,
                on_chunk, on_tool, on_state_change, on_finish, on_error,
            )
        else:
            self._run_agent_loop(
                user_prompt,
                on_thought, on_code, on_geom_commands, on_finish, on_error,
            )

        return task_type

    def _record_student_interaction(self, user_prompt: str):
        """记录学生互动到认知模型（自适应学习）。"""
        if not self.student_model:
            return
        try:
            from mathlab.core.student_model import AdaptiveEngine
            engine = AdaptiveEngine(self.student_model)
            interaction_type = engine.classify_interaction(user_prompt)
            knowledge_point = engine.extract_knowledge_point(user_prompt)
            self.student_model.record_interaction(
                interaction_type=interaction_type,
                knowledge_point=knowledge_point,
                prompt_text=user_prompt,
            )
        except Exception as e:
            logger.error(f"记录学生互动失败: {e}")

    def _run_function_calling(
        self,
        user_prompt: str,
        canvas_state: str,
        on_chunk, on_tool, on_state_change, on_finish, on_error,
    ):
        """范式 A：通过 AIEngineWorker + Function Calling 处理简单工具调用。"""
        from mathlab.core.ai_tools import AVAILABLE_TOOLS

        tools = AVAILABLE_TOOLS
        system_prompt = "你是 MathLab 数学助手。根据用户请求调用合适的工具函数。"

        self.ai_manager.ask(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            tools=tools,
            canvas_state=canvas_state,
            on_state_change=on_state_change,
            on_chunk=on_chunk,
            on_tool=on_tool,
            on_finish=on_finish,
            on_error=on_error,
        )

    def _run_agent_loop(
        self,
        user_prompt: str,
        on_thought, on_code, on_geom_commands, on_finish, on_error,
    ):
        """范式 B：通过 AgentRegistry + 代码生成处理复杂多步推理。"""
        if not self.agent_registry:
            if on_error:
                on_error("Agent 系统未初始化，无法处理复杂推理任务。")
            return

        # AgentRegistry.route_and_execute 是异步的，
        # 通过 AgentUIBridge 的信号回调通知 UI
        try:
            self.agent_registry.route_and_execute(
                user_prompt,
                on_thought=on_thought,
                on_code=on_code,
                on_geom_commands=on_geom_commands,
                on_finish=on_finish,
                on_error=on_error,
            )
        except Exception as e:
            logger.error("Agent 执行失败: %s", e, exc_info=True)
            if on_error:
                on_error(str(e))
