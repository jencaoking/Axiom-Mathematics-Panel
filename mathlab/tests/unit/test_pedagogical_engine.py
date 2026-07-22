"""教学法引导引擎单元测试。

测试覆盖：
1. PedagogicalPromptBuilder — Bloom/ZPD/UDL/Socratic 约束生成
2. TeachingQualityEvaluator — 三维度质量评估
3. PedagogicalConstraint — 约束验证规则
4. QualityReport — 评估报告序列化
"""

from mathlab.core.student_model import (
    StudentModel,
    CognitiveLevel,
    InteractionType,
)
from mathlab.core.pedagogical_engine import (
    PedagogicalPromptBuilder,
    TeachingQualityEvaluator,
    PedagogicalConstraint,
    TeachingPrinciple,
    QualityDimension,
    QualityReport,
)


class TestPedagogicalConstraint:
    """教学法约束规则测试。"""

    def test_socratic_constraint_detects_direct_answer(self):
        constraint = PedagogicalConstraint(
            principle=TeachingPrinciple.SOCRATIC_GUIDED,
            description="禁止直接给最终答案",
            check_pattern=r"答案是[:：]|最终结果[:：]|正确答案[:：]",
            violation_hint="不应直接给出答案",
        )
        passed, hint = constraint.validate("答案是：42")
        assert not passed
        assert "不应直接给出答案" in hint

    def test_socratic_constraint_passes_guided_content(self):
        constraint = PedagogicalConstraint(
            principle=TeachingPrinciple.SOCRATIC_GUIDED,
            description="禁止直接给最终答案",
            check_pattern=r"答案是[:：]|最终结果[:：]|正确答案[:：]",
            violation_hint="不应直接给出答案",
        )
        passed, _ = constraint.validate("你觉得下一步该怎么做？")
        assert passed

    def test_scaffolding_constraint_detects_obvious(self):
        constraint = PedagogicalConstraint(
            principle=TeachingPrinciple.SCAFFOLDING,
            description="禁止一步到位",
            check_pattern=r"显然|很明显|trivially",
            violation_hint="不应跳过推理",
        )
        passed, hint = constraint.validate("显然结果是正确的")
        assert not passed

    def test_constraint_without_pattern_always_passes(self):
        constraint = PedagogicalConstraint(
            principle=TeachingPrinciple.BLOOM_TAXONOMY,
            description="无检查模式",
        )
        passed, _ = constraint.validate("任何内容")
        assert passed


class TestPedagogicalPromptBuilder:
    """教学法提示词构建器测试。"""

    def test_build_decomposition_constraint_contains_bloom(self):
        builder = PedagogicalPromptBuilder()
        constraint = builder.build_decomposition_constraint()
        assert "Bloom" in constraint
        assert "认知层级" in constraint

    def test_build_decomposition_constraint_contains_socratic(self):
        builder = PedagogicalPromptBuilder()
        constraint = builder.build_decomposition_constraint()
        assert "苏格拉底" in constraint

    def test_build_decomposition_constraint_contains_scaffolding(self):
        builder = PedagogicalPromptBuilder()
        constraint = builder.build_decomposition_constraint()
        assert "脚手架" in constraint

    def test_build_decomposition_constraint_with_student_model(self):
        student = StudentModel("test")
        builder = PedagogicalPromptBuilder(student)
        constraint = builder.build_decomposition_constraint()
        assert "最近发展区" in constraint
        assert "UDL" in constraint

    def test_build_step_execution_constraint_contains_cognitive_level(self):
        builder = PedagogicalPromptBuilder()
        constraint = builder.build_step_execution_constraint(
            step_title="理解导数定义",
            cognitive_level="理解",
            hint="从极限角度理解",
        )
        assert "理解" in constraint
        assert "Bloom" in constraint
        assert "教学提示" in constraint

    def test_build_step_execution_constraint_for_apply_level(self):
        builder = PedagogicalPromptBuilder()
        constraint = builder.build_step_execution_constraint(
            step_title="用导数求极值",
            cognitive_level="应用",
            hint="实际计算",
        )
        assert "应用" in constraint
        assert "计算" in constraint  # bloom verbs for apply

    def test_build_step_execution_constraint_for_create_level(self):
        builder = PedagogicalPromptBuilder()
        constraint = builder.build_step_execution_constraint(
            step_title="设计最优化方案",
            cognitive_level="创造",
            hint="创造性任务",
        )
        assert "创造" in constraint
        assert "设计" in constraint

    def test_build_code_generation_constraint_has_quality_rules(self):
        builder = PedagogicalPromptBuilder()
        constraint = builder.build_code_generation_constraint("求导数")
        assert "可读性" in constraint
        assert "分步展示" in constraint
        assert "教学注释" in constraint

    def test_build_code_generation_constraint_with_weak_knowledge(self):
        student = StudentModel("test")
        # 多次失败使掌握度降低
        for _ in range(5):
            student.record_interaction(
                interaction_type=InteractionType.ANSWER_WRONG,
                knowledge_point="导数",
                success=False,
            )
        builder = PedagogicalPromptBuilder(student)
        constraint = builder.build_code_generation_constraint("求导数")
        assert "薄弱知识点" in constraint
        assert "导数" in constraint

    def test_bloom_guidelines_all_levels_present(self):
        builder = PedagogicalPromptBuilder()
        for level in CognitiveLevel:
            assert level in builder.BLOOM_GUIDELINES
            assert "verbs" in builder.BLOOM_GUIDELINES[level]
            assert "activities" in builder.BLOOM_GUIDELINES[level]
            assert "question_stems" in builder.BLOOM_GUIDELINES[level]

    def test_udl_principles_all_present(self):
        builder = PedagogicalPromptBuilder()
        assert "representation" in builder.UDL_PRINCIPLES
        assert "engagement" in builder.UDL_PRINCIPLES
        assert "expression" in builder.UDL_PRINCIPLES


class TestTeachingQualityEvaluator:
    """教学质量评估器测试。"""

    def test_evaluate_high_quality_content(self):
        student = StudentModel("test")
        evaluator = TeachingQualityEvaluator(student)
        content = """
        首先，我们来看导数的定义。因为导数表示变化率，所以可以用极限来理解。
        ```python
        import numpy as np
        # 教学要点：导数是函数在某点的瞬时变化率
        def derivative(f, x, h=1e-5):
            return (f(x + h) - f(x)) / h

        print("导数计算结果:", derivative(lambda x: x**2, 3))
        ```
        接下来，你觉得导数在物理中有什么应用？
        """
        reports = evaluator.evaluate(content, "什么是导数", plan=None)

        overall = evaluator.get_overall_score(reports)
        assert overall > 0.5
        assert all(r.score > 0 for r in reports.values())

    def test_evaluate_low_quality_content(self):
        evaluator = TeachingQualityEvaluator()
        content = "答案是：42"
        reports = evaluator.evaluate(content, "求极限", plan=None)

        content_report = reports[QualityDimension.CONTENT_UNDERSTANDING]
        assert not content_report.passed
        assert len(content_report.issues) > 0

    def test_evaluate_empty_content(self):
        evaluator = TeachingQualityEvaluator()
        reports = evaluator.evaluate("", "求导数", plan=None)

        content_report = reports[QualityDimension.CONTENT_UNDERSTANDING]
        assert not content_report.passed

    def test_evaluate_content_missing_explanation(self):
        evaluator = TeachingQualityEvaluator()
        content = "```python\nprint(42)\n```"
        reports = evaluator.evaluate(content, "求值", plan=None)

        content_report = reports[QualityDimension.CONTENT_UNDERSTANDING]
        assert any("解释" in issue for issue in content_report.issues)

    def test_evaluate_content_missing_steps(self):
        evaluator = TeachingQualityEvaluator()
        content = "因为导数是变化率所以得到数值42"
        reports = evaluator.evaluate(content, "求导数", plan=None)

        content_report = reports[QualityDimension.CONTENT_UNDERSTANDING]
        assert any("中间步骤" in issue for issue in content_report.issues)

    def test_evaluate_direct_answer_violation(self):
        evaluator = TeachingQualityEvaluator()
        content = "因为公式很显然成立，所以答案是：42。最终结果：42。"
        reports = evaluator.evaluate(content, "求值", plan=None)

        pedagogy_report = reports[QualityDimension.PEDAGOGICAL_DESIGN]
        assert not pedagogy_report.passed
        assert any("苏格拉底" in issue or "答案" in issue for issue in pedagogy_report.issues)

    def test_evaluate_missing_question_ending(self):
        evaluator = TeachingQualityEvaluator()
        content = (
            "因为导数表示变化率，所以得到数值42。"
            "导数的几何意义是切线斜率，这个概念非常重要需要深入理解。"
            "在实际应用中导数可以帮助我们求解最值问题和分析函数性质。"
            "导数在物理学中也有广泛应用，比如速度和加速度的概念。"
            "在经济学中边际成本和边际收益也是导数的具体应用。"
            "我们需要从多个角度来理解导数这个核心概念。"
        )
        reports = evaluator.evaluate(content, "什么是导数", plan=None)

        pedagogy_report = reports[QualityDimension.PEDAGOGICAL_DESIGN]
        assert any("提问" in issue for issue in pedagogy_report.issues)

    def test_evaluate_single_representation_violation(self):
        evaluator = TeachingQualityEvaluator()
        # 只有公式没有图形/代码
        content = (
            "因为 $f'(x) = \\lim_{h \\to 0} \\frac{f(x+h)-f(x)}{h}$，"
            "所以导数就是极限。然后我们继续分析导数的性质和特点。"
            "这是一个很长的解释但没有代码和可视化调用。导数的几何意义是切线斜率。"
            "我们需要深入理解导数在微积分中的重要地位和作用。"
            "导数不仅在纯数学中至关重要，在工程应用中也有广泛用途。"
            "比如在信号处理中，导数可以用来检测信号的突变点。"
            "在机器学习中，梯度下降算法的核心就是导数和偏导数的概念。"
            "总之导数是现代数学和工程学的基石之一，必须牢固掌握。"
        )
        reports = evaluator.evaluate(content, "什么是导数", plan=None)

        pedagogy_report = reports[QualityDimension.PEDAGOGICAL_DESIGN]
        assert any("表达方式" in issue or "UDL" in issue for issue in pedagogy_report.issues)

    def test_evaluate_coherence_with_good_plan(self):
        evaluator = TeachingQualityEvaluator()
        plan = {
            "topic": "导数",
            "steps": [
                {"num": 1, "title": "回忆极限", "cognitive_level": "记忆"},
                {"num": 2, "title": "理解导数定义", "cognitive_level": "理解"},
                {"num": 3, "title": "应用导数求解", "cognitive_level": "应用"},
                {"num": 4, "title": "分析导数性质", "cognitive_level": "分析"},
            ],
        }
        content = "首先回忆极限概念。然后理解导数。接着应用导数。最后分析性质。"
        reports = evaluator.evaluate(content, "导数", plan=plan)

        coherence_report = reports[QualityDimension.CONTEXT_COHERENCE]
        assert coherence_report.passed

    def test_evaluate_coherence_with_bad_plan(self):
        evaluator = TeachingQualityEvaluator()
        plan = {
            "topic": "导数",
            "steps": [
                {"num": 1, "title": "创造模型", "cognitive_level": "创造"},
                {"num": 2, "title": "回忆定义", "cognitive_level": "记忆"},
                {"num": 3, "title": "评价方法", "cognitive_level": "评价"},
                {"num": 4, "title": "理解概念", "cognitive_level": "理解"},
            ],
        }
        content = "首先创造模型然后回忆定义接着评价方法最后理解概念。"
        reports = evaluator.evaluate(content, "导数", plan=plan)

        coherence_report = reports[QualityDimension.CONTEXT_COHERENCE]
        assert not coherence_report.passed
        assert any("梯度" in issue or "跨度" in issue for issue in coherence_report.issues)

    def test_evaluate_coherence_excessive_level_span(self):
        evaluator = TeachingQualityEvaluator()
        plan = {
            "topic": "测试",
            "steps": [
                {"num": 1, "title": "记忆", "cognitive_level": "记忆"},
                {"num": 2, "title": "创造", "cognitive_level": "创造"},
            ],
        }
        content = "首先记忆然后创造。"
        reports = evaluator.evaluate(content, "测试", plan=plan)

        coherence_report = reports[QualityDimension.CONTEXT_COHERENCE]
        assert any("跨度" in issue for issue in coherence_report.issues)

    def test_get_overall_score_weighted(self):
        evaluator = TeachingQualityEvaluator()
        reports = {
            QualityDimension.CONTENT_UNDERSTANDING: QualityReport(
                dimension=QualityDimension.CONTENT_UNDERSTANDING,
                score=1.0,
                passed=True,
            ),
            QualityDimension.CONTEXT_COHERENCE: QualityReport(
                dimension=QualityDimension.CONTEXT_COHERENCE,
                score=0.0,
                passed=False,
            ),
            QualityDimension.PEDAGOGICAL_DESIGN: QualityReport(
                dimension=QualityDimension.PEDAGOGICAL_DESIGN,
                score=1.0,
                passed=True,
            ),
        }
        overall = evaluator.get_overall_score(reports)
        # 1.0*0.4 + 0.0*0.25 + 1.0*0.35 = 0.75
        assert overall == 0.75

    def test_build_improvement_feedback_for_failed(self):
        evaluator = TeachingQualityEvaluator()
        reports = {
            QualityDimension.CONTENT_UNDERSTANDING: QualityReport(
                dimension=QualityDimension.CONTENT_UNDERSTANDING,
                score=0.2,
                passed=False,
                issues=["内容过短"],
                suggestions=["增加详细解释"],
            ),
            QualityDimension.CONTEXT_COHERENCE: QualityReport(
                dimension=QualityDimension.CONTEXT_COHERENCE,
                score=0.8,
                passed=True,
            ),
            QualityDimension.PEDAGOGICAL_DESIGN: QualityReport(
                dimension=QualityDimension.PEDAGOGICAL_DESIGN,
                score=0.9,
                passed=True,
            ),
        }
        feedback = evaluator.build_improvement_feedback(reports)
        assert "修正" in feedback
        assert "内容理解" in feedback
        assert "内容过短" in feedback
        assert "增加详细解释" in feedback
        # 只有失败维度出现在反馈中
        assert "连贯性" not in feedback

    def test_build_improvement_feedback_all_passed(self):
        evaluator = TeachingQualityEvaluator()
        reports = {
            dim: QualityReport(
                dimension=dim,
                score=1.0,
                passed=True,
            )
            for dim in QualityDimension
        }
        feedback = evaluator.build_improvement_feedback(reports)
        assert feedback == ""

    def test_quality_report_to_dict(self):
        report = QualityReport(
            dimension=QualityDimension.CONTENT_UNDERSTANDING,
            score=0.85,
            passed=True,
            issues=[],
            suggestions=[],
        )
        d = report.to_dict()
        assert d["dimension"] == "content_understanding"
        assert d["score"] == 0.85
        assert d["passed"] is True

    def test_evaluate_missing_connectives(self):
        evaluator = TeachingQualityEvaluator()
        # 长内容但没有逻辑连接词
        content = "导数是变化率。" * 50
        reports = evaluator.evaluate(content, "导数", plan=None)

        coherence_report = reports[QualityDimension.CONTEXT_COHERENCE]
        assert any("连接词" in issue for issue in coherence_report.issues)

    def test_evaluate_with_multiple_representations(self):
        evaluator = TeachingQualityEvaluator()
        content = """
        因为导数是变化率，所以可以用图形理解。
        ```python
        # 教学要点：绘制导数图形
        import matplotlib
        print("导数:", 42)
        ```
        $f'(x)$ 表示变化率。首先理解定义，然后应用计算。
        你觉得这个结果合理吗？
        """
        reports = evaluator.evaluate(content, "导数", plan=None)

        pedagogy_report = reports[QualityDimension.PEDAGOGICAL_DESIGN]
        # 有公式+代码+图形 = 多元表达
        assert pedagogy_report.score > 0.5
