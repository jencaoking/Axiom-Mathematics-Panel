import logging
import threading
import json
import os
from mathlab.core.ai_tools import AVAILABLE_TOOLS

logger = logging.getLogger(__name__)


class AgentInfo:
    """轻量级专家描述对象，供 UI 层查询专家身份与能力。"""

    def __init__(self, agent_id, name, icon, system_prompt, tools=None):
        self.id = agent_id
        self.name = name
        self.icon = icon
        self.system_prompt = system_prompt
        self.tools = tools if tools is not None else []


# 全局专家名片表：id -> AgentInfo
_AGENT_PROFILES = {
    "planner": AgentInfo(
        agent_id="planner",
        name="教研组长",
        icon="🎓",
        system_prompt=(
            "你是一个【数学教研组长 (PlannerAgent)】。\n"
            "你的核心职责是分析用户的数学问题，将其拆解为 3-5 个由浅入深、循序渐进的教学步骤，\n"
            "然后协调解析几何专家和数据可视化专家共同完成教学。\n"
            "教学过程中禁止直接给出最终答案——要通过引导式提问让学生自己发现规律。"
        ),
        tools=AVAILABLE_TOOLS,
    ),
    "general": AgentInfo(
        agent_id="general",
        name="通用数学助手",
        icon="🧠",
        system_prompt=(
            "你是一个资深的数学科研助手与高级 Python 程序员。\n"
            "请通过 Thought, Action, Observation 闭环结构的计算过程解决问题。"
        ),
        tools=AVAILABLE_TOOLS,
    ),
    "geometry": AgentInfo(
        agent_id="geometry",
        name="解析几何专家",
        icon="📐",
        system_prompt=(
            "你是一个【2D 解析几何与代数专家】。\n"
            "你的任务是编写 Python 代码，调用 numpy 和 scipy 解决数学问题，"
            "并利用现有的全局几何画板环境绘图。\n"
            "请通过 Thought, Action, Observation 闭环进行。"
        ),
        tools=AVAILABLE_TOOLS,
    ),
    "quiz": AgentInfo(
        agent_id="quiz",
        name="出题考官",
        icon="📝",
        system_prompt=(
            "你是一个严谨的数学出题专家。\n"
            "根据用户提供的知识点或画板状态，设计难度适中、考查点明确的试题，"
            "并给出标准答案与详细解析。"
        ),
        tools=AVAILABLE_TOOLS,
    ),
    "dataviz": AgentInfo(
        agent_id="dataviz",
        name="数据可视化专家",
        icon="📊",
        system_prompt=(
            "你是一个【高级数据可视化专家 (DataVizAgent)】。\n"
            "你的任务是根据用户的需求，生成极具科技感、配色高级的交互式图表，"
            "且必须使用环境内置的渲染桥接器渲染。"
        ),
        tools=AVAILABLE_TOOLS,
    ),
}


def get_agent(agent_id: str) -> AgentInfo:
    """根据专家 ID 返回其描述对象，未知 ID 回退到 general。"""
    if not agent_id:
        return _AGENT_PROFILES["general"]
    key = agent_id.lower()
    return _AGENT_PROFILES.get(key, _AGENT_PROFILES["general"])


def list_agents():
    """返回所有已注册的专家名片。"""
    return list(_AGENT_PROFILES.values())


class AgentRegistry:
    def __init__(self, ai_manager, student_model=None):
        self.ai_manager = ai_manager
        self.student_model = student_model  # 学生认知模型（自适应学习）
        self.agents = {}  # 存放所有已注册的专家 Agent
        self._execution_timeout = 300  # [修复] 整体执行超时时间（秒）
        # 结构化通信协议：消息总线与路由器
        from mathlab.core.agent_message import get_message_bus, get_message_router

        self.message_bus = get_message_bus()
        self.message_router = get_message_router()
        self.message_router.agent_registry = self

    def register_agent(self, name, description, agent_instance):
        """注册一个专家 Agent 及其能力描述"""
        if name in self.agents:
            logger.warning(f"⚠️ 专家 {name} 已存在，正在被覆盖注册！")

        self.agents[name] = {"description": description, "instance": agent_instance}

        # 注册到消息总线，为 Agent 创建消息邮箱
        self.message_router.register_agent(name, agent_instance)

        # 绑定消息总线到 Agent 实例，使其可以主动发送消息
        if hasattr(agent_instance, "set_message_bus"):
            agent_instance.set_message_bus(self.message_bus)
            agent_instance.agent_id = name

        # 修复 Bug 2: 尝试打通动态注册系统与静态名片表 (_AGENT_PROFILES)
        matched_key = None
        for k in _AGENT_PROFILES.keys():
            if k in name.lower():
                matched_key = k
                break
        if matched_key:
            _AGENT_PROFILES[matched_key].system_prompt = getattr(
                agent_instance,
                "system_prompt",
                _AGENT_PROFILES[matched_key].system_prompt,
            )

        logger.info(f"🔌 [Agent Registry] 已注册专家: {name}")

    def unregister_agent(self, name):
        """运行时卸载一个已注册的专家 Agent"""
        if name not in self.agents:
            logger.warning(f"⚠️ 专家 {name} 未注册，无法卸载")
            return False

        # 尝试清理 agent 实例的资源
        instance = self.agents[name].get("instance")
        if instance and hasattr(instance, "cleanup"):
            try:
                instance.cleanup()
            except Exception as e:
                logger.warning(f"清理 Agent {name} 资源时出错: {e}")

        # 从消息总线注销
        self.message_bus.unsubscribe(name)

        del self.agents[name]
        # 从静态名片表中移除（仅限动态添加的）
        if name.lower() in _AGENT_PROFILES and _AGENT_PROFILES[name.lower()].id not in (
            "planner",
            "general",
            "geometry",
            "quiz",
            "dataviz",
        ):
            del _AGENT_PROFILES[name.lower()]

        logger.info(f"🔌 [Agent Registry] 已卸载专家: {name}")
        return True

    def load_agent_from_config(self, config: dict):
        """从配置字典动态创建并注册一个新专家 Agent，无需重启应用。

        配置格式：
        {
            "name": "CustomAgent",
            "description": "专家能力描述",
            "system_prompt": "你是...",
            "model_override": "gpt-4o",          # 可选，指定使用的模型
            "icon": "🔬",                         # 可选，UI 图标
            "display_name": "自定义专家",           # 可选，UI 显示名
            "max_memory_mb": 256,                 # 可选，资源限制
            "max_time_seconds": 60,               # 可选
            "max_cpu_percent": 80,                # 可选
            "max_steps": 5                        # 可选，ReAct 最大重试次数
        }
        """
        from mathlab.core.ai_manager import BaseMathAgent, ResourceConfig

        name = config.get("name", "")
        if not name:
            raise ValueError("Agent 配置必须包含 'name' 字段")

        if name in self.agents:
            logger.warning(f"⚠️ 专家 {name} 已存在，将被覆盖")

        description = config.get("description", "自定义专家")
        system_prompt = config.get(
            "system_prompt",
            "你是一个数学科研助手。请通过 Thought, Action, Observation 闭环解决问题。",
        )
        model_override = config.get("model_override")

        # 构建资源限制配置
        resource_config = ResourceConfig(
            max_memory_mb=config.get("max_memory_mb", 512),
            max_time_seconds=config.get("max_time_seconds", 60),
            max_cpu_percent=config.get("max_cpu_percent", 80),
            max_steps=config.get("max_steps", 5),
        )

        # 动态创建 Agent 实例（基于 BaseMathAgent），注入学生模型
        agent = BaseMathAgent(
            self.ai_manager,
            model_override=model_override,
            resource_config=resource_config,
            student_model=self.student_model,
        )
        agent.system_prompt = system_prompt

        # 注册到路由系统
        self.register_agent(
            name=name,
            description=description,
            agent_instance=agent,
        )

        # 自动创建 UI 名片
        profile_key = name.lower()
        _AGENT_PROFILES[profile_key] = AgentInfo(
            agent_id=profile_key,
            name=config.get("display_name", name),
            icon=config.get("icon", "🤖"),
            system_prompt=system_prompt,
            tools=AVAILABLE_TOOLS,
        )

        logger.info(f"🔌 [Agent Registry] 动态加载专家成功: {name}")
        return name

    def load_agent_from_file(self, config_path: str):
        """从 JSON 配置文件热加载一个新专家 Agent。

        文件格式同 load_agent_from_config 的 config 字典。
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Agent 配置文件不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        return self.load_agent_from_config(config)

    def load_agents_from_directory(self, dir_path: str):
        """从目录批量热加载所有 JSON 格式的 Agent 配置文件。

        Args:
            dir_path: 包含 *.json Agent 配置文件的目录路径

        Returns:
            (loaded_names, failed_names) 已加载和加载失败的 Agent 名称列表
        """
        loaded: list[str] = []
        failed: list[str] = []

        if not os.path.isdir(dir_path):
            logger.warning(f"Agent 配置目录不存在: {dir_path}")
            return loaded, failed

        for filename in os.listdir(dir_path):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(dir_path, filename)
            try:
                name = self.load_agent_from_file(filepath)
                loaded.append(name)
            except Exception as e:
                logger.error(f"加载 Agent 配置失败 ({filename}): {e}")
                failed.append(filename)

        logger.info(f"🔌 批量热加载完成: 成功 {len(loaded)} 个, 失败 {len(failed)} 个")
        return loaded, failed

    def list_registered_agents(self):
        """返回所有已注册专家的详细信息，供 UI 展示"""
        result = []
        for name, info in self.agents.items():
            instance = info["instance"]
            model = getattr(
                instance,
                "_get_effective_model",
                lambda: getattr(instance, "model", "unknown"),
            )()
            result.append(
                {
                    "name": name,
                    "description": info["description"],
                    "model": model,
                    "resource_config": getattr(instance, "resource_config", None),
                }
            )
        return result

    def route_and_execute(
        self, user_prompt, on_thought_cb, on_code_cb, on_finish_cb, on_geom_cb=None
    ):
        """
        核心路由逻辑：分类 -> 派发 -> 执行

        [修复] 添加整体执行超时控制，防止 LLM 响应慢导致系统阻塞
        """
        if not self.agents:
            if on_thought_cb:
                on_thought_cb("❌ 系统中没有可用的专家 Agent。")
            if on_finish_cb:
                on_finish_cb(False, "")
            return

        # 1. 构建动态的路由 Prompt，列出所有可用专家
        agent_descriptions = "\n".join(
            [f"- {name}: {info['description']}" for name, info in self.agents.items()]
        )

        # BUG 10 修复：使用三引号嵌套避免用户输入中的引号破坏格式
        router_prompt = f"""你是一个高级任务调度路由大脑。
请分析用户的需求：{user_prompt}
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
                max_tokens=50,
                timeout=30,
            )

            content = response.choices[0].message.content
            selected_agent_name = content.strip() if content else ""

            # 清理可能携带的标点符号和空格
            selected_agent_name = selected_agent_name.strip(" '\"\n\t*.,")

            # 3. 容错回退机制：优先回退给教研组长（能拆解任何任务），其次 Geometry
            if selected_agent_name not in self.agents:
                fallback = (
                    "PlannerAgent"
                    if "PlannerAgent" in self.agents
                    else (
                        "GeometryAgent"
                        if "GeometryAgent" in self.agents
                        else (list(self.agents.keys())[0] if self.agents else None)
                    )
                )
                if not fallback:
                    raise RuntimeError("系统中没有任何已注册的专家。")
                if on_thought_cb:
                    on_thought_cb(
                        f"⚠️ 路由识别为 {selected_agent_name} 但未找到该专家，默认回退给 {fallback}。"
                    )
                selected_agent_name = fallback
            else:
                if on_thought_cb:
                    on_thought_cb(
                        f"🎯 意图锁定！已将任务移交至领域专家：【{selected_agent_name}】"
                    )

            # 4. 真正移交控制权，启动该专家的 ReAct 推理闭环
            # [修复] 添加超时控制，防止 LLM 响应慢导致系统阻塞
            expert_agent = self.agents[selected_agent_name]["instance"]

            result_container = {"finished": False, "error": None}

            def _execute_with_timeout():
                try:
                    expert_agent.solve_problem(
                        user_prompt, on_thought_cb, on_code_cb, on_finish_cb, on_geom_cb
                    )
                except Exception as e:
                    result_container["error"] = e
                finally:
                    result_container["finished"] = True

            exec_thread = threading.Thread(target=_execute_with_timeout, daemon=True)
            exec_thread.start()
            exec_thread.join(timeout=self._execution_timeout)

            if not result_container["finished"]:
                if on_thought_cb:
                    on_thought_cb(
                        f"⏰ 专家执行超时（超过 {self._execution_timeout} 秒），已强制终止。"
                    )
                if on_finish_cb:
                    on_finish_cb(False, f"执行超时（{self._execution_timeout}秒）")
            elif result_container["error"]:
                raise result_container["error"]

        except Exception as e:
            if on_thought_cb:
                on_thought_cb(f"❌ 路由中枢发生故障: {e}")
            if on_finish_cb:
                on_finish_cb(False, "")
