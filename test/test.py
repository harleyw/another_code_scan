from util.config_manager import ConfigManager
from github_file_fetcher import GitHubFileFetcher

# 初始化配置管理器（使用自动计算的默认路径）并获取GitHub token
config_manager = ConfigManager()
github_token = config_manager.get_github_token()

# 创建实例
fetcher = GitHubFileFetcher(auth_token=github_token)

# 获取文件内容
content = fetcher.get_file_at_commit(
    owner="sonic-net",
    repo="sonic-buildimage",
    file_path="src/sonic-config-engine/tests/test_j2files.py b/src/sonic-config-engine/tests/test_j2files.py",
    commit_sha="f332e9ba83b9b0a4842d90495a9364b6fbacd759"
)

print(content)

# 保存文件
# fetcher.get_file_at_commit(
#     owner="sonic-net",
#     repo="sonic-buildimage",
#     file_path="README.md",
#     commit_sha="abcdef12",
#     save_to="./README_abcdef12.md"
# )