# -*- coding: utf-8 -*-
"""
GitHub All PRs Exporter to Excel
This tool is used to export all PRs of a GitHub repository to Excel file,
using the GitHubPRToExcelExporter class to handle individual PR data.
"""

import os
import sys
import argparse
import requests
from typing import List, Optional

from util.config_manager import ConfigManager
from github_pr_to_excel import GitHubPRToExcelExporter


class GitHubAllPRsExporter:
    """Tool class for exporting all PRs of a GitHub repository to Excel"""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the exporter
        
        Args:
            token: GitHub personal access token, used to access private repositories or increase API rate limits
        """
        # 初始化配置管理器（使用自动计算的默认路径）
        config_manager = ConfigManager()
        # 如果没有传入token，则从配置文件中获取
        token = token or config_manager.get_github_token()
        
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
        
        # Initialize the PR to Excel exporter
        self.pr_exporter = GitHubPRToExcelExporter(token)

    def get_pr_file_path(self, state: str) -> str:
        """Get the PR file path based on the state
        
        Args:
            state: State of PRs (open, closed, merged, or all)
        
        Returns:
            Path to the PR file
        """
        return f"all_prs_{state}.txt"

    def get_all_prs(self, owner: str, repo: str, state: str = "all") -> List[int]:
        """Get all PR numbers for a repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: State of PRs to fetch (open, closed, merged, or all)
            
        Returns:
            List of PR numbers
        """
        pr_numbers = []
        page = 1
        per_page = 100  # Maximum allowed by GitHub API
        
        # Special handling for merged state
        is_merged_state = state == "merged"
        if is_merged_state:
            # For merged PRs, we need to fetch closed PRs first and then filter by merged_at
            state = "closed"
            print(f"Fetching all merged PRs for {owner}/{repo}...")
        else:
            print(f"Fetching all {state} PRs for {owner}/{repo}...")
        
        while True:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls?state={state}&page={page}&per_page={per_page}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            prs = response.json()
            if not prs:
                break  # No more PRs to fetch
            
            # Extract PR numbers and apply filters
            new_prs = []
            for pr in prs:
                pr_number = pr["number"]
                
                # For merged state, check if merged_at is not null
                if is_merged_state and pr["merged_at"] is None:
                    continue
                
                new_prs.append(pr_number)
            
            pr_numbers.extend(new_prs)
            
            print(f"  Fetched page {page}, got {len(new_prs)} PRs...")
            page += 1
            
        print(f"Total PRs found: {len(pr_numbers)}")
        return pr_numbers
    
    def export_all_prs_to_excel(self, owner: str, repo: str, output_file: str, state: str = "all", pr_numbers: Optional[List[int]] = None) -> None:
        """Export all PRs of a repository to Excel file
        
        Args:
            owner: Repository owner
            repo: Repository name
            output_file: Output Excel file path
            state: State of PRs to export (open, closed, merged, or all)
            pr_numbers: Optional list of specific PR numbers to export. If provided, ignores the state parameter.
        """
        # 如果指定了具体的PR编号，直接使用
        if pr_numbers:
            prs_to_process = pr_numbers.copy()
        else:
            # 获取PR文件路径
            pr_file_path = self.get_pr_file_path(state)
            
            # 检查PR文件是否存在
            if os.path.exists(pr_file_path):
                print(f"Found PR file: {pr_file_path}")
                # 从文件中读取PR编号
                try:
                    with open(pr_file_path, 'r') as f:
                        prs_to_process = [int(line.strip()) for line in f if line.strip().isdigit()]
                except Exception as e:
                    print(f"Error reading PR file: {str(e)}")
                    # 如果读取失败，重新从GitHub获取
                    prs_to_process = self.get_all_prs(owner, repo, state)
                    # 保存到文件
                    with open(pr_file_path, 'w') as f:
                        for pr_id in prs_to_process:
                            f.write(f"{pr_id}\n")
            else:
                # 文件不存在，从GitHub获取PR并保存到文件
                print(f"PR file {pr_file_path} not found. Fetching from GitHub...")
                prs_to_process = self.get_all_prs(owner, repo, state)
                # 保存到文件
                with open(pr_file_path, 'w') as f:
                    for pr_id in prs_to_process:
                        f.write(f"{pr_id}\n")
        
        # Export each PR to the same Excel file
        total_prs = len(prs_to_process)
        for i, pr_number in enumerate(prs_to_process, 1):
            try:
                print(f"\nProcessing PR #{pr_number} ({i}/{total_prs})...")
                self.pr_exporter.export_to_excel(owner, repo, pr_number, output_file)
                
                # 如果使用了PR文件，成功处理后从文件中删除该PR
                if not pr_numbers:
                    pr_file_path = self.get_pr_file_path(state)
                    if os.path.exists(pr_file_path):
                        # 读取当前文件内容
                        with open(pr_file_path, 'r') as f:
                            lines = f.readlines()
                        # 过滤掉已处理的PR
                        with open(pr_file_path, 'w') as f:
                            for line in lines:
                                if line.strip() != str(pr_number):
                                    f.write(line)
                        print(f"Removed PR #{pr_number} from {pr_file_path}")
            except Exception as e:
                print(f"Error exporting PR #{pr_number}: {str(e)}", file=sys.stderr)
                # Continue with next PR
        
        print(f"\nAll PR data successfully exported to {output_file}")


def main():
    """Command line entry function"""
    parser = argparse.ArgumentParser(description="Export all GitHub PRs of a repository to Excel")
    parser.add_argument("--owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument("--state", choices=["open", "closed", "merged", "all"], default="all", help="State of PRs to export")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--output", default="all_prs_data.xlsx", help="Output Excel file path")
    parser.add_argument("--prs", type=str, help="Comma-separated list of specific PR numbers to export, e.g., '1,2,3'")
    parser.add_argument("--fresh", action="store_true", help="Delete the corresponding PR file before starting")
    
    args = parser.parse_args()
    
    # 初始化配置管理器并获取GitHub token
    config_manager = ConfigManager("./cfg/config.json")
    if not args.token:
        args.token = config_manager.get_github_token()
    
    try:
        # Initialize exporter
        exporter = GitHubAllPRsExporter(args.token)
        
        # 如果指定了--fresh参数，删除对应的PR文件
        if args.fresh and not args.prs:
            pr_file_path = exporter.get_pr_file_path(args.state)
            if os.path.exists(pr_file_path):
                os.remove(pr_file_path)
                print(f"Removed existing PR file: {pr_file_path}")
        
        # Parse specific PR numbers if provided
        pr_numbers = None
        if args.prs:
            pr_numbers = [int(pr.strip()) for pr in args.prs.split(",")]
            print(f"Exporting specific PRs: {pr_numbers}")
        else:
            print(f"Exporting all {args.state} PRs from {args.owner}/{args.repo} to {args.output}...")
        
        exporter.export_all_prs_to_excel(
            args.owner,
            args.repo,
            args.output,
            args.state,
            pr_numbers
        )
        
    except Exception as e:
        print(f"Error occurred: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()