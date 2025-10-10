"""
PR Audit Tool
This tool is used to check and update PRs with empty code changes column in Excel files.
"""

import os
import sys
import argparse
import pandas as pd
from typing import Optional

from util.config_manager import ConfigManager
from github_pr_to_excel import GitHubPRToExcelExporter


class PRAuditTool:
    """Tool class for auditing PR Excel files and updating empty code changes"""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the audit tool
        
        Args:
            token: GitHub personal access token, used to access private repositories or increase API rate limits
        """
        # 初始化配置管理器（使用自动计算的默认路径）
        config_manager = ConfigManager()
        # 如果没有传入token，则从配置文件中获取
        token = token or config_manager.get_github_token()
        
        # Initialize the PR to Excel exporter
        self.pr_exporter = GitHubPRToExcelExporter(token)
    
    def check_and_update_empty_code_changes(self, owner: str, repo: str, output_file: str) -> None:
        """Check Excel file for PRs with empty code changes column and update them
        
        Args:
            owner: Repository owner
            repo: Repository name
            output_file: Excel file path to check and update
        """
        # Check if the file exists
        if not os.path.exists(output_file):
            print(f"Error: File {output_file} does not exist.")
            return
        
        print(f"Checking {output_file} for PRs with empty code changes...")
        
        # Read the Excel file
        try:
            df = pd.read_excel(output_file, sheet_name='PR Data')
        except Exception as e:
            print(f"Error reading Excel file: {str(e)}")
            return
        
        # Check if required columns exist
        if 'PR id' not in df.columns or 'code changes' not in df.columns:
            print("Error: Required columns ('PR id' or 'code changes') not found in the Excel file.")
            return
        
        # Find PRs with empty code changes
        pr_ids_to_update = []
        
        # If PR_rows column exists, use it to find unique PRs
        if 'PR_rows' in df.columns:
            # Get the first occurrence of each PR (where PR_rows is not NaN)
            first_occurrences = df[~df['PR_rows'].isna()].index.tolist()
            
            for idx in first_occurrences:
                pr_id = df.loc[idx, 'PR_id'] if 'PR_id' in df.columns else df.loc[idx, 'PR id']
                code_changes = df.loc[idx, 'code changes']
                
                # Check if code changes is empty or NaN
                if pd.isna(code_changes) or str(code_changes).strip() == '':
                    pr_ids_to_update.append(pr_id)
        else:
            # Use the old method - check all rows
            unique_pr_ids = df['PR id'].unique()
            
            for pr_id in unique_pr_ids:
                # Get the first row of this PR
                pr_row = df[df['PR id'] == pr_id].iloc[0]
                code_changes = pr_row['code changes']
                
                # Check if code changes is empty or NaN
                if pd.isna(code_changes) or str(code_changes).strip() == '':
                    pr_ids_to_update.append(pr_id)
        
        # Print the results
        if not pr_ids_to_update:
            print(f"No PRs with empty code changes found in {output_file}.")
            return
        
        print(f"Found {len(pr_ids_to_update)} PR(s) with empty code changes:")
        for pr_id in pr_ids_to_update:
            print(f"  - PR #{pr_id}")
        
        # Update the PRs with empty code changes
        print(f"\nUpdating PRs with empty code changes...")
        for i, pr_id in enumerate(pr_ids_to_update, 1):
            try:
                print(f"\nProcessing PR #{pr_id} ({i}/{len(pr_ids_to_update)})...")
                self.pr_exporter.export_to_excel(owner, repo, pr_id, output_file)
            except Exception as e:
                print(f"Error updating PR #{pr_id}: {str(e)}", file=sys.stderr)
                # Continue with next PR
        
        print(f"\nAll PRs with empty code changes have been processed.")


if __name__ == "__main__":
    # Example usage
    parser = argparse.ArgumentParser(description="Audit PR Excel files and update empty code changes")
    parser.add_argument("--owner", required=True, help="Repository owner")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument("--output", required=True, help="Excel file path to check and update")
    parser.add_argument("--token", help="GitHub personal access token")
    args = parser.parse_args()
    
    # 初始化配置管理器并获取GitHub token
    config_manager = ConfigManager("./cfg/config.json")
    if not args.token:
        args.token = config_manager.get_github_token()
    
    # Create the audit tool and run the check
    audit_tool = PRAuditTool(args.token)
    audit_tool.check_and_update_empty_code_changes(args.owner, args.repo, args.output)