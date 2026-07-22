import os
import yaml
from mathlab.utils.logger import get_logger

logger = get_logger(__name__)


class PromptManager:
    """
    统一管理和渲染系统提示词的单例引擎
    """

    _instance = None
    _prompts = {}

    def __new__(cls, config_path=None):
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
            cls._instance._load_prompts(config_path)
        return cls._instance

    def _load_prompts(self, config_path):
        """从 yaml 文件加载提示词字典"""
        import sys

        if not config_path:
            # 默认去 config 目录下寻找 prompts.yaml
            if getattr(sys, "frozen", False):
                base_dir = sys._MEIPASS
                config_path = os.path.join(base_dir, "mathlab", "config", "prompts.yaml")
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                config_path = os.path.join(base_dir, "config", "prompts.yaml")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._prompts = yaml.safe_load(f) or {}
            logger.info(f"已成功加载魔法咒语库: {len(self._prompts)} 个场景模板")
        except Exception as e:
            logger.error(f"读取 prompts.yaml 失败: {e}")
            self._prompts = {}

    def get_system(self, scenario: str) -> str:
        """获取指定场景的系统提示词"""
        return self._prompts.get(scenario, {}).get("system", "")

    def build_user(self, scenario: str, **kwargs) -> str:
        """
        注入变量，构建动态的用户提示词
        用法示例: build_user("code_explainer", full_code="...", selected_code="...")
        """
        template = self._prompts.get(scenario, {}).get("user_template", "")
        if not template:
            return ""

        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"构建 Prompt 缺失必要参数 {e} (场景: {scenario})")
            return template


# 全局单例实例，供其他模块直接导入使用
prompt_manager = PromptManager()
