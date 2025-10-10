import os
from libs.pr_helper.export_all_prs_to_excel import GitHubAllPRsExporter
from util.config_manager import ConfigManager
from services.repo_manager.repo_manager import repo_service_manager

def collect_merged_prs_task(owner: str, repo: str):
    """异步任务：收集指定仓库的所有merged PR并生成excel文件"""
    try:
        # 初始化配置管理器（使用自动计算的默认路径）
        config_manager = ConfigManager()
        token = config_manager.get_github_token()
        
        # 创建输出目录 - 使用当前目录下的owner/repo结构
        output_dir = f"./{owner}/{repo}"
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化PR导出器
        exporter = GitHubAllPRsExporter(token)
        
        # 导出所有merged PR到excel
        output_file = f"{output_dir}/all_merged_prs.xlsx"
        exporter.export_all_prs_to_excel(owner, repo, output_file, state="merged")
        
        # 导出完成后，更新对应的服务实例的vectorstore
        repo_service_manager.update_service_vectorstore(owner, repo)
    except Exception as e:
        print(f"收集PR时出错: {str(e)}")