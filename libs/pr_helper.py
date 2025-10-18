import os
from libs.pr_helper.export_all_prs_to_excel import GitHubAllPRsExporter
from util.config_manager import ConfigManager

class PRHelper:
    """PR处理工具的封装类"""
    
    def __init__(self):
        """初始化PR助手"""
        self.config_manager = ConfigManager()
        self.github_token = self.config_manager.get_github_token()
        if not self.github_token:
            raise ValueError("GitHub token not found. Please set it in the config file or as an environment variable.")
        
    def export_merged_prs(self, owner: str, repo: str, output_dir: str = None) -> str:
        """导出指定仓库的所有merged PR到Excel文件"""
        # 如果未指定输出目录，使用配置管理器获取PR审查数据目录路径
        if not output_dir:
            data_dir = self.config_manager.get_pr_review_data_dir()
            output_dir = os.path.join(data_dir, owner, repo)
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化PR导出器
        exporter = GitHubAllPRsExporter(self.github_token)
        
        # 导出所有merged PR到excel
        output_file = f"{output_dir}/all_merged_prs.xlsx"
        exporter.export_all_prs_to_excel(owner, repo, output_file, state="merged")
        
        return output_file
    
    def is_valid_repo(self, owner: str, repo: str) -> bool:
        """检查仓库是否有效"""
        # 这里可以添加实际的仓库有效性检查逻辑
        # 暂时简单检查owner和repo是否为空
        return bool(owner and repo)
    
    def get_pr_file_path(self, owner: str, repo: str) -> str:
        """获取PR Excel文件的路径"""
        data_dir = self.config_manager.get_pr_review_data_dir()
        return os.path.join(data_dir, owner, repo, "all_merged_prs.xlsx")
    
    def pr_file_exists(self, owner: str, repo: str) -> bool:
        """检查PR Excel文件是否存在"""
        file_path = self.get_pr_file_path(owner, repo)
        return os.path.exists(file_path)