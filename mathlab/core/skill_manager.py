import json
import os
import threading

import numpy as np

try:
    from mathlab.utils.logger import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# 利用现有环境中的 sklearn 进行轻量级文本向量化
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class SkillLibrary:
    def __init__(self):
        # 技能库持久化路径
        self.file_path = os.path.join(os.path.dirname(__file__), "..", "data", "skills.json")
        self.skills = []
        self._lock = threading.Lock()  # BUG 2 修复：线程安全锁
        self._vectorizer = None  # BUG 8 修复：TF-IDF 缓存
        self._tfidf_matrix = None
        self._load_skills()

    def _load_skills(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.skills = json.load(f)
            except Exception as e:
                logger.error(f"加载技能库失败: {e}")

    def _invalidate_cache(self):
        """技能库变更后使 TF-IDF 缓存失效"""
        self._vectorizer = None
        self._tfidf_matrix = None

    def save_skill(self, intent, abstract_code):
        """将 AI 提炼的通用代码存入技能库"""
        with self._lock:  # BUG 2 修复：加锁保护读写操作
            # 简单查重：如果意图已经极度相似，则覆盖或跳过
            for skill in self.skills:
                if skill["intent"] == intent:
                    return

            self.skills.append({"intent": intent, "code": abstract_code})

            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.skills, f, ensure_ascii=False, indent=4)

            self._invalidate_cache()  # BUG 8 修复：写入后使缓存失效
            logger.info(f"🌟 新技能已沉淀至本地库: {intent}")

    def retrieve_relevant_skills(self, user_prompt, top_k=2, threshold=0.15):
        """利用 TF-IDF 检索与用户当前问题最匹配的历史成功经验"""
        with self._lock:  # BUG 2 修复：加锁保护读操作
            if not self.skills:
                return []

            if not SKLEARN_AVAILABLE:
                # 如果没有 sklearn，降级为简单的关键词命中匹配
                return [s for s in self.skills if any(word in s["intent"] for word in user_prompt.split())][:top_k]

            try:
                corpus = [skill["intent"] for skill in self.skills]

                # BUG 8 修复：延迟初始化并缓存 vectorizer 和 tfidf_matrix
                if self._vectorizer is None or self._tfidf_matrix is None:
                    self._vectorizer = TfidfVectorizer()
                    self._tfidf_matrix = self._vectorizer.fit_transform(corpus)

                query_vec = self._vectorizer.transform([user_prompt])
                similarities = cosine_similarity(query_vec, self._tfidf_matrix)[0]

                # 取出相似度最高的 top_k 个索引
                top_indices = np.argsort(similarities)[::-1][:top_k]

                results = []
                for idx in top_indices:
                    if similarities[idx] > threshold:
                        results.append(self.skills[idx])
                return results
            except Exception as e:
                logger.error(f"RAG 检索失败: {e}")
                return []
