import requests
import argparse
import os
import sys

from util.config_manager import ConfigManager

class GitHubFileFetcher:
    def __init__(self, auth_token=None):
        """初始化GitHub文件获取器
        
        Args:
            auth_token (str, optional): GitHub个人访问令牌，用于访问私有仓库或提高API速率限制
        """
        # 初始化配置管理器（使用自动计算的默认路径）
        config_manager = ConfigManager()
        # 如果没有传入auth_token，则从配置文件中获取
        self.auth_token = auth_token or config_manager.get_github_token()
        self.base_url = "https://api.github.com"
        
    def _get_headers(self):
        """构建请求头"""
        headers = {
            "Accept": "application/vnd.github.v3.raw"
        }
        if self.auth_token:
            headers["Authorization"] = f"token {self.auth_token}"
        return headers
    
    def get_file_at_commit(self, owner, repo, file_path, commit_sha, save_to=None):
        """获取特定commit版本的文件内容
        
        Args:
            owner (str): 仓库所有者（用户名或组织名）
            repo (str): 仓库名称
            file_path (str): 文件路径（从仓库根目录开始）
            commit_sha (str): Commit的SHA哈希值（完整或前7个字符）
            save_to (str, optional): 保存文件的路径，如果不提供则返回内容
            
        Returns:
            str: 文件内容，如果指定了save_to则返回保存的文件路径
            
        Raises:
            Exception: 当API请求失败时抛出异常
        """
        # 构建API端点
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={commit_sha}"
        
        # 发送请求
        headers = self._get_headers()
        response = requests.get(url, headers=headers)
        
        # 检查响应状态
        if response.status_code != 200:
            raise Exception(f"获取文件失败: {response.status_code} - {response.text}")
        
        # 获取文件内容
        content = response.text
        
        # 如果指定了保存路径，则保存文件
        if save_to:
            # 确保目录存在
            os.makedirs(os.path.dirname(save_to), exist_ok=True)
            # 写入文件
            with open(save_to, 'w', encoding='utf-8') as f:
                f.write(content)
            return save_to
        
        return content
    
    def get_commit_info(self, owner, repo, commit_sha):
        """获取特定commit的详细信息
        
        Args:
            owner (str): 仓库所有者
            repo (str): 仓库名称
            commit_sha (str): Commit的SHA哈希值
            
        Returns:
            dict: Commit信息的字典
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/git/commits/{commit_sha}"
        headers = self._get_headers()
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"获取commit信息失败: {response.status_code} - {response.text}")
        
        return response.json()


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description="GitHub文件版本获取工具")
    parser.add_argument("--owner", required=True, help="仓库所有者（用户名或组织名）")
    parser.add_argument("--repo", required=True, help="仓库名称")
    parser.add_argument("--path", required=True, help="文件路径")
    parser.add_argument("--commit", required=True, help="Commit的SHA哈希值")
    parser.add_argument("--save-to", help="保存文件的路径")
    parser.add_argument("--token", help="GitHub个人访问令牌")
    
    args = parser.parse_args()
    
    try:
        # 创建文件获取器实例
        fetcher = GitHubFileFetcher(args.token)
        
        # 获取文件内容
        result = fetcher.get_file_at_commit(
            owner=args.owner,
            repo=args.repo,
            file_path=args.path,
            commit_sha=args.commit,
            save_to=args.save_to
        )
        
        # 输出结果
        if args.save_to:
            print(f"文件已保存到: {result}")
        else:
            print("文件内容:")
            print(result)
            
    except Exception as e:
        print(f"错误: {str(e)}")


if __name__ == "__main__":
    main()