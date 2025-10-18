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
        
    def get_pr_review_data_dir(self) -> str:
        """获取PR审查数据目录路径
        
        Returns:
            str: PR审查数据目录路径，如果未设置则返回默认值"./pr_review_data"
        """
        data_dir = self.config_data.get("pr_review_data_dir")
        if not data_dir:
            # 如果配置文件中没有设置，则尝试从环境变量获取，否则返回默认值
            data_dir = os.environ.get("PR_REVIEW_DATA_DIR", "./pr_review_data")
        return data_dir
    
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
        
    def get_max_concurrent_pr_collection(self) -> int:
        """获取历史PR收集任务的最大并发数
        
        Returns:
            int: 历史PR收集任务的最大并发数，如果未设置则返回默认值5
        """
        max_concurrent = self.config_data.get("max_concurrent_pr_collection")
        if max_concurrent is None:
            # 如果配置文件中没有设置，则尝试从环境变量获取，否则返回默认值
            max_concurrent = os.environ.get("MAX_CONCURRENT_PR_COLLECTION", 5)
        return int(max_concurrent)
    
    def get_config_value(self, key: str, default_value=None):
        """获取配置文件中的任意配置值
        
        Args:
            key: 配置项的键名
            default_value: 配置项不存在时返回的默认值
        
        Returns:
            配置项的值，如果不存在则返回默认值
        """
        # 首先从配置文件中获取
        value = self.config_data.get(key)
        
        # 如果配置文件中不存在，尝试从环境变量获取
        if value is None:
            # 将key转换为环境变量格式（大写，下划线替换点）
            env_key = key.upper().replace(".", "_")
            value = os.environ.get(env_key)
        
        # 如果仍然不存在，返回默认值
        if value is None:
            value = default_value
        
        return value