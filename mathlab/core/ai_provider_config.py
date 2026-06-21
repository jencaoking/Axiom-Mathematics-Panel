"""AI 提供商配置管理器。

线程安全的单例实现，负责加载、合并、缓存与持久化 AI 提供商配置。
配置由两层组成：
  1. 默认配置：mathlab/config/ai_providers.json (随项目分发，read-only)
  2. 用户配置：mathlab/config/user_ai_config.json (用户自定义，runtime 写入)
读取时优先返回用户配置覆盖项，未覆盖时回退到默认配置。
"""

import json
import threading
from pathlib import Path
from typing import Dict, Optional


class AIProviderConfig:
    """AI 提供商配置管理器 (线程安全的单例模式)。"""

    _instance: Optional["AIProviderConfig"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AIProviderConfig, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config_dir: Optional[Path] = None):
        # 确保单例只初始化一次，避免重复磁盘 I/O
        if self._initialized:
            return

        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.default_config_file = self.config_dir / "ai_providers.json"
        self.user_config_file = self.config_dir / "user_ai_config.json"

        self._config_cache: Dict[str, dict] = {}
        self._load_config()
        self._initialized = True

    # ── 加载与合并 ──────────────────────────────────────────────────────────
    def _load_config(self):
        """加载配置文件，合并默认配置和用户自定义配置。"""
        with self._lock:
            # 1. 加载默认配置
            try:
                if self.default_config_file.exists():
                    with open(self.default_config_file, "r", encoding="utf-8") as f:
                        self._config_cache = json.load(f).get("ai_providers", {})
                else:
                    self._config_cache = {}
            except Exception as e:
                print(f"[Warning] Failed to load default AI config: {e}")
                self._config_cache = {}

            # 2. 加载并合并用户自定义配置 (User Overrides)
            if self.user_config_file.exists():
                try:
                    with open(self.user_config_file, "r", encoding="utf-8") as f:
                        user_config = json.load(f).get("user_overrides", {})
                        self._merge_user_config(user_config)
                except Exception as e:
                    print(f"[Warning] Failed to load user AI config: {e}")

    def _merge_user_config(self, user_config: Dict):
        """深度合并用户配置：允许覆盖已有字段，也允许新增自定义提供商。"""
        for provider, overrides in user_config.items():
            if provider in self._config_cache and isinstance(self._config_cache[provider], dict):
                self._config_cache[provider].update(overrides)
            else:
                # 允许用户通过配置文件新增全新的提供商
                self._config_cache[provider] = overrides

    # ── 持久化 ──────────────────────────────────────────────────────────────
    def save_user_overrides(self, provider: str, overrides: dict):
        """允许通过 UI 修改配置并持久化到 user_ai_config.json。"""
        with self._lock:
            user_data: dict = {"user_overrides": {}}
            if self.user_config_file.exists():
                try:
                    with open(self.user_config_file, "r", encoding="utf-8") as f:
                        user_data = json.load(f)
                except Exception:
                    pass

            if "user_overrides" not in user_data:
                user_data["user_overrides"] = {}

            if provider not in user_data["user_overrides"]:
                user_data["user_overrides"][provider] = {}

            user_data["user_overrides"][provider].update(overrides)

            with open(self.user_config_file, "w", encoding="utf-8") as f:
                json.dump(user_data, f, indent=2, ensure_ascii=False)

        # 保存后立即热更新内存缓存
        self._load_config()

    # ── 访问器：获取配置的便利方法 ──────────────────────────────────────────
    def get_model_name(self, provider_value: str) -> str:
        """获取指定提供商的模型名称 (优先 custom_model，回退 default_model)。"""
        provider_config = self._config_cache.get(provider_value, {})
        return provider_config.get("custom_model") or provider_config.get("default_model", "")

    def get_api_endpoint(self, provider_value: str) -> str:
        """获取指定提供商的 API 端点 (优先 custom_endpoint，回退 api_endpoint)。"""
        provider_config = self._config_cache.get(provider_value, {})
        return provider_config.get("custom_endpoint") or provider_config.get("api_endpoint", "")

    def get_auth_type(self, provider_value: str) -> str:
        """获取指定提供商的认证类型 (默认 bearer，claude 系列使用 anthropic)。"""
        provider_config = self._config_cache.get(provider_value, {})
        return provider_config.get("auth_type", "bearer")

    def requires_api_key(self, provider_value: str) -> bool:
        """指定提供商是否需要 API 密钥 (本地 ollama 不需要)。"""
        provider_config = self._config_cache.get(provider_value, {})
        return bool(provider_config.get("requires_api_key", True))

    def get_all_providers(self) -> Dict[str, dict]:
        """返回当前已加载的全部提供商配置 (浅拷贝，避免外部误改缓存)。"""
        return dict(self._config_cache)

    # ── 热更新 ──────────────────────────────────────────────────────────────
    def reload_config(self):
        """暴露给外部的强制热更新接口。"""
        self._load_config()

    def reset_singleton(self):
        """测试或热重载时使用：重置单例 (下次构造会重新读盘)。"""
        with self._lock:
            AIProviderConfig._instance = None
