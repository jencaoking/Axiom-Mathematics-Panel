import yaml
import os

class PromptManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._load_prompts()
        return cls._instance

    def _load_prompts(self):
        yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'prompts.yaml')
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                self.prompts = yaml.safe_load(f)
        except Exception as e:
            print(f"无法加载 prompts.yaml: {e}")
            self.prompts = {}

    def get_system_prompt(self, key: str) -> str:
        return self.prompts.get(key, {}).get("system", "")

    def build(self, key: str, **kwargs) -> str:
        template = self.prompts.get(key, {}).get("user_template", "")
        if template:
            return template.format(**kwargs)
        return ""

prompt_manager = PromptManager()
