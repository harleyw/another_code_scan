import os
import json
from typing import Optional

class ConfigManager:
    """配置管理器，用于读取和管理配置文件中的key"""
    
    def __init__(self, config_path: str = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        # 如果没有提供配置路径，使用相对于项目根目录的默认路径
        if config_path is None:
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 计算项目根目录（util目录的父目录）
            project_root = os.path.dirname(current_dir)
            # 设置默认配置路径
            config_path = os.path.join(project_root, "cfg", "config.json")
            
        self.config_path = config_path
        self.config_data = self._load_config()
    
    def _load_config(self) -> dict:
        """加载配置文件
        
        Returns:
            dict: 配置数据
        """
        if not os.path.exists(self.config_path):
            # 如果配置文件不存在，创建一个空的配置文件
            default_config = {
                "github_token": "",
                "dashscope_api_key": "",
                "openai_api_key": ""
            }
            self._save_config(default_config)
            return default_config
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_config(self, config_data: dict):
        """保存配置文件
        
        Args:
            config_data: 配置数据
        """
        # 确保配置目录存在
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def get_github_token(self) -> Optional[str]:
        """获取GitHub token
        
        Returns:
            str: GitHub token，如果未设置则返回None
        """
        token = self.config_data.get("github_token")
        if not token:
            # 如果配置文件中没有token，则尝试从环境变量获取
            token = os.environ.get("GITHUB_TOKEN")
        return token if token else None
    
    def get_dashscope_api_key(self) -> Optional[str]:
        """获取DashScope API key
        
        Returns:
            str: DashScope API key，如果未设置则返回None
        """
        api_key = self.config_data.get("dashscope_api_key")
        if not api_key:
            # 如果配置文件中没有api key，则尝试从环境变量获取
            api_key = os.environ.get("DASHSCOPE_API_KEY")
        return api_key if api_key else None
    
    def get_openai_api_key(self) -> Optional[str]:
        """获取OpenAI API key
        
        Returns:
            str: OpenAI API key，如果未设置则返回None
        """
        api_key = self.config_data.get("openai_api_key")
        if not api_key:
            # 如果配置文件中没有api key，则尝试从环境变量获取
            api_key = os.environ.get("OPENAI_API_KEY")
        return api_key if api_key else None
    
    def set_github_token(self, token: str):
        """设置GitHub token
        
        Args:
            token: GitHub token
        """
        self.config_data["github_token"] = token
        self._save_config(self.config_data)
    
    def set_dashscope_api_key(self, api_key: str):
        """设置DashScope API key
        
        Args:
            api_key: DashScope API key
        """
        self.config_data["dashscope_api_key"] = api_key
        self._save_config(self.config_data)
    
    def set_openai_api_key(self, api_key: str):
        """设置OpenAI API key
        
        Args:
            api_key: OpenAI API key
        """
        self.config_data["openai_api_key"] = api_key
        self._save_config(self.config_data)