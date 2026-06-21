# mathlab/core/plugin_base.py
from abc import ABC, abstractmethod
from mathlab.core.extension_api import MathLabAPI

class MathLabPlugin(ABC):
    """所有 MathLab 插件的抽象基类"""
    
    name = "Unnamed Plugin"
    version = "1.0.0"
    author = "Unknown"
    description = "No description provided."

    @abstractmethod
    def on_activate(self, api: MathLabAPI):
        """插件被加载和激活时调用"""
        pass

    @abstractmethod
    def on_deactivate(self):
        """插件被禁用或系统关闭时调用，用于清理资源"""
        pass
