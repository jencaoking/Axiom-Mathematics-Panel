import os
import json
import numpy as np

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
        self.file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'skills.json')
        self.skills = []
        self._load_skills()

    def _load_skills(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.skills = json.load(f)
            except Exception as e:
                print(f"加载技能库失败: {e}")

    def save_skill(self, intent, abstract_code):
        """将 AI 提炼的通用代码存入技能库"""
        # 简单查重：如果意图已经极度相似，则覆盖或跳过
        for skill in self.skills:
            if skill['intent'] == intent:
                return

        self.skills.append({
            "intent": intent,
            "code": abstract_code
        })
        
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.skills, f, ensure_ascii=False, indent=4)
        print(f"🌟 新技能已沉淀至本地库: {intent}")

    def retrieve_relevant_skills(self, user_prompt, top_k=2, threshold=0.15):
        """利用 TF-IDF 检索与用户当前问题最匹配的历史成功经验"""
        if not self.skills:
            return []
            
        if not SKLEARN_AVAILABLE:
            # 如果没有 sklearn，降级为简单的关键词命中匹配
            return [s for s in self.skills if any(word in s['intent'] for word in user_prompt.split())][:top_k]

        try:
            corpus = [skill['intent'] for skill in self.skills]
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(corpus)
            
            query_vec = vectorizer.transform([user_prompt])
            similarities = cosine_similarity(query_vec, tfidf_matrix)[0]
            
            # 取出相似度最高的 top_k 个索引
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > threshold:
                    results.append(self.skills[idx])
            return results
        except Exception as e:
            print(f"RAG 检索失败: {e}")
            return []
