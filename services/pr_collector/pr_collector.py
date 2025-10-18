import os
import hashlib
from libs.pr_helper.export_all_prs_to_excel import GitHubAllPRsExporter
from util.config_manager import ConfigManager
from services.repo_manager.repo_manager import repo_service_manager

def collect_merged_prs_task(owner: str, repo: str):
    """异步任务：收集指定仓库的所有merged PR并生成excel文件"""
    try:
        # 初始化配置管理器（使用自动计算的默认路径）
        config_manager = ConfigManager()
        token = config_manager.get_github_token()
        refresh = config_manager.get_config_value('auto_update_pr_data', False)
        
        # 使用配置管理器获取PR审查数据目录路径
        data_dir = config_manager.get_pr_review_data_dir()
        output_dir = os.path.join(data_dir, owner, repo)
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化PR导出器
        exporter = GitHubAllPRsExporter(token, refresh)
        
        # 导出所有merged PR到excel
        output_file = f"{output_dir}/all_merged_prs.xlsx"
        
        # 检查导出前文件是否存在及哈希值
        file_changed = True
        if os.path.exists(output_file):
            # 计算导出前文件的哈希值
            with open(output_file, 'rb') as f:
                pre_hash = hashlib.md5(f.read()).hexdigest()
        else:
            pre_hash = None
        
        # 执行导出操作
        exporter.export_all_prs_to_excel(owner, repo, output_file, state="merged")
        
        # 检查导出后文件是否变化
        if pre_hash is not None:
            with open(output_file, 'rb') as f:
                post_hash = hashlib.md5(f.read()).hexdigest()
            file_changed = pre_hash != post_hash
        
        # 只有当Excel文件发生变化时，才更新vectorstore
        if file_changed:
            repo_service_manager.update_service_vectorstore(owner, repo)
    except Exception as e:
        print(f"收集PR时出错: {str(e)}")