"""教学法引导引擎：将教育理论注入 AI 内容生成与质量评估。

参考论文《From MOOC to MAIC》的三维度评估框架，实现：
1. PedagogicalPromptBuilder — 基于 Bloom/ZPD/UDL/Socratic 构建教学法约束提示词
2. TeachingQualityEvaluator — 三维度教学质量评估（内容理解/连贯性/教学设计）
3. PedagogicalConstraint — 可量化的教学法约束规则集

三大教学理论应用：
- Bloom's Taxonomy: 确保教学步骤覆盖从记忆到创造的认知层级梯度
- Vygotsky's ZPD: 内容难度落在"最近发展区"，跳一跳够得着
- UDL (Universal Design for Learning): 多元表达、多元参与、多元表达方式
- Socratic Method: 苏格拉底式提问引导，禁止直接给答案
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from mathlab.core.student_model import (
    AdaptiveEngine,
    CognitiveLevel,
    LearningStyle,
    StudentModel,
)
from mathlab.utils.logger import get_logger

logger = get_logger(__name__)


class TeachingPrinciple(Enum):
    """教学法原则枚举。"""

    BLOOM_TAXONOMY = "bloom_taxonomy"  # Bloom 认知层级覆盖
    ZPD_DIFFICULTY = "zpd_difficulty"  # 最近发展区难度控制
    UDL_REPRESENTATION = "udl_representation"  # UDL 多元表达
    SOCRATIC_GUIDED = "socratic_guided"  # 苏格拉底引导式
    SCAFFOLDING = "scaffolding"  # 脚手架式渐进
    INSTANT_FEEDBACK = "instant_feedback"  # 即时反馈


@dataclass
class PedagogicalConstraint:
    """单条教学法约束规则。"""

    principle: TeachingPrinciple
    description: str
    check_pattern: Optional[str] = None  # 正则检查模式
    violation_hint: str = ""  # 违规时的修正提示

    def validate(self, content: str) -> Tuple[bool, str]:
        """验证内容是否满足此约束。

        Returns:
            (passed, message): 是否通过，未通过时的修正建议
        """
        if not self.check_pattern:
            return True, ""
        if re.search(self.check_pattern, content, re.IGNORECASE):
            return False, self.violation_hint
        return True, ""


class PedagogicalPromptBuilder:
    """教学法提示词构建器。

    将教育理论转化为 LLM 可执行的教学约束，
    注入到 Agent 的 System Prompt 中，引导生成内容符合教育原则。
    """

    # Bloom 各层级的详细行为动词与教学活动指导
    BLOOM_GUIDELINES = {
        CognitiveLevel.REMEMBER: {
            "verbs": "回忆、列举、描述、识别、命名、陈述",
            "activities": "概念复习、术语匹配、事实回忆",
            "question_stems": "什么是...？请列举...的要素。",
        },
        CognitiveLevel.UNDERSTAND: {
            "verbs": "解释、总结、推断、分类、比较",
            "activities": "概念解释、关系图绘制、用自己的话复述",
            "question_stems": "请用自己的话解释...。...和...有什么区别？",
        },
        CognitiveLevel.APPLY: {
            "verbs": "计算、求解、演示、运用、实施",
            "activities": "公式应用、例题求解、算法实现",
            "question_stems": "请用...方法求解...。在...情境下如何应用...？",
        },
        CognitiveLevel.ANALYZE: {
            "verbs": "分解、比较、对比、辨别、组织",
            "activities": "多解法比较、条件分析、错误诊断",
            "question_stems": "比较...和...的异同。分析...的条件依赖关系。",
        },
        CognitiveLevel.EVALUATE: {
            "verbs": "判断、评估、批判、辩护、选择",
            "activities": "方法评价、最优解选择、证明检验",
            "question_stems": "哪种方法更优？为什么？请评估...的合理性。",
        },
        CognitiveLevel.CREATE: {
            "verbs": "设计、构建、规划、综合、生成",
            "activities": "建模、出题、新解法构造",
            "question_stems": "请设计一个...的方案。构建一个满足...的模型。",
        },
    }

    # UDL 三原则的中文指导
    UDL_PRINCIPLES = {
        "representation": (
            "多元表达：同一概念用至少两种方式呈现（如公式+图形、文字+数值）。" "提供信息的不同感知方式，降低认知负荷。"
        ),
        "engagement": ("多元参与：提供探索性任务而非纯听讲。" "设置适度挑战，连接学生已有经验，维持学习动机。"),
        "expression": (
            "多元表达方式：允许学生用画图、公式、文字等多种方式回答。" "不要限定唯一的解题路径，鼓励创造性表达。"
        ),
    }

    def __init__(self, student_model: Optional[StudentModel] = None):
        self.student = student_model
        self._adaptive_engine = AdaptiveEngine(student_model) if student_model else None

    def build_decomposition_constraint(self) -> str:
        """构建问题拆解阶段的教学法约束。

        指导 PlannerAgent 如何将数学问题拆解为符合教育原则的教学步骤。
        """
        constraints = [
            self._build_bloom_ladder_constraint(),
            self._build_zpd_constraint(),
            self._build_scaffolding_constraint(),
            self._build_socratic_constraint(),
        ]

        if self.student:
            constraints.append(self._build_udl_constraint())

        return "\n".join(constraints)

    def build_step_execution_constraint(
        self,
        step_title: str,
        cognitive_level: str,
        hint: str = "",
    ) -> str:
        """构建单个教学步骤的执行约束。

        指导子 Agent 在执行具体步骤时遵循教学法要求。

        Args:
            step_title: 步骤标题
            cognitive_level: 该步骤的 Bloom 认知层级
            hint: 教学提示
        """
        level = CognitiveLevel.from_string(cognitive_level)
        bloom_guide = self.BLOOM_GUIDELINES.get(level, {})
        verbs = bloom_guide.get("verbs", "")
        activities = bloom_guide.get("activities", "")
        question_stems = bloom_guide.get("question_stems", "")

        constraint = f"""【教学法约束 — 步骤执行指导】

📌 当前步骤：{step_title}
📌 认知层级：{level.to_chinese()}（Bloom 第{level.value}层）
📌 教学提示：{hint}

🎯 Bloom 层级行为指导：
  - 适用动词：{verbs}
  - 推荐活动：{activities}
  - 提问范式：{question_stems}

📜 执行规则：
  1. 内容必须匹配「{level.to_chinese()}」认知层级，不要越级
  2. 使用苏格拉底式提问，以引导性问题结尾，不直接给答案
  3. 代码/公式后必须有中文注释或解释，不能只给结果
  4. 如果涉及画图，用图形辅助说明抽象概念"""

        # 注入 UDL 多元表达约束
        if self.student:
            constraint += f"\n\n{self._build_udl_constraint()}"

        return constraint

    def build_code_generation_constraint(self, user_prompt: str) -> str:
        """构建代码生成阶段的教学法约束。

        指导 BaseMathAgent 在生成 Python 代码时遵循教育原则，
        确保生成的代码本身具有教学价值。
        """
        constraint = """【教学法约束 — 代码生成质量】

生成的代码必须满足以下教育原则：
1. **可读性优先**：变量名语义化，添加中文注释解释数学原理
2. **分步展示**：复杂计算拆分为多个中间步骤，每步打印中间结果
3. **可视化辅助**：如果涉及几何/函数，调用画板 API 绘制图形
4. **错误处理**：包含输入验证和异常处理，展示良好的编程习惯
5. **教学注释**：在关键算法处添加 '# 教学要点：...' 注释解释为什么这样做"""

        if self._adaptive_engine:
            kp = self._adaptive_engine.extract_knowledge_point(user_prompt)
            if kp:
                mastery = self.student.get_mastery_level(kp)
                if mastery in ("未掌握", "初步理解"):
                    constraint += (
                        f"\n6. **薄弱知识点强化**：检测到学生对「{kp}」"
                        f"掌握度为「{mastery}」，请在代码中增加更详细的"
                        f"注释和中间步骤展示，降低理解门槛。"
                    )

        return constraint

    def _build_bloom_ladder_constraint(self) -> str:
        """构建 Bloom 认知层级梯度约束。"""
        current_level = CognitiveLevel.UNDERSTAND
        if self.student:
            current_level = self.student.cognitive_level

        comfort, stretch = (
            self.student.get_zpd_zone() if self.student else (CognitiveLevel.UNDERSTAND, CognitiveLevel.APPLY)
        )

        return f"""【Bloom 认知层级梯度约束】
教学步骤必须形成认知梯度，从低到高覆盖 Bloom 分类法：
  第1层 记忆 → 第2层 理解 → 第3层 应用 → 第4层 分析 → 第5层 评价 → 第6层 创造

当前学生认知层级：{current_level.to_chinese()}
  - 起始步骤应从「{comfort.to_chinese()}」层级开始（建立信心）
  - 结束步骤应达到「{stretch.to_chinese()}」层级（突破成长）
  - 中间步骤逐级递进，不要跳级超过2个层级

每个步骤必须标注 cognitive_level 字段，取值范围：记忆/理解/应用/分析/评价/创造"""

    def _build_zpd_constraint(self) -> str:
        """构建 ZPD 最近发展区约束。"""
        if not self.student:
            return ""

        comfort, stretch = self.student.get_zpd_zone()
        profile = self.student.get_profile_summary()

        weakness_hint = ""
        if profile["weakness_areas"]:
            weakness_hint = (
                f"\n  ⚠️ 学生薄弱知识点：{', '.join(profile['weakness_areas'])}。"
                f"如果本问题涉及这些知识点，在低认知层级增加巩固步骤。"
            )

        return f"""【Vygotsky 最近发展区 (ZPD) 约束】
  舒适区（{comfort.to_chinese()}）：学生可独立完成 → 用于热身和建立信心
  挑战区（{stretch.to_chinese()}）：需要引导才能完成 → 用于突破和成长
  恐慌区（超出{stretch.to_chinese()}）：学生无法完成 → 禁止直接跳到此区

  规则：教学步骤必须从舒适区开始，逐步过渡到挑战区，绝不直接进入恐慌区。{weakness_hint}"""

    def _build_scaffolding_constraint(self) -> str:
        """构建脚手架式渐进约束。"""
        return """【脚手架式渐进教学约束】
  1. 每个步骤只引入一个新概念或新技巧
  2. 后续步骤必须建立在前序步骤的成果之上
  3. 复杂问题先给出部分解答作为"脚手架"，再让学生补充
  4. 如果前序步骤失败，后续步骤应降低难度提供补救路径"""

    def _build_socratic_constraint(self) -> str:
        """构建苏格拉底式引导约束。"""
        return """【苏格拉底式引导约束】
  1. 禁止在非最后步骤直接给出最终答案
  2. 每个步骤的输出应以引导式问题结尾
  3. 用"你觉得下一步该怎么做？"而非"答案是..."
  4. 当学生可能出错时，用反例提问引导自我发现
  5. 最后一步可以给出完整解答，但必须附带"为什么这样解"的解释"""

    def _build_udl_constraint(self) -> str:
        """构建 UDL 多元表达约束。"""
        style_hint = ""
        if self.student:
            style_map = {
                LearningStyle.VISUAL: "学生偏好视觉表达，优先使用图形/动画",
                LearningStyle.ANALYTICAL: "学生偏好分析表达，优先使用公式推导",
                LearningStyle.VERBAL: "学生偏好语言表达，优先使用文字解释",
                LearningStyle.BALANCED: "学生均衡偏好，交替使用多种表达",
            }
            style_hint = f"\n  当前学生偏好：{style_map.get(self.student.learning_style, '均衡')}"

        udl_text = "\n".join(f"  - {k}：{v}" for k, v in self.UDL_PRINCIPLES.items())

        return f"""【UDL 多元表达约束】
{udl_text}{style_hint}
  规则：每个核心概念至少用两种方式呈现（如公式+图形、数值+文字）"""


class QualityDimension(Enum):
    """教学质量评估维度。"""

    CONTENT_UNDERSTANDING = "content_understanding"  # 内容理解
    CONTEXT_COHERENCE = "context_coherence"  # 上下文连贯性
    PEDAGOGICAL_DESIGN = "pedagogical_design"  # 教学设计


@dataclass
class QualityReport:
    """教学质量评估报告。"""

    dimension: QualityDimension
    score: float  # 0.0~1.0
    passed: bool  # score >= threshold
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 2),
            "passed": self.passed,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


class TeachingQualityEvaluator:
    """教学质量评估器。

    从三个维度评估 AI 生成的教学内容质量：
    1. 内容理解 (Content Understanding)：内容是否准确反映教学目标
    2. 上下文连贯性 (Context Coherence)：教学叙事是否一致且逻辑流畅
    3. 教学设计 (Pedagogical Design)：是否遵循教育原则
    """

    def __init__(self, student_model: Optional[StudentModel] = None, pass_threshold: float = 0.6):
        self.student = student_model
        self.pass_threshold = pass_threshold
        self._prompt_builder = PedagogicalPromptBuilder(student_model)

    def evaluate(
        self,
        content: str,
        user_prompt: str,
        plan: Optional[dict] = None,
    ) -> Dict["QualityDimension", QualityReport]:
        """全面评估教学内容质量。

        Args:
            content: AI 生成的教学内容（代码+输出）
            user_prompt: 原始用户问题
            plan: 教学大纲（如果有）

        Returns:
            各维度的评估报告字典
        """
        reports = {}
        reports[QualityDimension.CONTENT_UNDERSTANDING] = self._evaluate_content_understanding(content, user_prompt)
        reports[QualityDimension.CONTEXT_COHERENCE] = self._evaluate_context_coherence(content, plan)
        reports[QualityDimension.PEDAGOGICAL_DESIGN] = self._evaluate_pedagogical_design(content, user_prompt)
        return reports

    def _evaluate_content_understanding(self, content: str, user_prompt: str) -> QualityReport:
        """评估内容理解维度：生成内容是否准确回应了用户问题。"""
        issues = []
        suggestions = []

        # 检查 1：内容是否为空或过短
        if len(content.strip()) < 20:
            issues.append("生成内容过短，可能未充分回答问题")
            suggestions.append("增加详细解释和中间步骤")

        # 检查 2：是否包含数学公式/代码
        has_math = bool(re.search(r"\$.*\$|\\[a-zA-Z]+|numpy|scipy|def\s+", content))
        if not has_math:
            issues.append("内容缺少数学公式或代码，教学深度不足")
            suggestions.append("添加 LaTeX 公式或 Python 代码来展示数学原理")

        # 检查 3：是否包含解释性文字
        has_explanation = bool(re.search(r"因为|所以|由于|因此|这意味着|原理是|解释", content))
        if not has_explanation:
            issues.append("缺少解释性文字，学生可能无法理解为什么这样做")
            suggestions.append("在代码/公式后添加'为什么'的解释")

        # 检查 4：是否有中间步骤展示
        has_steps = bool(
            re.search(
                r"步骤|第.步|Step\s|print\(|输出结果|中间结果|计算结果",
                content,
                re.IGNORECASE,
            )
        )
        if not has_steps:
            issues.append("缺少中间步骤展示，学生看不到推理过程")
            suggestions.append("将计算拆分为多个步骤，每步打印中间结果")

        score = 1.0 - len(issues) * 0.2
        score = max(0.0, min(1.0, score))

        return QualityReport(
            dimension=QualityDimension.CONTENT_UNDERSTANDING,
            score=score,
            passed=score >= self.pass_threshold,
            issues=issues,
            suggestions=suggestions,
        )

    def _evaluate_context_coherence(self, content: str, plan: Optional[dict]) -> QualityReport:
        """评估上下文连贯性维度：教学叙事是否一致且逻辑流畅。"""
        issues = []
        suggestions = []

        if plan and "steps" in plan:
            steps = plan["steps"]
            # 检查：教学步骤是否有认知层级梯度
            levels = []
            for step in steps:
                cl = step.get("cognitive_level", "理解")
                level = CognitiveLevel.from_string(cl)
                levels.append(level.value)

            if levels:
                # 检查是否大致递增（允许个别持平）
                increases = sum(1 for i in range(1, len(levels)) if levels[i] >= levels[i - 1])
                ratio = increases / max(1, len(levels) - 1)
                if ratio < 0.6:
                    issues.append(f"认知层级梯度不合理（递增率{ratio:.0%}），" f"步骤间难度跳跃过大")
                    suggestions.append("调整步骤顺序，确保认知层级大致递增")

                # 检查是否跨越太多层级
                level_span = max(levels) - min(levels)
                if level_span > 4:
                    issues.append(f"认知层级跨度过大（{level_span}层），" f"学生可能无法跟上")
                    suggestions.append("增加中间过渡步骤，减小层级跨度")

        # 检查内容中的逻辑连接词
        connectives = re.findall(r"首先|其次|然后|接着|最后|因此|所以|综上|接下来", content)
        if len(connectives) < 2 and len(content) > 200:
            issues.append("缺少逻辑连接词，叙事连贯性不足")
            suggestions.append("使用'首先/其次/最后'等连接词增强逻辑流畅度")

        score = 1.0 - len(issues) * 0.25
        score = max(0.0, min(1.0, score))

        return QualityReport(
            dimension=QualityDimension.CONTEXT_COHERENCE,
            score=score,
            passed=score >= self.pass_threshold,
            issues=issues,
            suggestions=suggestions,
        )

    def _evaluate_pedagogical_design(self, content: str, user_prompt: str) -> QualityReport:
        """评估教学设计维度：是否遵循教育原则。"""
        issues = []
        suggestions = []
        constraints = self._build_pedagogical_constraints()

        for constraint in constraints:
            passed, hint = constraint.validate(content)
            if not passed:
                issues.append(f"违反「{constraint.principle.value}」原则：{hint}")
                suggestions.append(hint)

        # 检查苏格拉底式引导：是否有提问
        has_question = bool(re.search(r"[？\?]\s*$", content, re.MULTILINE))
        if not has_question and len(content) > 100:
            issues.append("缺少引导式提问，不符合苏格拉底教学法")
            suggestions.append("在内容末尾添加启发式问题引导学生思考")

        # 检查 UDL 多元表达：是否有多种表达方式
        has_formula = bool(re.search(r"\$.*\$|\\[a-zA-Z]+", content))
        has_code = bool(re.search(r"```python|def\s+|import\s+", content))
        has_visual = bool(re.search(r"画图|绘制|draw\(|plot\(|画板", content))
        representation_count = sum([has_formula, has_code, has_visual])
        if representation_count < 2 and len(content) > 200:
            issues.append(f"表达方式单一（仅{representation_count}种），不符合UDL多元表达原则")
            suggestions.append("用至少两种方式呈现核心概念（公式+图形/代码+文字）")

        score = 1.0 - len(issues) * 0.3
        score = max(0.0, min(1.0, score))

        return QualityReport(
            dimension=QualityDimension.PEDAGOGICAL_DESIGN,
            score=score,
            passed=score >= self.pass_threshold,
            issues=issues,
            suggestions=suggestions,
        )

    def _build_pedagogical_constraints(self) -> List[PedagogicalConstraint]:
        """构建教学法约束规则集。"""
        return [
            PedagogicalConstraint(
                principle=TeachingPrinciple.SOCRATIC_GUIDED,
                description="禁止直接给最终答案（非最后步骤）",
                check_pattern=r"答案是[:：]|最终结果[:：]|正确答案[:：]",
                violation_hint="不应直接给出答案，应使用引导式提问让学生自己发现",
            ),
            PedagogicalConstraint(
                principle=TeachingPrinciple.SCAFFOLDING,
                description="禁止一步到位跳过推理过程",
                check_pattern=r"显然|很明显|trivially|一目了然",
                violation_hint="不应使用'显然'等词跳过推理，需要展示中间步骤",
            ),
        ]

    def get_overall_score(self, reports: Dict[QualityDimension, QualityReport]) -> float:
        """计算总体质量评分（加权平均）。"""
        weights = {
            QualityDimension.CONTENT_UNDERSTANDING: 0.4,
            QualityDimension.CONTEXT_COHERENCE: 0.25,
            QualityDimension.PEDAGOGICAL_DESIGN: 0.35,
        }
        total = sum(weights[dim] * reports[dim].score for dim in reports)
        return round(total, 2)

    def build_improvement_feedback(self, reports: Dict[QualityDimension, QualityReport]) -> str:
        """根据评估报告生成改进反馈 Prompt。

        当质量评估不通过时，将此反馈注入到 LLM 的对话历史中，
        引导 AI 修正生成内容。
        """
        failed_dims = [r for r in reports.values() if not r.passed]
        if not failed_dims:
            return ""

        feedback_parts = ["【教学质量评估反馈 — 请修正以下问题】"]
        for report in failed_dims:
            dim_name = {
                QualityDimension.CONTENT_UNDERSTANDING: "内容理解",
                QualityDimension.CONTEXT_COHERENCE: "连贯性",
                QualityDimension.PEDAGOGICAL_DESIGN: "教学设计",
            }.get(report.dimension, report.dimension.value)
            feedback_parts.append(f"\n❌ {dim_name}（得分: {report.score:.0%}）:")
            for issue in report.issues:
                feedback_parts.append(f"  - 问题：{issue}")
            for sug in report.suggestions:
                feedback_parts.append(f"  - 建议：{sug}")

        feedback_parts.append("\n请根据以上反馈修正你的回答。")
        return "\n".join(feedback_parts)
