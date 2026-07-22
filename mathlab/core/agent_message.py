"""结构化 Agent 通信协议 (Agent Communication Protocol, ACP)。

替代原有基于回调函数的 ad-hoc 通信方式，提供：
1. AgentMessage — 标准消息格式（发送方/接收方/类型/内容/元数据）
2. MessageBus — 线程安全的发布-订阅消息总线
3. MessageRouter — 消息路由层，支持点对点和广播通信
4. MessageHistory — 消息历史记录，支持审计和调试

设计原则：
- 向后兼容：保留原有回调接口，消息总线为增量功能
- 线程安全：所有消息操作使用锁保护
- 可扩展：支持自定义消息类型和处理器
- 可观测：消息历史记录支持调试和审计
"""

import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Deque, cast

from mathlab.utils.logger import get_logger

logger = get_logger(__name__)


class MessageType(Enum):
    """Agent 间消息类型。"""

    # 任务相关
    TASK_REQUEST = "task_request"  # 请求执行任务
    TASK_RESULT = "task_result"  # 任务执行结果
    TASK_PROGRESS = "task_progress"  # 任务进度更新
    TASK_ERROR = "task_error"  # 任务执行错误

    # 查询相关
    QUERY = "query"  # 向另一个 Agent 查询信息
    RESPONSE = "response"  # 查询响应

    # 协作相关
    COLLABORATION_REQUEST = "collab_request"  # 请求协作
    COLLABORATION_ACCEPT = "collab_accept"  # 接受协作
    COLLABORATION_REJECT = "collab_reject"  # 拒绝协作

    # 通知相关
    NOTIFICATION = "notification"  # 通用通知
    BROADCAST = "broadcast"  # 广播消息

    # 状态相关
    STATUS_UPDATE = "status_update"  # Agent 状态更新
    HEARTBEAT = "heartbeat"  # 心跳信号


class MessagePriority(Enum):
    """消息优先级。"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class AgentMessage:
    """标准 Agent 通信消息。

    Attributes:
        id: 消息唯一标识（自动生成 UUID）
        sender_id: 发送方 Agent ID
        receiver_id: 接收方 Agent ID（"broadcast" 表示广播）
        msg_type: 消息类型
        content: 消息内容（字符串或字典）
        metadata: 元数据（如知识点、认知层级、步骤编号等）
        priority: 消息优先级
        timestamp: 消息创建时间戳
        reply_to: 回复的消息 ID（如果是回复消息）
        conversation_id: 会话 ID（关联同一轮对话的所有消息）
    """

    sender_id: str
    receiver_id: str
    msg_type: MessageType
    content: Any = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    reply_to: Optional[str] = None
    conversation_id: Optional[str] = None

    def to_dict(self) -> dict:
        """序列化为字典。"""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "msg_type": self.msg_type.value,
            "content": (self.content if isinstance(self.content, (str, int, float, dict, list)) else str(self.content)),
            "metadata": self.metadata,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "reply_to": self.reply_to,
            "conversation_id": self.conversation_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentMessage":
        """从字典反序列化。"""
        return cls(
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            msg_type=MessageType(data.get("msg_type", "notification")),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            priority=MessagePriority(data.get("priority", 1)),
            timestamp=data.get("timestamp", time.time()),
            id=data.get("id", str(uuid.uuid4())[:8]),
            reply_to=data.get("reply_to"),
            conversation_id=data.get("conversation_id"),
        )

    @classmethod
    def create_task_request(
        cls,
        sender_id: str,
        receiver_id: str,
        task_prompt: str,
        step_num: Optional[int] = None,
        cognitive_level: Optional[str] = None,
        conversation_id: Optional[str] = None,
        **extra_metadata,
    ) -> "AgentMessage":
        """快捷创建任务请求消息。"""
        metadata = {
            "step_num": step_num,
            "cognitive_level": cognitive_level,
            **extra_metadata,
        }
        return cls(
            sender_id=sender_id,
            receiver_id=receiver_id,
            msg_type=MessageType.TASK_REQUEST,
            content=task_prompt,
            metadata=metadata,
            conversation_id=conversation_id,
        )

    @classmethod
    def create_task_result(
        cls,
        sender_id: str,
        receiver_id: str,
        success: bool,
        code: str = "",
        result: str = "",
        geom_commands: list = None,
        reply_to: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> "AgentMessage":
        """快捷创建任务结果消息。"""
        return cls(
            sender_id=sender_id,
            receiver_id=receiver_id,
            msg_type=MessageType.TASK_RESULT,
            content={
                "success": success,
                "code": code,
                "result": result,
                "geom_commands": geom_commands or [],
            },
            reply_to=reply_to,
            conversation_id=conversation_id,
        )


class MessageHistory:
    """消息历史记录器，支持审计和调试。

    保留最近 N 条消息，支持按发送方/接收方/类型/会话 ID 过滤查询。
    """

    def __init__(self, max_size: int = 500):
        self._history: Deque[AgentMessage] = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def record(self, message: AgentMessage):
        """记录一条消息到历史。"""
        with self._lock:
            self._history.append(message)

    def query(
        self,
        sender_id: Optional[str] = None,
        receiver_id: Optional[str] = None,
        msg_type: Optional[MessageType] = None,
        conversation_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[AgentMessage]:
        """查询消息历史。"""
        with self._lock:
            results = []
            for msg in reversed(self._history):
                if sender_id and msg.sender_id != sender_id:
                    continue
                if receiver_id and msg.receiver_id != receiver_id:
                    continue
                if msg_type and msg.msg_type != msg_type:
                    continue
                if conversation_id and msg.conversation_id != conversation_id:
                    continue
                results.append(msg)
                if len(results) >= limit:
                    break
            return results

    def get_conversation(self, conversation_id: str) -> List[AgentMessage]:
        """获取某个会话的所有消息（按时间排序）。"""
        with self._lock:
            return [msg for msg in self._history if msg.conversation_id == conversation_id]

    def clear(self):
        """清空历史记录。"""
        with self._lock:
            self._history.clear()

    def __len__(self):
        with self._lock:
            return len(self._history)


class MessageBus:
    """线程安全的发布-订阅消息总线。

    核心功能：
    1. 点对点消息：发送方指定接收方 ID，消息直接投递
    2. 广播消息：接收方 ID 为 "broadcast"，所有订阅者收到
    3. 主题订阅：Agent 可订阅特定消息类型
    4. 消息历史：自动记录所有经过总线的消息

    线程安全设计：
    - 使用 RLock 保护订阅者字典
    - 消息投递在锁外执行，避免回调中再次发送消息导致死锁
    """

    def __init__(self, history_size: int = 500):
        self._subscribers: Dict[str, Callable[[AgentMessage], None]] = {}
        self._type_subscribers: Dict[MessageType, List[Callable]] = {}
        self._history = MessageHistory(history_size)
        self._lock = threading.RLock()
        self._message_counter = 0

    def subscribe(
        self,
        agent_id: str,
        handler: Callable[[AgentMessage], None],
    ):
        """订阅点对点消息。

        Args:
            agent_id: 订阅者的 Agent ID
            handler: 消息处理回调函数
        """
        with self._lock:
            self._subscribers[agent_id] = handler
            logger.debug(f"消息总线: {agent_id} 已订阅")

    def subscribe_to_type(
        self,
        msg_type: MessageType,
        handler: Callable[[AgentMessage], None],
    ):
        """订阅特定类型的消息（不论接收方是谁）。

        用于监控、日志、审计等场景。
        """
        with self._lock:
            if msg_type not in self._type_subscribers:
                self._type_subscribers[msg_type] = []
            self._type_subscribers[msg_type].append(handler)

    def unsubscribe(self, agent_id: str):
        """取消订阅。"""
        with self._lock:
            self._subscribers.pop(agent_id, None)
            logger.debug(f"消息总线: {agent_id} 已取消订阅")

    def publish(self, message: AgentMessage) -> bool:
        """发布消息到总线。

        Returns:
            True 如果消息被投递给至少一个订阅者
        """
        # 记录到历史
        self._history.record(message)
        self._message_counter += 1

        delivered = False

        # 收集需要通知的处理器（在锁内收集，锁外执行）
        handlers_to_call = []

        with self._lock:
            # 点对点消息
            if message.receiver_id == "broadcast":
                # 广播：通知所有订阅者
                for handler in self._subscribers.values():
                    handlers_to_call.append(handler)
            else:
                # 点对点：只通知指定接收方
                handler = self._subscribers.get(message.receiver_id)
                if handler:
                    handlers_to_call.append(handler)

            # 类型订阅者
            type_handlers = self._type_subscribers.get(message.msg_type, [])
            handlers_to_call.extend(type_handlers)

        # 在锁外执行回调，避免死锁
        for handler in handlers_to_call:
            try:
                handler(message)
                delivered = True
            except Exception as e:
                logger.error(f"消息处理器异常 (msg={message.id}, type={message.msg_type.value}): {e}")

        if not delivered and message.receiver_id != "broadcast":
            logger.warning(
                f"消息未投递: {message.sender_id} → {message.receiver_id} "
                f"(type={message.msg_type.value}, id={message.id})"
            )

        return delivered

    def get_history(self) -> MessageHistory:
        """获取消息历史记录器。"""
        return self._history

    def get_stats(self) -> dict:
        """获取消息总线统计信息。"""
        with self._lock:
            return {
                "total_messages": self._message_counter,
                "active_subscribers": len(self._subscribers),
                "type_subscribers": {t.value: len(hs) for t, hs in self._type_subscribers.items()},
                "history_size": len(self._history),
            }


class MessageRouter:
    """消息路由层：连接 AgentRegistry 和 MessageBus。

    职责：
    1. 为每个注册的 Agent 创建消息邮箱
    2. 将任务请求消息转化为 Agent 的 solve_problem 调用
    3. 将 Agent 的执行结果转化为任务结果消息
    4. 支持同步和异步消息处理
    """

    def __init__(self, message_bus: MessageBus, agent_registry=None):
        self.bus = message_bus
        self.agent_registry = agent_registry
        self._pending_tasks: Dict[str, dict] = {}  # message_id → task_info
        self._lock = threading.RLock()

    def register_agent(self, agent_id: str, agent_instance):
        """注册 Agent 到消息路由层。

        为 Agent 创建消息邮箱，并设置消息处理器。
        """

        def _handle_message(message: AgentMessage):
            self._dispatch_to_agent(agent_id, agent_instance, message)

        self.bus.subscribe(agent_id, _handle_message)
        logger.info(f"消息路由: Agent '{agent_id}' 已注册消息邮箱")

    def _dispatch_to_agent(
        self,
        agent_id: str,
        agent_instance,
        message: AgentMessage,
    ):
        """将消息分派到 Agent 实例。

        根据消息类型调用 Agent 的不同方法：
        - TASK_REQUEST → solve_problem
        - QUERY → 自定义查询处理
        - NOTIFICATION → 日志记录
        """
        if message.msg_type == MessageType.TASK_REQUEST:
            self._handle_task_request(agent_id, agent_instance, message)
        elif message.msg_type == MessageType.QUERY:
            self._handle_query(agent_id, agent_instance, message)
        elif message.msg_type == MessageType.NOTIFICATION:
            logger.info(f"Agent '{agent_id}' 收到通知: {message.content}")
        elif message.msg_type == MessageType.STATUS_UPDATE:
            logger.debug(f"Agent '{agent_id}' 状态更新: {message.content}")
        else:
            logger.debug(f"Agent '{agent_id}' 收到消息 (type={message.msg_type.value})")

    def _handle_task_request(
        self,
        agent_id: str,
        agent_instance,
        message: AgentMessage,
    ):
        """处理任务请求消息：调用 Agent 的 solve_problem。"""
        task_prompt = message.content if isinstance(message.content, str) else str(message.content)

        # 收集执行结果
        result_container = {
            "success": False,
            "code": "",
            "result": "",
            "geom_commands": [],
        }

        def _on_finish(success, content):
            result_container["success"] = success
            result_container["code"] = content or ""

        def _on_geom(cmds):
            result_container["geom_commands"].extend(cmds or [])

        try:
            agent_instance.solve_problem(
                task_prompt,
                on_finish_cb=_on_finish,
                on_geom_cb=_on_geom,
            )

            # 发送任务结果消息
            result_msg = AgentMessage.create_task_result(
                sender_id=agent_id,
                receiver_id=message.sender_id,
                success=cast(bool, result_container["success"]),
                code=cast(str, result_container["code"]),
                geom_commands=cast(list, result_container["geom_commands"]),
                reply_to=message.id,
                conversation_id=message.conversation_id,
            )
            self.bus.publish(result_msg)

        except Exception as e:
            # 发送错误消息
            error_msg = AgentMessage(
                sender_id=agent_id,
                receiver_id=message.sender_id,
                msg_type=MessageType.TASK_ERROR,
                content=str(e),
                reply_to=message.id,
                conversation_id=message.conversation_id,
            )
            self.bus.publish(error_msg)
            logger.error(f"Agent '{agent_id}' 执行任务失败: {e}")

    def _handle_query(
        self,
        agent_id: str,
        agent_instance,
        message: AgentMessage,
    ):
        """处理查询消息：返回 Agent 的能力描述或状态信息。"""
        query = message.content if isinstance(message.content, str) else ""

        response_content = ""
        if "capability" in query.lower() or "能力" in query:
            response_content = getattr(agent_instance, "system_prompt", "N/A")
        elif "status" in query.lower() or "状态" in query:
            response_content = (
                f"Agent '{agent_id}' 在线，模型: {getattr(agent_instance, '_get_effective_model', lambda: 'unknown')()}"
            )
        else:
            response_content = f"查询已收到: {query}"

        response_msg = AgentMessage(
            sender_id=agent_id,
            receiver_id=message.sender_id,
            msg_type=MessageType.RESPONSE,
            content=response_content,
            reply_to=message.id,
            conversation_id=message.conversation_id,
        )
        self.bus.publish(response_msg)

    def send_task_request(
        self,
        sender_id: str,
        receiver_id: str,
        task_prompt: str,
        **metadata,
    ) -> str:
        """发送任务请求消息（便捷方法）。

        Returns:
            消息 ID（可用于追踪回复）
        """
        conversation_id = metadata.pop("conversation_id", str(uuid.uuid4())[:8])
        msg = AgentMessage.create_task_request(
            sender_id=sender_id,
            receiver_id=receiver_id,
            task_prompt=task_prompt,
            conversation_id=conversation_id,
            **metadata,
        )
        self.bus.publish(msg)
        return msg.id

    def broadcast_notification(
        self,
        sender_id: str,
        content: str,
        **metadata,
    ):
        """广播通知消息。"""
        msg = AgentMessage(
            sender_id=sender_id,
            receiver_id="broadcast",
            msg_type=MessageType.NOTIFICATION,
            content=content,
            metadata=metadata,
        )
        self.bus.publish(msg)


# 全局消息总线实例（单例）
_global_message_bus: Optional[MessageBus] = None
_global_message_router: Optional[MessageRouter] = None
_bus_lock = threading.RLock()  # 可重入锁，允许 get_message_router 调用 get_message_bus


def get_message_bus() -> MessageBus:
    """获取全局消息总线实例（单例模式）。"""
    global _global_message_bus
    if _global_message_bus is None:
        with _bus_lock:
            if _global_message_bus is None:
                _global_message_bus = MessageBus()
                logger.info("全局消息总线已初始化")
    return _global_message_bus


def get_message_router() -> MessageRouter:
    """获取全局消息路由器实例（单例模式）。"""
    global _global_message_router
    if _global_message_router is None:
        with _bus_lock:
            if _global_message_router is None:
                _global_message_router = MessageRouter(get_message_bus())
                logger.info("全局消息路由器已初始化")
    return _global_message_router


def reset_message_bus():
    """重置全局消息总线（主要用于测试）。"""
    global _global_message_bus, _global_message_router
    with _bus_lock:
        _global_message_bus = None
        _global_message_router = None
