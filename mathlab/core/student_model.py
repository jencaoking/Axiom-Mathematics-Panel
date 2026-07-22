import json
import os
import threading
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from mathlab.utils.logger import get_logger

logger = get_logger(__name__)


class CognitiveLevel(Enum):
    """Bloom 认知层级（从低到高）。"""

    REMEMBER = 1  # 记忆：回忆事实、术语、基本概念
    UNDERSTAND = 2  # 理解：解释、总结、推断
    APPLY = 3  # 应用：在新情境中使用知识
    ANALYZE = 4  # 分析：分解、比较、组织
    EVALUATE = 5  # 评价：判断、批判、辩护
    CREATE = 6  # 创造：设计、构建、规划

    @classmethod
    def from_string(cls, level_str: str) -> "CognitiveLevel":
        mapping = {
            "记忆": cls.REMEMBER,
            "remember": cls.REMEMBER,
            "理解": cls.UNDERSTAND,
            "understand": cls.UNDERSTAND,
            "应用": cls.APPLY,
            "apply": cls.APPLY,
            "分析": cls.ANALYZE,
            "analyze": cls.ANALYZE,
            "评价": cls.EVALUATE,
            "evaluate": cls.EVALUATE,
            "创造": cls.CREATE,
            "create": cls.CREATE,
        }
        return mapping.get(level_str.lower().strip(), cls.UNDERSTAND)

    def to_chinese(self) -> str:
        names = {
            CognitiveLevel.REMEMBER: "记忆",
            CognitiveLevel.UNDERSTAND: "理解",
            CognitiveLevel.APPLY: "应用",
            CognitiveLevel.ANALYZE: "分析",
            CognitiveLevel.EVALUATE: "评价",
            CognitiveLevel.CREATE: "创造",
        }
        return names[self]


class LearningStyle(Enum):
    """学习偏好风格（UDL 多元表达原则）。"""

    VISUAL = "visual"  # 视觉型：偏好图表、几何图形
    ANALYTICAL = "analytical"  # 分析型：偏好公式推导、符号运算
    VERBAL = "verbal"  # 语言型：偏好文字解释、口语化讲解
    BALANCED = "balanced"  # 均衡型：多种方式交替


class InteractionType(Enum):
    """互动类型分类。"""

    QUESTION = "question"  # 提问
    ANSWER_CORRECT = "answer_correct"  # 正确回答
    ANSWER_WRONG = "answer_wrong"  # 错误回答
    DRAW_REQUEST = "draw_request"  # 绘图请求
    EXPLAIN_REQUEST = "explain_request"  # 解释请求
    SOLVE_REQUEST = "solve_request"  # 求解请求


class StudentModel:
    """学生认知模型：多维度追踪学习状态。

    维度包括：
    - knowledge_mastery: 各知识点的掌握度 (0.0~1.0)
    - cognitive_level: 当前 Bloom 认知层级
    - learning_style: 学习偏好风格
    - interaction_history: 互动历史记录
    - weakness_areas: 薄弱知识点列表
    - engagement_score: 参与度评分 (0.0~1.0)
    """

    def __init__(self, student_id: str = "default"):
        self.student_id = student_id
        self.knowledge_mastery: Dict[str, float] = {}
        self.cognitive_level: CognitiveLevel = CognitiveLevel.UNDERSTAND
        self.learning_style: LearningStyle = LearningStyle.BALANCED
        self.interaction_history: List[Dict] = []
        self.weakness_areas: List[str] = []
        self.engagement_score: float = 0.5
        self.total_interactions: int = 0
        self.correct_count: int = 0
        self._lock = threading.Lock()

    def record_interaction(
        self,
        interaction_type: InteractionType,
        knowledge_point: str = "",
        prompt_text: str = "",
        success: bool = None,
        cognitive_demand: CognitiveLevel = None,
    ):
        """记录一次学生互动并更新模型状态。

        Args:
            interaction_type: 互动类型
            knowledge_point: 涉及的知识点
            prompt_text: 用户原始输入
            success: 是否成功（解答正确/绘图成功），None 表示中性互动
            cognitive_demand: 本次互动所需的认知层级
        """
        with self._lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "type": interaction_type.value,
                "knowledge_point": knowledge_point,
                "prompt": prompt_text[:200],  # 截断防止过长
                "success": success,
                "cognitive_demand": (cognitive_demand.value if cognitive_demand else None),
            }
            self.interaction_history.append(entry)

            # 限制历史长度，保留最近 200 条
            if len(self.interaction_history) > 200:
                self.interaction_history = self.interaction_history[-200:]

            self.total_interactions += 1

            # 更新知识点掌握度
            if knowledge_point:
                self._update_mastery(knowledge_point, success)

            # 更新认知层级
            if cognitive_demand:
                self._update_cognitive_level(cognitive_demand, success)

            # 更新参与度
            self._update_engagement(interaction_type, success)

            # 更新学习偏好
            self._infer_learning_style(interaction_type)

            # 更新薄弱知识点
            self._refresh_weakness_areas()

    def _update_mastery(self, knowledge_point: str, success: Optional[bool]):
        """更新知识点掌握度。

        使用指数移动平均 (EMA) 平滑更新：
        - 正确回答：掌握度上升
        - 错误回答：掌握度下降
        - 中性互动：轻微上升（表示接触过）
        """
        current = self.knowledge_mastery.get(knowledge_point, 0.3)
        alpha = 0.15  # 学习率

        if success is True:
            current = current + alpha * (1.0 - current)
        elif success is False:
            current = current * (1.0 - alpha * 0.5)
        else:
            current = current + alpha * 0.1 * (1.0 - current)

        self.knowledge_mastery[knowledge_point] = max(0.0, min(1.0, current))

    def _update_cognitive_level(self, demand: CognitiveLevel, success: Optional[bool]):
        """根据互动结果动态调整学生的 Bloom 认知层级。"""
        if success is True:
            # 成功完成高认知需求任务 -> 提升层级
            if demand.value >= self.cognitive_level.value and self.cognitive_level.value < 6:
                self.cognitive_level = CognitiveLevel(self.cognitive_level.value + 1)
        elif success is False:
            # 高认知需求任务失败 -> 可能需要降级巩固
            if demand.value > self.cognitive_level.value and self.cognitive_level.value > 1:
                # 不直接降级，而是标记为薄弱（通过 weakness_areas 处理）
                pass

    def _update_engagement(self, interaction_type: InteractionType, success: Optional[bool]):
        """更新参与度评分。"""
        if success is True:
            self.correct_count += 1
            self.engagement_score = min(1.0, self.engagement_score + 0.02)
        elif success is False:
            self.engagement_score = max(0.1, self.engagement_score - 0.01)
        else:
            # 提问本身也是参与
            self.engagement_score = min(1.0, self.engagement_score + 0.01)

    def _infer_learning_style(self, interaction_type: InteractionType):
        """从互动类型推断学习偏好。

        通过统计最近 30 次互动的类型分布来推断偏好。
        """
        recent = self.interaction_history[-30:]
        if len(recent) < 5:
            return

        type_counts: Dict[str, int] = {}
        for entry in recent:
            t = entry["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        draw_ratio = type_counts.get("draw_request", 0) / len(recent)
        solve_ratio = type_counts.get("solve_request", 0) / len(recent)
        explain_ratio = type_counts.get("explain_request", 0) / len(recent)

        max_ratio = max(draw_ratio, solve_ratio, explain_ratio)
        if max_ratio < 0.3:
            self.learning_style = LearningStyle.BALANCED
        elif draw_ratio == max_ratio:
            self.learning_style = LearningStyle.VISUAL
        elif solve_ratio == max_ratio:
            self.learning_style = LearningStyle.ANALYTICAL
        else:
            self.learning_style = LearningStyle.VERBAL

    def _refresh_weakness_areas(self):
        """刷新薄弱知识点列表。"""
        self.weakness_areas = [kp for kp, mastery in self.knowledge_mastery.items() if mastery < 0.4]
        # 按掌握度升序排列（最薄弱的在前）
        self.weakness_areas.sort(key=lambda kp: self.knowledge_mastery.get(kp, 0))

    def get_mastery_level(self, knowledge_point: str) -> str:
        """返回知识点的掌握等级描述。"""
        mastery = self.knowledge_mastery.get(knowledge_point, 0.0)
        if mastery < 0.3:
            return "未掌握"
        elif mastery < 0.6:
            return "初步理解"
        elif mastery < 0.8:
            return "基本掌握"
        else:
            return "熟练掌握"

    def get_zpd_zone(self) -> tuple:
        """计算 Vygotsky 最近发展区。

        返回 (comfort_level, stretch_level):
        - comfort_level: 学生舒适区（当前能独立完成的认知层级）
        - stretch_level: 挑战区（需要引导才能完成的认知层级）
        """
        comfort = self.cognitive_level
        stretch = CognitiveLevel(min(comfort.value + 1, 6))
        return comfort, stretch

    def get_profile_summary(self) -> Dict:
        """返回学生画像摘要，供注入到 AI Prompt 中。"""
        comfort, stretch = self.get_zpd_zone()
        avg_mastery = (
            sum(self.knowledge_mastery.values()) / len(self.knowledge_mastery) if self.knowledge_mastery else 0.0
        )

        style_map = {
            LearningStyle.VISUAL: "视觉型（偏好图形、动画、几何直观）",
            LearningStyle.ANALYTICAL: "分析型（偏好公式推导、符号运算）",
            LearningStyle.VERBAL: "语言型（偏好文字解释、口语化讲解）",
            LearningStyle.BALANCED: "均衡型（多种方式交替）",
        }

        return {
            "cognitive_level": self.cognitive_level.to_chinese(),
            "comfort_zone": comfort.to_chinese(),
            "stretch_zone": stretch.to_chinese(),
            "learning_style": style_map[self.learning_style],
            "avg_mastery": f"{avg_mastery:.0%}",
            "weakness_areas": self.weakness_areas[:5],
            "engagement": f"{self.engagement_score:.0%}",
            "total_interactions": self.total_interactions,
            "accuracy": (
                f"{self.correct_count / self.total_interactions:.0%}" if self.total_interactions > 0 else "N/A"
            ),
            "top_mastered": self._get_top_mastered(5),
        }

    def _get_top_mastered(self, n: int) -> List[Dict]:
        """返回掌握度最高的 n 个知识点。"""
        if not self.knowledge_mastery:
            return []
        sorted_kp = sorted(self.knowledge_mastery.items(), key=lambda x: x[1], reverse=True)
        return [{"point": kp, "mastery": f"{m:.0%}"} for kp, m in sorted_kp[:n]]

    def to_dict(self) -> Dict:
        """序列化为可持久化的字典。"""
        return {
            "student_id": self.student_id,
            "knowledge_mastery": self.knowledge_mastery,
            "cognitive_level": self.cognitive_level.value,
            "learning_style": self.learning_style.value,
            "interaction_history": self.interaction_history,
            "weakness_areas": self.weakness_areas,
            "engagement_score": self.engagement_score,
            "total_interactions": self.total_interactions,
            "correct_count": self.correct_count,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "StudentModel":
        """从字典反序列化。"""
        model = cls(student_id=data.get("student_id", "default"))
        model.knowledge_mastery = data.get("knowledge_mastery", {})
        model.cognitive_level = CognitiveLevel(data.get("cognitive_level", CognitiveLevel.UNDERSTAND.value))
        model.learning_style = LearningStyle(data.get("learning_style", LearningStyle.BALANCED.value))
        model.interaction_history = data.get("interaction_history", [])
        model.weakness_areas = data.get("weakness_areas", [])
        model.engagement_score = data.get("engagement_score", 0.5)
        model.total_interactions = data.get("total_interactions", 0)
        model.correct_count = data.get("correct_count", 0)
        return model


class AdaptiveEngine:
    """自适应调度引擎：基于学生模型动态生成教学策略。

    核心功能：
    1. 根据学生认知层级 (Bloom) 调整教学步骤的难度梯度
    2. 根据 ZPD 理论确保内容在"最近发展区"内
    3. 根据 UDL 多元表达原则选择最适合的表达方式
    4. 生成个性化的 System Prompt 注入到 Agent 中
    """

    def __init__(self, student_model: StudentModel):
        self.student = student_model

    def build_adaptive_prompt(self, user_prompt: str) -> str:
        """构建注入到 PlannerAgent 的自适应教学策略 Prompt。

        这是整个自适应系统的核心输出：它将学生画像转化为
        LLM 可理解的教学指导，直接影响生成内容的质量。
        """
        profile = self.student.get_profile_summary()
        comfort, stretch = self.student.get_zpd_zone()

        # 薄弱知识点指导
        weakness_hint = ""
        if profile["weakness_areas"]:
            weakness_hint = (
                f"\n⚠️ 学生薄弱知识点：{', '.join(profile['weakness_areas'])}。"
                f"在教学过程中需要额外关注这些知识点，"
                f"优先用直观的例子帮助理解。"
            )

        # 学习偏好指导
        style_hint = self._get_style_hint(profile["learning_style"])

        # ZPD 难度指导
        zpd_hint = (
            f"\n🎯 最近发展区策略："
            f"\n  - 舒适区（{comfort.to_chinese()}）：学生可独立完成，用于建立信心"
            f"\n  - 挑战区（{stretch.to_chinese()}）：需要引导才能完成，用于突破成长"
            f"\n  教学步骤应从舒适区开始，逐步过渡到挑战区，确保'跳一跳够得着'。"
        )

        # 认知层级覆盖要求
        bloom_hint = self._get_bloom_coverage_hint()

        # 掌握度概览
        mastery_hint = ""
        if profile["top_mastered"]:
            mastered_str = ", ".join(f"{m['point']}({m['mastery']})" for m in profile["top_mastered"])
            mastery_hint = f"\n📊 已熟练掌握的知识点：{mastered_str}"

        adaptive_prompt = f"""【自适应教学策略 — 基于学生认知画像】

👤 学生认知画像：
  - 认知层级：{profile['cognitive_level']}（Bloom分类法）
  - 学习偏好：{profile['learning_style']}
  - 平均掌握度：{profile['avg_mastery']}
  - 参与度：{profile['engagement']}
  - 答题正确率：{profile['accuracy']}
{zpd_hint}
{bloom_hint}{weakness_hint}{mastery_hint}
{style_hint}

【教学策略要求】
1. 难度梯度：教学步骤从{comfort.to_chinese()}层级开始，逐步提升到{stretch.to_chinese()}层级。
2. 个性化表达：根据学生的学习偏好调整讲解方式。
3. 薄弱知识点强化：如果本次问题涉及薄弱知识点，增加铺垫步骤和直观示例。
4. 苏格拉底式引导：不要直接给答案，通过提问引导学生自主发现规律。
5. 即时反馈：在每个步骤后评估学生是否跟上，及时调整难度。"""

        return adaptive_prompt

    def _get_style_hint(self, style_desc: str) -> str:
        """根据学习偏好生成表达方式指导。"""
        if "视觉型" in style_desc:
            return (
                "\n🎨 表达策略（视觉型学生）："
                "\n  - 优先使用几何画板绘图来辅助讲解"
                "\n  - 用图形、颜色、动画演示抽象概念"
                "\n  - 减少纯文字描述，增加'请看这张图'式引导"
            )
        elif "分析型" in style_desc:
            return (
                "\n📝 表达策略（分析型学生）："
                "\n  - 优先使用公式推导和符号运算"
                "\n  - 展示完整的数学证明过程"
                "\n  - 强调逻辑严密性和步骤完整性"
            )
        elif "语言型" in style_desc:
            return (
                "\n💬 表达策略（语言型学生）："
                "\n  - 用通俗易懂的自然语言讲解"
                "\n  - 多用类比和生活中的例子"
                "\n  - 减少公式堆砌，用文字解释数学含义"
            )
        else:
            return (
                "\n🔀 表达策略（均衡型学生）："
                "\n  - 交替使用图形、公式和文字三种表达方式"
                "\n  - 每个概念用至少两种方式呈现以加深理解"
            )

    def _get_bloom_coverage_hint(self) -> str:
        """生成 Bloom 认知层级覆盖要求。"""
        current = self.student.cognitive_level
        if current.value <= 2:
            return (
                "\n📚 认知覆盖要求（基础阶段）："
                "\n  侧重'记忆'和'理解'层级，通过反复练习巩固基础概念。"
                "\n  在学生准备好后，适当引入'应用'层级的问题。"
            )
        elif current.value <= 4:
            return (
                "\n📚 认知覆盖要求（进阶阶段）："
                "\n  侧重'应用'和'分析'层级，鼓励学生拆解问题、比较方法。"
                "\n  适当引入'评价'层级的批判性思考问题。"
            )
        else:
            return (
                "\n📚 认知覆盖要求（高阶阶段）："
                "\n  侧重'评价'和'创造'层级，鼓励学生提出新解法、构建模型。"
                "\n  引导学生从多角度审视问题，培养数学创造力。"
            )

    def classify_interaction(self, user_prompt: str, success: bool = None) -> InteractionType:
        """从用户输入文本分类互动类型。"""
        prompt_lower = user_prompt.lower()

        draw_keywords = ["画", "绘制", "作图", "draw", "plot", "render", "图形"]
        solve_keywords = [
            "求解",
            "计算",
            "解方程",
            "积分",
            "微分",
            "solve",
            "calculate",
        ]
        explain_keywords = ["解释", "为什么", "讲解", "explain", "why", "证明"]

        if any(kw in prompt_lower for kw in draw_keywords):
            return InteractionType.DRAW_REQUEST
        if any(kw in prompt_lower for kw in solve_keywords):
            return InteractionType.SOLVE_REQUEST
        if any(kw in prompt_lower for kw in explain_keywords):
            return InteractionType.EXPLAIN_REQUEST

        return InteractionType.QUESTION

    def extract_knowledge_point(self, user_prompt: str) -> str:
        """从用户输入中提取涉及的知识点。

        使用关键词匹配的方式提取，后续可升级为 LLM 提取。
        """
        kp_keywords = {
            "勾股定理": ["勾股", "直角三角形", "pythagor"],
            "三角函数": ["三角", "正弦", "余弦", "正切", "sin", "cos", "tan"],
            "导数": ["导数", "求导", "derivative"],
            "积分": ["积分", "integrate", "积分运算"],
            "极限": ["极限", "limit"],
            "向量": ["向量", "vector"],
            "矩阵": ["矩阵", "matrix"],
            "概率": ["概率", "probability"],
            "统计": ["统计", "statistics", "均值", "方差"],
            "圆": ["圆", "circle", "半径", "直径"],
            "直线": ["直线", "line", "斜率", "截距"],
            "椭圆": ["椭圆", "ellipse"],
            "抛物线": ["抛物线", "parabola"],
            "双曲线": ["双曲线", "hyperbola"],
            "多边形": ["多边形", "polygon", "三角形", "四边形"],
            "复数": ["复数", "complex"],
            "级数": ["级数", "series", "等差", "等比"],
            "微分方程": ["微分方程", "differential equation"],
        }

        prompt_lower = user_prompt.lower()
        for kp, keywords in kp_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                return kp
        return ""

    def suggest_difficulty_adjustment(self, recent_success_rate: float) -> str:
        """根据近期成功率建议难度调整方向。"""
        if recent_success_rate > 0.8:
            return "提升难度，引入更高认知层级的挑战"
        elif recent_success_rate > 0.5:
            return "维持当前难度，适当增加变式练习"
        elif recent_success_rate > 0.3:
            return "降低难度，回到基础概念巩固"
        else:
            return "大幅降低难度，从最基础的知识点重新开始"

    def get_recommended_cognitive_demand(self) -> CognitiveLevel:
        """根据 ZPD 推荐本次教学内容的认知需求层级。"""
        comfort, stretch = self.student.get_zpd_zone()
        # 如果参与度高且掌握度好，直接挑战
        if self.student.engagement_score > 0.7:
            return stretch
        # 否则从舒适区开始
        return comfort


class StudentModelManager:
    """学生模型持久化管理器。

    负责学生画像的保存、加载和多学生管理。
    数据存储在 ~/.mathlab/student_profiles/ 目录下。
    """

    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            storage_dir = os.path.join(os.path.expanduser("~"), ".mathlab", "student_profiles")
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self._models: Dict[str, StudentModel] = {}
        self._lock = threading.RLock()  # 可重入锁，允许 save_all 调用 save_model

    def get_model(self, student_id: str = "default") -> StudentModel:
        """获取学生模型，不存在则创建新的。"""
        with self._lock:
            if student_id not in self._models:
                self._models[student_id] = self._load_model(student_id)
            return self._models[student_id]

    def save_model(self, student_id: str = "default"):
        """持久化保存学生模型。"""
        with self._lock:
            model = self._models.get(student_id)
            if model is None:
                return
            filepath = os.path.join(self.storage_dir, f"{student_id}.json")
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(model.to_dict(), f, ensure_ascii=False, indent=2)
                logger.info(f"学生画像已保存: {student_id}")
            except Exception as e:
                logger.error(f"保存学生画像失败: {e}")

    def save_all(self):
        """保存所有已加载的学生模型。"""
        with self._lock:
            for student_id in self._models:
                self.save_model(student_id)

    def _load_model(self, student_id: str) -> StudentModel:
        """从磁盘加载学生模型，不存在则创建新的。"""
        filepath = os.path.join(self.storage_dir, f"{student_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"学生画像已加载: {student_id}")
                return StudentModel.from_dict(data)
            except Exception as e:
                logger.error(f"加载学生画像失败: {e}")
        return StudentModel(student_id=student_id)

    def reset_model(self, student_id: str = "default"):
        """重置学生模型（清除所有学习记录）。"""
        with self._lock:
            self._models[student_id] = StudentModel(student_id=student_id)
            filepath = os.path.join(self.storage_dir, f"{student_id}.json")
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
            logger.info(f"学生画像已重置: {student_id}")
