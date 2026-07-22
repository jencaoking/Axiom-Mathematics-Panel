"""结构化 Agent 通信协议 (ACP) 单元测试。

测试覆盖：
1. AgentMessage — 消息创建、序列化、快捷工厂方法
2. MessageBus — 发布/订阅、广播、类型订阅、线程安全
3. MessageHistory — 历史记录、查询过滤
4. MessageRouter — 任务请求分派、查询处理、错误处理
5. 全局单例 — 消息总线路由器获取与重置
"""

import threading
import time
import pytest

from mathlab.core.agent_message import (
    AgentMessage,
    MessageBus,
    MessageHistory,
    MessageRouter,
    MessageType,
    MessagePriority,
    get_message_bus,
    get_message_router,
    reset_message_bus,
)


class TestAgentMessage:
    """Agent 消息测试。"""

    def test_create_basic_message(self):
        msg = AgentMessage(
            sender_id="PlannerAgent",
            receiver_id="GeometryAgent",
            msg_type=MessageType.TASK_REQUEST,
            content="画一个三角形",
        )
        assert msg.sender_id == "PlannerAgent"
        assert msg.receiver_id == "GeometryAgent"
        assert msg.msg_type == MessageType.TASK_REQUEST
        assert msg.content == "画一个三角形"
        assert msg.priority == MessagePriority.NORMAL
        assert msg.id is not None
        assert len(msg.id) == 8

    def test_create_task_request_factory(self):
        msg = AgentMessage.create_task_request(
            sender_id="PlannerAgent",
            receiver_id="GeometryAgent",
            task_prompt="求解方程",
            step_num=1,
            cognitive_level="应用",
        )
        assert msg.msg_type == MessageType.TASK_REQUEST
        assert msg.content == "求解方程"
        assert msg.metadata["step_num"] == 1
        assert msg.metadata["cognitive_level"] == "应用"

    def test_create_task_result_factory(self):
        msg = AgentMessage.create_task_result(
            sender_id="GeometryAgent",
            receiver_id="PlannerAgent",
            success=True,
            code="print(42)",
            geom_commands=["draw_circle"],
        )
        assert msg.msg_type == MessageType.TASK_RESULT
        assert msg.content["success"] is True
        assert msg.content["code"] == "print(42)"
        assert "draw_circle" in msg.content["geom_commands"]

    def test_serialization_roundtrip(self):
        msg = AgentMessage(
            sender_id="A",
            receiver_id="B",
            msg_type=MessageType.QUERY,
            content="你的能力是什么？",
            metadata={"topic": "数学"},
            priority=MessagePriority.HIGH,
            conversation_id="conv123",
        )
        data = msg.to_dict()
        restored = AgentMessage.from_dict(data)

        assert restored.sender_id == msg.sender_id
        assert restored.receiver_id == msg.receiver_id
        assert restored.msg_type == msg.msg_type
        assert restored.content == msg.content
        assert restored.metadata == msg.metadata
        assert restored.priority == msg.priority
        assert restored.conversation_id == msg.conversation_id

    def test_broadcast_receiver_id(self):
        msg = AgentMessage(
            sender_id="A",
            receiver_id="broadcast",
            msg_type=MessageType.BROADCAST,
            content="系统通知",
        )
        assert msg.receiver_id == "broadcast"

    def test_reply_to_chain(self):
        original = AgentMessage.create_task_request(
            sender_id="A", receiver_id="B", task_prompt="任务"
        )
        reply = AgentMessage.create_task_result(
            sender_id="B",
            receiver_id="A",
            success=True,
            reply_to=original.id,
        )
        assert reply.reply_to == original.id


class TestMessageBus:
    """消息总线测试。"""

    def test_publish_point_to_point(self):
        bus = MessageBus()
        received = []

        bus.subscribe("B", lambda msg: received.append(msg))

        msg = AgentMessage(
            sender_id="A",
            receiver_id="B",
            msg_type=MessageType.NOTIFICATION,
            content="hello",
        )
        delivered = bus.publish(msg)

        assert delivered is True
        assert len(received) == 1
        assert received[0].content == "hello"

    def test_publish_broadcast(self):
        bus = MessageBus()
        received_a = []
        received_b = []
        received_c = []

        bus.subscribe("A", lambda msg: received_a.append(msg))
        bus.subscribe("B", lambda msg: received_b.append(msg))
        bus.subscribe("C", lambda msg: received_c.append(msg))

        msg = AgentMessage(
            sender_id="System",
            receiver_id="broadcast",
            msg_type=MessageType.BROADCAST,
            content="系统更新",
        )
        bus.publish(msg)

        assert len(received_a) == 1
        assert len(received_b) == 1
        assert len(received_c) == 1

    def test_publish_no_subscriber(self):
        bus = MessageBus()
        msg = AgentMessage(
            sender_id="A",
            receiver_id="Unknown",
            msg_type=MessageType.NOTIFICATION,
            content="hello",
        )
        delivered = bus.publish(msg)
        assert delivered is False

    def test_subscribe_to_type(self):
        bus = MessageBus()
        type_messages = []

        bus.subscribe_to_type(
            MessageType.TASK_REQUEST,
            lambda msg: type_messages.append(msg),
        )

        # 发布一条 TASK_REQUEST 消息
        bus.publish(
            AgentMessage(
                sender_id="A",
                receiver_id="B",
                msg_type=MessageType.TASK_REQUEST,
                content="任务",
            )
        )
        # 发布一条 NOTIFICATION 消息（不应被捕获）
        bus.publish(
            AgentMessage(
                sender_id="A",
                receiver_id="B",
                msg_type=MessageType.NOTIFICATION,
                content="通知",
            )
        )

        assert len(type_messages) == 1
        assert type_messages[0].msg_type == MessageType.TASK_REQUEST

    def test_unsubscribe(self):
        bus = MessageBus()
        received = []

        bus.subscribe("B", lambda msg: received.append(msg))
        bus.unsubscribe("B")

        bus.publish(
            AgentMessage(
                sender_id="A",
                receiver_id="B",
                msg_type=MessageType.NOTIFICATION,
            )
        )
        assert len(received) == 0

    def test_handler_exception_doesnt_block_others(self):
        bus = MessageBus()
        received = []

        def bad_handler(msg):
            raise RuntimeError("故意出错")

        bus.subscribe("B", bad_handler)
        bus.subscribe("C", lambda msg: received.append(msg))

        # 广播消息，B 的处理器出错但 C 应该仍能收到
        bus.publish(
            AgentMessage(
                sender_id="A",
                receiver_id="broadcast",
                msg_type=MessageType.NOTIFICATION,
            )
        )

        assert len(received) == 1

    def test_thread_safety(self):
        """测试多线程并发发布消息的线程安全性。"""
        bus = MessageBus()
        received = []
        lock = threading.Lock()

        def handler(msg):
            with lock:
                received.append(msg)

        bus.subscribe("B", handler)

        def publisher():
            for i in range(20):
                bus.publish(
                    AgentMessage(
                        sender_id="A",
                        receiver_id="B",
                        msg_type=MessageType.NOTIFICATION,
                        content=f"msg-{i}",
                    )
                )

        threads = [threading.Thread(target=publisher) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(received) == 100  # 5 threads × 20 msgs

    def test_get_stats(self):
        bus = MessageBus()
        bus.subscribe("A", lambda msg: None)
        bus.subscribe("B", lambda msg: None)

        bus.publish(
            AgentMessage(
                sender_id="System",
                receiver_id="A",
                msg_type=MessageType.NOTIFICATION,
                content="test",
            )
        )

        stats = bus.get_stats()
        assert stats["total_messages"] == 1
        assert stats["active_subscribers"] == 2
        assert stats["history_size"] == 1


class TestMessageHistory:
    """消息历史记录测试。"""

    def test_record_and_query(self):
        history = MessageHistory(max_size=100)

        for i in range(10):
            history.record(
                AgentMessage(
                    sender_id=f"Agent-{i % 3}",
                    receiver_id=f"Receiver-{i % 2}",
                    msg_type=(
                        MessageType.NOTIFICATION
                        if i % 2 == 0
                        else MessageType.TASK_REQUEST
                    ),
                    content=f"msg-{i}",
                    conversation_id=f"conv-{i % 2}",
                )
            )

        # 查询全部
        all_msgs = history.query(limit=100)
        assert len(all_msgs) == 10

        # 按 sender 查询
        agent_0_msgs = history.query(sender_id="Agent-0")
        assert len(agent_0_msgs) > 0
        assert all(m.sender_id == "Agent-0" for m in agent_0_msgs)

        # 按类型查询
        task_msgs = history.query(msg_type=MessageType.TASK_REQUEST)
        assert all(m.msg_type == MessageType.TASK_REQUEST for m in task_msgs)

        # 按会话查询
        conv_msgs = history.query(conversation_id="conv-0")
        assert all(m.conversation_id == "conv-0" for m in conv_msgs)

    def test_max_size_enforced(self):
        history = MessageHistory(max_size=5)
        for i in range(10):
            history.record(
                AgentMessage(
                    sender_id="A",
                    receiver_id="B",
                    msg_type=MessageType.NOTIFICATION,
                    content=f"msg-{i}",
                )
            )
        assert len(history) == 5  # 只保留最近 5 条

    def test_get_conversation(self):
        history = MessageHistory()
        conv_id = "test-conv"

        for i in range(5):
            history.record(
                AgentMessage(
                    sender_id="A",
                    receiver_id="B",
                    msg_type=MessageType.NOTIFICATION,
                    content=f"msg-{i}",
                    conversation_id=conv_id,
                )
            )
        # 添加一条不属于此会话的
        history.record(
            AgentMessage(
                sender_id="A",
                receiver_id="B",
                msg_type=MessageType.NOTIFICATION,
                content="other",
                conversation_id="other-conv",
            )
        )

        conv_msgs = history.get_conversation(conv_id)
        assert len(conv_msgs) == 5
        assert all(m.conversation_id == conv_id for m in conv_msgs)

    def test_clear(self):
        history = MessageHistory()
        for i in range(5):
            history.record(
                AgentMessage(
                    sender_id="A",
                    receiver_id="B",
                    msg_type=MessageType.NOTIFICATION,
                )
            )
        assert len(history) == 5
        history.clear()
        assert len(history) == 0


class TestMessageRouter:
    """消息路由器测试。"""

    def test_register_and_dispatch_task_request(self):
        """测试注册 Agent 并分派任务请求。"""
        bus = MessageBus()
        router = MessageRouter(bus)

        class MockAgent:
            def __init__(self):
                self.solved = False
                self.last_prompt = ""

            def solve_problem(
                self, prompt, on_finish_cb=None, on_geom_cb=None, **kwargs
            ):
                self.solved = True
                self.last_prompt = prompt
                if on_finish_cb:
                    on_finish_cb(True, "result_code")

        agent = MockAgent()
        router.register_agent("TestAgent", agent)

        # 发送任务请求
        msg = AgentMessage.create_task_request(
            sender_id="PlannerAgent",
            receiver_id="TestAgent",
            task_prompt="求解方程",
        )
        bus.publish(msg)

        assert agent.solved is True
        assert agent.last_prompt == "求解方程"

    def test_query_handling(self):
        """测试查询消息处理。"""
        bus = MessageBus()
        router = MessageRouter(bus)
        responses = []

        class MockAgent:
            system_prompt = "我是测试Agent"

        agent = MockAgent()
        router.register_agent("TestAgent", agent)

        # 订阅 PlannerAgent 的消息以接收响应
        bus.subscribe("PlannerAgent", lambda msg: responses.append(msg))

        # 发送查询
        query_msg = AgentMessage(
            sender_id="PlannerAgent",
            receiver_id="TestAgent",
            msg_type=MessageType.QUERY,
            content="capability",
        )
        bus.publish(query_msg)

        assert len(responses) == 1
        assert responses[0].msg_type == MessageType.RESPONSE
        assert "测试Agent" in responses[0].content

    def test_task_error_on_exception(self):
        """测试 Agent 执行异常时发送错误消息。"""
        bus = MessageBus()
        router = MessageRouter(bus)
        errors = []

        class BadAgent:
            def solve_problem(self, *args, **kwargs):
                raise RuntimeError("执行失败")

        bus.subscribe("PlannerAgent", lambda msg: errors.append(msg))
        router.register_agent("BadAgent", BadAgent())

        bus.publish(
            AgentMessage.create_task_request(
                sender_id="PlannerAgent",
                receiver_id="BadAgent",
                task_prompt="任务",
            )
        )

        assert len(errors) == 1
        assert errors[0].msg_type == MessageType.TASK_ERROR
        assert "执行失败" in errors[0].content

    def test_send_task_request_convenience(self):
        """测试便捷发送方法。"""
        bus = MessageBus()
        router = MessageRouter(bus)
        received = []

        bus.subscribe("TargetAgent", lambda msg: received.append(msg))

        msg_id = router.send_task_request(
            sender_id="PlannerAgent",
            receiver_id="TargetAgent",
            task_prompt="画图",
            step_num=1,
        )

        assert msg_id is not None
        assert len(received) == 1
        assert received[0].content == "画图"
        assert received[0].metadata["step_num"] == 1

    def test_broadcast_notification(self):
        """测试广播通知。"""
        bus = MessageBus()
        router = MessageRouter(bus)
        notifications = []

        bus.subscribe("AgentA", lambda msg: notifications.append(msg))
        bus.subscribe("AgentB", lambda msg: notifications.append(msg))

        router.broadcast_notification("System", "系统维护通知")

        assert len(notifications) == 2
        assert all(n.content == "系统维护通知" for n in notifications)


class TestGlobalSingleton:
    """全局单例测试。"""

    def test_get_message_bus_singleton(self):
        reset_message_bus()
        bus1 = get_message_bus()
        bus2 = get_message_bus()
        assert bus1 is bus2

    def test_get_message_router_singleton(self):
        reset_message_bus()
        router1 = get_message_router()
        router2 = get_message_router()
        assert router1 is router2

    def test_reset_message_bus(self):
        bus1 = get_message_bus()
        reset_message_bus()
        bus2 = get_message_bus()
        assert bus1 is not bus2
