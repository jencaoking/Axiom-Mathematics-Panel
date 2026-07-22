"""学生认知模型与自适应学习引擎单元测试。

测试覆盖：
1. StudentModel — 知识掌握度更新、认知层级演进、学习偏好推断、薄弱点追踪
2. AdaptiveEngine — 自适应 Prompt 生成、互动分类、知识点提取、ZPD 计算
3. StudentModelManager — 持久化存储、加载、重置
4. 序列化/反序列化一致性
"""

import os

from mathlab.core.student_model import (
    StudentModel,
    AdaptiveEngine,
    StudentModelManager,
    CognitiveLevel,
    LearningStyle,
    InteractionType,
)


class TestCognitiveLevel:
    """Bloom 认知层级测试。"""

    def test_from_string_chinese(self):
        assert CognitiveLevel.from_string("记忆") == CognitiveLevel.REMEMBER
        assert CognitiveLevel.from_string("理解") == CognitiveLevel.UNDERSTAND
        assert CognitiveLevel.from_string("应用") == CognitiveLevel.APPLY
        assert CognitiveLevel.from_string("分析") == CognitiveLevel.ANALYZE
        assert CognitiveLevel.from_string("评价") == CognitiveLevel.EVALUATE
        assert CognitiveLevel.from_string("创造") == CognitiveLevel.CREATE

    def test_from_string_english(self):
        assert CognitiveLevel.from_string("remember") == CognitiveLevel.REMEMBER
        assert CognitiveLevel.from_string("create") == CognitiveLevel.CREATE

    def test_from_string_invalid_defaults_to_understand(self):
        assert CognitiveLevel.from_string("unknown") == CognitiveLevel.UNDERSTAND

    def test_to_chinese(self):
        assert CognitiveLevel.REMEMBER.to_chinese() == "记忆"
        assert CognitiveLevel.CREATE.to_chinese() == "创造"

    def test_hierarchy_order(self):
        assert CognitiveLevel.REMEMBER.value < CognitiveLevel.UNDERSTAND.value
        assert CognitiveLevel.UNDERSTAND.value < CognitiveLevel.APPLY.value
        assert CognitiveLevel.CREATE.value == 6


class TestStudentModel:
    """学生模型核心测试。"""

    def test_initial_state(self):
        model = StudentModel("test_student")
        assert model.student_id == "test_student"
        assert model.knowledge_mastery == {}
        assert model.cognitive_level == CognitiveLevel.UNDERSTAND
        assert model.learning_style == LearningStyle.BALANCED
        assert model.engagement_score == 0.5
        assert model.total_interactions == 0

    def test_record_correct_answer_increases_mastery(self):
        model = StudentModel("test")
        initial_mastery = model.knowledge_mastery.get("导数", 0.3)

        model.record_interaction(
            interaction_type=InteractionType.ANSWER_CORRECT,
            knowledge_point="导数",
            prompt_text="求导",
            success=True,
            cognitive_demand=CognitiveLevel.APPLY,
        )

        new_mastery = model.knowledge_mastery["导数"]
        assert new_mastery > initial_mastery
        assert model.total_interactions == 1
        assert model.correct_count == 1

    def test_record_wrong_answer_decreases_mastery(self):
        model = StudentModel("test")
        # 先建立初始掌握度
        model.record_interaction(
            interaction_type=InteractionType.ANSWER_CORRECT,
            knowledge_point="积分",
            success=True,
            cognitive_demand=CognitiveLevel.APPLY,
        )
        mid_mastery = model.knowledge_mastery["积分"]

        # 记录错误回答
        model.record_interaction(
            interaction_type=InteractionType.ANSWER_WRONG,
            knowledge_point="积分",
            success=False,
            cognitive_demand=CognitiveLevel.ANALYZE,
        )

        final_mastery = model.knowledge_mastery["积分"]
        assert final_mastery < mid_mastery

    def test_cognitive_level_promotion_on_success(self):
        model = StudentModel("test")
        assert model.cognitive_level == CognitiveLevel.UNDERSTAND

        # 成功完成高认知需求任务应提升层级
        model.record_interaction(
            interaction_type=InteractionType.SOLVE_REQUEST,
            knowledge_point="极限",
            success=True,
            cognitive_demand=CognitiveLevel.UNDERSTAND,
        )
        assert model.cognitive_level == CognitiveLevel.APPLY

    def test_cognitive_level_capped_at_create(self):
        model = StudentModel("test")
        model.cognitive_level = CognitiveLevel.CREATE

        model.record_interaction(
            interaction_type=InteractionType.SOLVE_REQUEST,
            knowledge_point="极限",
            success=True,
            cognitive_demand=CognitiveLevel.CREATE,
        )
        assert model.cognitive_level == CognitiveLevel.CREATE

    def test_engagement_score_increases_on_success(self):
        model = StudentModel("test")
        initial = model.engagement_score

        model.record_interaction(
            interaction_type=InteractionType.ANSWER_CORRECT,
            knowledge_point="矩阵",
            success=True,
        )
        assert model.engagement_score > initial

    def test_engagement_score_decreases_on_failure(self):
        model = StudentModel("test")
        model.engagement_score = 0.8
        initial = model.engagement_score

        model.record_interaction(
            interaction_type=InteractionType.ANSWER_WRONG,
            knowledge_point="矩阵",
            success=False,
        )
        assert model.engagement_score < initial

    def test_engagement_score_floor(self):
        model = StudentModel("test")
        model.engagement_score = 0.05

        model.record_interaction(
            interaction_type=InteractionType.ANSWER_WRONG,
            knowledge_point="矩阵",
            success=False,
        )
        assert model.engagement_score >= 0.1

    def test_weakness_areas_tracking(self):
        model = StudentModel("test")
        # 多次失败使掌握度降低
        for _ in range(5):
            model.record_interaction(
                interaction_type=InteractionType.ANSWER_WRONG,
                knowledge_point="向量",
                success=False,
            )

        assert "向量" in model.weakness_areas

    def test_mastery_level_description(self):
        model = StudentModel("test")
        model.knowledge_mastery["A"] = 0.1
        model.knowledge_mastery["B"] = 0.4
        model.knowledge_mastery["C"] = 0.7
        model.knowledge_mastery["D"] = 0.9

        assert model.get_mastery_level("A") == "未掌握"
        assert model.get_mastery_level("B") == "初步理解"
        assert model.get_mastery_level("C") == "基本掌握"
        assert model.get_mastery_level("D") == "熟练掌握"
        assert model.get_mastery_level("unknown") == "未掌握"

    def test_zpd_zone(self):
        model = StudentModel("test")
        model.cognitive_level = CognitiveLevel.APPLY
        comfort, stretch = model.get_zpd_zone()
        assert comfort == CognitiveLevel.APPLY
        assert stretch == CognitiveLevel.ANALYZE

    def test_zpd_zone_at_max(self):
        model = StudentModel("test")
        model.cognitive_level = CognitiveLevel.CREATE
        comfort, stretch = model.get_zpd_zone()
        assert comfort == CognitiveLevel.CREATE
        assert stretch == CognitiveLevel.CREATE

    def test_interaction_history_truncation(self):
        model = StudentModel("test")
        for i in range(250):
            model.record_interaction(
                interaction_type=InteractionType.QUESTION,
                prompt_text=f"question {i}",
            )
        assert len(model.interaction_history) <= 200

    def test_learning_style_inference_visual(self):
        model = StudentModel("test")
        for _ in range(10):
            model.record_interaction(
                interaction_type=InteractionType.DRAW_REQUEST,
                prompt_text="画一个圆",
            )

        assert model.learning_style == LearningStyle.VISUAL

    def test_learning_style_inference_analytical(self):
        model = StudentModel("test")
        for _ in range(10):
            model.record_interaction(
                interaction_type=InteractionType.SOLVE_REQUEST,
                prompt_text="计算积分",
            )

        assert model.learning_style == LearningStyle.ANALYTICAL

    def test_profile_summary(self):
        model = StudentModel("test")
        model.record_interaction(
            interaction_type=InteractionType.SOLVE_REQUEST,
            knowledge_point="导数",
            success=True,
            cognitive_demand=CognitiveLevel.APPLY,
        )

        summary = model.get_profile_summary()
        assert "cognitive_level" in summary
        assert "learning_style" in summary
        assert "avg_mastery" in summary
        assert "weakness_areas" in summary
        assert "engagement" in summary
        assert "top_mastered" in summary

    def test_serialization_roundtrip(self):
        model = StudentModel("test_roundtrip")
        model.record_interaction(
            interaction_type=InteractionType.SOLVE_REQUEST,
            knowledge_point="极限",
            prompt_text="求极限",
            success=True,
            cognitive_demand=CognitiveLevel.APPLY,
        )
        model.cognitive_level = CognitiveLevel.ANALYZE

        data = model.to_dict()
        restored = StudentModel.from_dict(data)

        assert restored.student_id == model.student_id
        assert restored.knowledge_mastery == model.knowledge_mastery
        assert restored.cognitive_level == model.cognitive_level
        assert restored.learning_style == model.learning_style
        assert restored.total_interactions == model.total_interactions
        assert restored.correct_count == model.correct_count
        assert len(restored.interaction_history) == len(model.interaction_history)


class TestAdaptiveEngine:
    """自适应引擎测试。"""

    def test_build_adaptive_prompt_contains_key_sections(self):
        model = StudentModel("test")
        model.record_interaction(
            interaction_type=InteractionType.SOLVE_REQUEST,
            knowledge_point="导数",
            success=True,
            cognitive_demand=CognitiveLevel.APPLY,
        )
        engine = AdaptiveEngine(model)

        prompt = engine.build_adaptive_prompt("求导数")

        assert "学生认知画像" in prompt
        assert "Bloom分类法" in prompt
        assert "最近发展区" in prompt
        assert "教学策略要求" in prompt

    def test_build_adaptive_prompt_includes_weakness(self):
        model = StudentModel("test")
        for _ in range(5):
            model.record_interaction(
                interaction_type=InteractionType.ANSWER_WRONG,
                knowledge_point="向量",
                success=False,
            )
        engine = AdaptiveEngine(model)

        prompt = engine.build_adaptive_prompt("向量运算")
        assert "薄弱知识点" in prompt
        assert "向量" in prompt

    def test_classify_interaction_draw(self):
        model = StudentModel("test")
        engine = AdaptiveEngine(model)
        assert (
            engine.classify_interaction("画一个三角形") == InteractionType.DRAW_REQUEST
        )
        assert (
            engine.classify_interaction("绘制函数图像") == InteractionType.DRAW_REQUEST
        )

    def test_classify_interaction_solve(self):
        model = StudentModel("test")
        engine = AdaptiveEngine(model)
        assert engine.classify_interaction("计算积分") == InteractionType.SOLVE_REQUEST
        assert engine.classify_interaction("求解方程") == InteractionType.SOLVE_REQUEST

    def test_classify_interaction_explain(self):
        model = StudentModel("test")
        engine = AdaptiveEngine(model)
        assert (
            engine.classify_interaction("为什么这样解")
            == InteractionType.EXPLAIN_REQUEST
        )
        assert (
            engine.classify_interaction("解释一下证明过程")
            == InteractionType.EXPLAIN_REQUEST
        )

    def test_extract_knowledge_point(self):
        model = StudentModel("test")
        engine = AdaptiveEngine(model)

        assert engine.extract_knowledge_point("求导数") == "导数"
        assert engine.extract_knowledge_point("计算积分") == "积分"
        assert engine.extract_knowledge_point("画一个圆") == "圆"
        assert engine.extract_knowledge_point("矩阵运算") == "矩阵"
        assert engine.extract_knowledge_point("随便聊聊") == ""

    def test_difficulty_suggestion_high_success(self):
        model = StudentModel("test")
        engine = AdaptiveEngine(model)
        suggestion = engine.suggest_difficulty_adjustment(0.9)
        assert "提升难度" in suggestion

    def test_difficulty_suggestion_low_success(self):
        model = StudentModel("test")
        engine = AdaptiveEngine(model)
        suggestion = engine.suggest_difficulty_adjustment(0.2)
        assert "大幅降低" in suggestion

    def test_recommended_cognitive_demand(self):
        model = StudentModel("test")
        model.cognitive_level = CognitiveLevel.UNDERSTAND
        model.engagement_score = 0.8
        engine = AdaptiveEngine(model)

        demand = engine.get_recommended_cognitive_demand()
        # 高参与度应推荐挑战区
        assert demand == CognitiveLevel.APPLY

    def test_recommended_cognitive_demand_low_engagement(self):
        model = StudentModel("test")
        model.cognitive_level = CognitiveLevel.UNDERSTAND
        model.engagement_score = 0.3
        engine = AdaptiveEngine(model)

        demand = engine.get_recommended_cognitive_demand()
        # 低参与度应推荐舒适区
        assert demand == CognitiveLevel.UNDERSTAND


class TestStudentModelManager:
    """学生模型持久化管理测试。"""

    def test_persistence_roundtrip(self, tmp_path):
        manager = StudentModelManager(storage_dir=str(tmp_path))
        model = manager.get_model("test_user")

        model.record_interaction(
            interaction_type=InteractionType.SOLVE_REQUEST,
            knowledge_point="导数",
            prompt_text="求导",
            success=True,
            cognitive_demand=CognitiveLevel.APPLY,
        )
        manager.save_model("test_user")

        # 重新加载
        manager2 = StudentModelManager(storage_dir=str(tmp_path))
        loaded = manager2.get_model("test_user")

        assert loaded.total_interactions == 1
        assert loaded.knowledge_mastery.get("导数", 0) > 0
        assert loaded.correct_count == 1

    def test_reset_model(self, tmp_path):
        manager = StudentModelManager(storage_dir=str(tmp_path))
        model = manager.get_model("test_reset")
        model.record_interaction(
            interaction_type=InteractionType.QUESTION,
            knowledge_point="导数",
        )
        manager.save_model("test_reset")

        # 确认文件存在
        filepath = os.path.join(str(tmp_path), "test_reset.json")
        assert os.path.exists(filepath)

        manager.reset_model("test_reset")

        # 确认文件已删除
        assert not os.path.exists(filepath)

        # 确认模型已重置
        reset_model = manager.get_model("test_reset")
        assert reset_model.total_interactions == 0
        assert reset_model.knowledge_mastery == {}

    def test_save_all(self, tmp_path):
        manager = StudentModelManager(storage_dir=str(tmp_path))
        m1 = manager.get_model("user1")
        m2 = manager.get_model("user2")
        m1.record_interaction(
            interaction_type=InteractionType.QUESTION,
        )
        m2.record_interaction(
            interaction_type=InteractionType.QUESTION,
        )
        manager.save_all()

        assert os.path.exists(os.path.join(str(tmp_path), "user1.json"))
        assert os.path.exists(os.path.join(str(tmp_path), "user2.json"))

    def test_default_storage_dir(self):
        manager = StudentModelManager()
        assert ".mathlab" in manager.storage_dir
        assert "student_profiles" in manager.storage_dir
        assert os.path.isdir(manager.storage_dir)
