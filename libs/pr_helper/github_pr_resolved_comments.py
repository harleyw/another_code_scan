#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub PR Comments Fetcher
This tool is used to fetch comments in a specified GitHub Pull Request, including:
- Discussion comments (issue comments): Comments in the PR conversation thread
- Review comments (code comments): Inline comments on specific code lines
- Resolved comments: Review comments that have been marked as resolved
"""

import os
import sys
import argparse
import requests
from typing import Dict, List, Optional

from util.config_manager import ConfigManager


class GitHubPRCommentsFetcher:
    """Tool class for fetching resolved comments in a GitHub PR"""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the fetcher
        
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
    
    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get all discussion comments (issue comments) in the PR conversation thread
        
        In GitHub's API design, Pull Requests are treated as special cases of Issues.
        This endpoint retrieves the comments from the main conversation thread of the PR.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
        
        Returns:
            List of discussion comments in the PR
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_pr_review_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get all review comments in the PR
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
        
        Returns:
            List of review comments in the PR
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_all_comments(self, owner: str, repo: str, pr_number: int, include_review_comments: bool = True) -> Dict[str, List[Dict]]:
        """Get all comments in the PR
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            include_review_comments: Whether to include review comments (inline code comments)
        
        Returns:
            Dictionary containing all issue comments and all review comments
        """
        result = {
            "all_issue_comments": [],
            "all_review_comments": []
        }
        
        # Get all issue comments
        result["all_issue_comments"] = self.get_pr_comments(owner, repo, pr_number)
        
        # Get all review comments if requested
        if include_review_comments:
            result["all_review_comments"] = self.get_pr_review_comments(owner, repo, pr_number)
        
        return result
        
    def get_resolved_comments(self, owner: str, repo: str, pr_number: int, include_review_comments: bool = True) -> Dict[str, List[Dict]]:
        """Get all resolved comments in the PR
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            include_review_comments: Whether to include review comments (inline code comments)
        
        Returns:
            Dictionary containing resolved issue comments and resolved review comments
        """
        result = {
            "resolved_issue_comments": [],
            "resolved_review_comments": []
        }
        
        # Note: Standard issue comments don't have a resolved status in GitHub API
        # Only review comments have the resolved status
        result["resolved_issue_comments"] = []
        
        # Get and filter resolved review comments if requested
        if include_review_comments:
            review_comments = self.get_pr_review_comments(owner, repo, pr_number)
            result["resolved_review_comments"] = [
                comment for comment in review_comments 
                if comment.get("resolved_at") is not None  # This indicates the comment has been resolved
            ]
        
        return result
    
    def print_resolved_comments(self, resolved_comments: Dict[str, List[Dict]]) -> None:
        """Print resolved comments in a readable format
        
        Args:
            resolved_comments: Dictionary containing resolved comments
        """
        print(f"Found {len(resolved_comments['resolved_review_comments'])} resolved review comments:")
        print("=" * 80)
        
        for i, comment in enumerate(resolved_comments['resolved_review_comments'], 1):
            print(f"Comment #{i}:")
            print(f"By: {comment.get('user', {}).get('login', 'Unknown')}")
            print(f"File: {comment.get('path', 'Unknown')}")
            print(f"Line: {comment.get('line', 'Unknown')}")
            print(f"Resolved at: {comment.get('resolved_at', 'Unknown')}")
            print(f"Body:\n{comment.get('body', 'No content')}")
            print("-" * 80)
        
        # Note: Standard issue comments don't have resolved status in GitHub API
        if resolved_comments['resolved_issue_comments']:
            print(f"Found {len(resolved_comments['resolved_issue_comments'])} resolved issue comments:")
            print("=" * 80)
            for i, comment in enumerate(resolved_comments['resolved_issue_comments'], 1):
                print(f"Comment #{i}:")
                print(f"By: {comment.get('user', {}).get('login', 'Unknown')}")
                print(f"Created at: {comment.get('created_at', 'Unknown')}")
                print(f"Body:\n{comment.get('body', 'No content')}")
                print("-" * 80)
    
    def print_all_comments(self, all_comments: Dict[str, List[Dict]]) -> None:
        """Print all comments in a readable format
        
        Args:
            all_comments: Dictionary containing all comments
        """
        # Print discussion comments (issue comments) in thread format
        print(f"Found {len(all_comments['all_issue_comments'])} discussion comments in thread format:")
        print("=" * 80)
        
        # Group comments by thread using in_reply_to_id
        discussion_comments = all_comments['all_issue_comments']
        
        # Create a dictionary to map comment IDs to comments
        comment_dict = {comment['id']: comment for comment in discussion_comments}
        
        # Separate root comments (not replies) and replies
        root_comments = []
        reply_comments = {}
        
        for comment in discussion_comments:
            if 'in_reply_to_id' not in comment or comment['in_reply_to_id'] is None:
                root_comments.append(comment)
            else:
                parent_id = comment['in_reply_to_id']
                if parent_id not in reply_comments:
                    reply_comments[parent_id] = []
                reply_comments[parent_id].append(comment)
        
        # Sort root comments by creation time
        root_comments.sort(key=lambda x: x.get('created_at', ''))
        
        # Print each thread
        thread_count = 1
        for root_comment in root_comments:
            print(f"Thread #{thread_count}:")
            print("-" * 80)
            
            # Print root comment
            self._print_comment(root_comment, 0)
            
            # Print replies recursively
            self._print_replies(root_comment['id'], comment_dict, reply_comments, 1)
            
            print()
            thread_count += 1
        
        # Print all review comments
        if all_comments['all_review_comments']:
            print(f"\nFound {len(all_comments['all_review_comments'])} review comments:")
            print("=" * 80)
            
            for i, comment in enumerate(all_comments['all_review_comments'], 1):
                status = "(Resolved)" if comment.get('resolved_at') is not None else "(Unresolved)"
                print(f"Review Comment #{i} {status}:")
                print(f"By: {comment.get('user', {}).get('login', 'Unknown')}")
                print(f"File: {comment.get('path', 'Unknown')}")
                print(f"Line: {comment.get('line', 'Unknown')}")
                if comment.get('resolved_at') is not None:
                    print(f"Resolved at: {comment.get('resolved_at', 'Unknown')}")
                print(f"Body:\n{comment.get('body', 'No content')}")
                print("-" * 80)
                
    def _print_comment(self, comment: Dict, indent_level: int = 0) -> None:
        """Print a single comment with appropriate indentation
        
        Args:
            comment: The comment to print
            indent_level: The indentation level for formatting
        """
        indent = "  " * indent_level
        print(f"{indent}Comment by {comment.get('user', {}).get('login', 'Unknown')}")
        print(f"{indent}Created at: {comment.get('created_at', 'Unknown')}")
        
        # Format body with indentation for each line
        body_lines = comment.get('body', 'No content').split('\n')
        print(f"{indent}Body:")
        for line in body_lines:
            print(f"{indent}  {line}")
        print(f"{indent}")
        
    def _print_replies(self, parent_id: int, comment_dict: Dict[int, Dict], reply_comments: Dict[int, List[Dict]], 
                      indent_level: int) -> None:
        """Recursively print all replies to a comment
        
        Args:
            parent_id: The ID of the parent comment
            comment_dict: Dictionary mapping comment IDs to comments
            reply_comments: Dictionary mapping parent comment IDs to list of replies
            indent_level: Current indentation level
        """
        if parent_id not in reply_comments:
            return
        
        # Sort replies by creation time
        replies = reply_comments[parent_id]
        replies.sort(key=lambda x: x.get('created_at', ''))
        
        for reply in replies:
            self._print_comment(reply, indent_level)
            # Recursively print nested replies
            self._print_replies(reply['id'], comment_dict, reply_comments, indent_level + 1)


def main():
    """Command line entry function"""
    parser = argparse.ArgumentParser(description="Fetch comments in a GitHub PR")
    parser.add_argument("--owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument("--pr", type=int, required=True, help="PR number")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--no-review-comments", action="store_true", help="Exclude review comments")
    parser.add_argument("--all-comments", action="store_true", help="Fetch all comments including resolved and unresolved")
    
    args = parser.parse_args()
    if not args.token:
        args.token = os.environ.get("GITHUB_TOKEN")
    
    try:
        # Initialize fetcher
        fetcher = GitHubPRCommentsFetcher(args.token)
        
        if args.all_comments:
            # Fetch all comments
            print(f"Fetching all comments for PR #{args.pr} in {args.owner}/{args.repo}...")
            all_comments = fetcher.get_all_comments(
                args.owner, args.repo, args.pr, 
                include_review_comments=not args.no_review_comments
            )
            
            # Print results
            fetcher.print_all_comments(all_comments)
            
            print("\nSummary:")
            print(f"Total issue comments: {len(all_comments['all_issue_comments'])}")
            print(f"Total review comments: {len(all_comments['all_review_comments'])}")
        else:
            # Fetch resolved comments
            print(f"Fetching resolved comments for PR #{args.pr} in {args.owner}/{args.repo}...")
            resolved_comments = fetcher.get_resolved_comments(
                args.owner, args.repo, args.pr, 
                include_review_comments=not args.no_review_comments
            )
            
            # Print results
            fetcher.print_resolved_comments(resolved_comments)
            
            print("\nSummary:")
            print(f"Total resolved review comments: {len(resolved_comments['resolved_review_comments'])}")
            print(f"Total resolved issue comments: {len(resolved_comments['resolved_issue_comments'])}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()