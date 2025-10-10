#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PR Files Pre-Submission Downloader
This tool is used to download the contents of all files in a specified PR before they were submitted,
helping users apply the PR's diff to these files.
"""

import os
import sys
import argparse
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Set


class PRFilesPreDownloader:
    """Tool class for downloading pre-submission versions of all files in a PR"""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the downloader
        
        Args:
            token: GitHub personal access token, used to access private repositories or increase API rate limits
        """
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
        
    def get_pr_info(self, owner: str, repo: str, pr_number: int) -> Dict:
        """Get basic information about the PR
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
        
        Returns:
            Dictionary containing PR information
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get all files modified in the PR
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
        
        Returns:
            List of files modified in the PR
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_file_content_before_pr(self, owner: str, repo: str, file_path: str, base_sha: str) -> str:
        """Get file content before PR submission
        
        Args:
            owner: Repository owner
            repo: Repository name
            file_path: File path
            base_sha: Base branch SHA of the PR
        
        Returns:
            File content string
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={base_sha}"
        response = requests.get(url, headers=self.headers)
        
        # Handle possible error cases
        if response.status_code == 404:
            # The file might be newly added in the PR and thus doesn't exist in the base branch
            return ""
        
        response.raise_for_status()
        
        # Check if content is base64 encoded
        content_data = response.json()
        if isinstance(content_data, dict) and "content" in content_data:
            import base64
            return base64.b64decode(content_data["content"]).decode("utf-8", errors="replace")
        
        return str(content_data)
    
    def download_pr_files_before(self, owner: str, repo: str, pr_number: int, 
                               output_dir: str, max_workers: int = 5) -> List[str]:
        """Download pre-submission versions of all files in the PR
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            output_dir: Output directory
            max_workers: Maximum number of threads for concurrent download
        
        Returns:
            List of successfully downloaded files
        """
        # 1. Get PR information including base branch SHA
        pr_info = self.get_pr_info(owner, repo, pr_number)
        base_sha = pr_info["base"]["sha"]
        
        # 2. Get all files modified in the PR
        pr_files = self.get_pr_files(owner, repo, pr_number)
        
        # 3. Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # 4. Collect all file paths that need to be downloaded
        file_paths = [file["filename"] for file in pr_files]
        downloaded_files = []
        
        # Define function for downloading a single file
        def download_single_file(file_path: str) -> None:
            try:
                # Get file content before PR submission
                content = self.get_file_content_before_pr(owner, repo, file_path, base_sha)
                
                # Build local file path
                local_file_path = os.path.join(output_dir, file_path)
                
                # Create necessary directories
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                # Write to file
                with open(local_file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                downloaded_files.append(file_path)
                print(f"Downloaded: {file_path}")
            except Exception as e:
                print(f"Failed to download {file_path}: {str(e)}")
        
        # 5. Download files concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(download_single_file, file_paths)
        
        return downloaded_files


def main():
    """Command line entry function"""
    parser = argparse.ArgumentParser(description="Download pre-submission versions of all files in a PR")
    parser.add_argument("--owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument("--pr", type=int, required=True, help="PR number")
    parser.add_argument("--output", default="./pr_files_before", help="Output directory")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--threads", type=int, default=5, help="Number of concurrent download threads")
    
    args = parser.parse_args()
    if not args.token:
        args.token = os.environ.get("GITHUB_TOKEN")
    if not args.token:
        parser.error("GitHub token is required. Set it via --token or GITHUB_TOKEN environment variable.")
    
    try:
        # Initialize downloader
        downloader = PRFilesPreDownloader(args.token)
        
        # Download files
        print(f"Starting to download pre-submission versions of files in PR #{args.pr}...")
        downloaded_files = downloader.download_pr_files_before(
            args.owner, args.repo, args.pr, args.output, args.threads
        )
        
        print(f"\nDownload complete!")
        print(f"Successfully downloaded {len(downloaded_files)} files to directory: {args.output}")
        print("You can now apply the PR's diff to these files.")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()