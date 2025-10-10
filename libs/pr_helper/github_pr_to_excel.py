#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub PR Data Exporter to Excel
This tool is used to export GitHub Pull Request data to Excel file, including:
- PR description
- All comments (classified as issue comments, review comments, general comments)
- Linked GitHub issue URL or ID
"""

import os
import sys
import argparse
import requests
import pandas as pd
from typing import Dict, List, Optional, Union


class GitHubPRToExcelExporter:
    """Tool class for exporting GitHub PR data to Excel"""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the exporter
        
        Args:
            token: GitHub personal access token, used to access private repositories or increase API rate limits
        """
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    def get_pr_details(self, owner: str, repo: str, pr_number: int) -> Dict:
        """Get PR details including description and linked issues
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
        
        Returns:
            Dictionary containing PR details
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get all issue comments (discussion comments) in the PR conversation thread
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
        
        Returns:
            List of issue comments in the PR
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_pr_review_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get all review comments (inline code comments) in the PR
        
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
    
    def get_general_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get all general comments (PR review comments) in the PR
        
        These are the comments added at the PR review level, not tied to specific code lines
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
        
        Returns:
            List of general comments in the PR
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        # Extract body text from reviews where body is not empty
        general_comments = []
        for review in response.json():
            if review.get('body') and review.get('body').strip():
                general_comments.append({
                    'id': review.get('id'),
                    'user': review.get('user'),
                    'body': review.get('body'),
                    'created_at': review.get('submitted_at'),
                    'state': review.get('state')
                })
        
        return general_comments
    
    def extract_issue_link(self, pr_details: Dict) -> Optional[str]:
        """Extract linked issue URL or ID from PR details
        
        Args:
            pr_details: PR details dictionary
        
        Returns:
            Linked issue URL or ID if found, None otherwise
        """
        # Check if there's a linked issue in the PR body using common patterns
        body = pr_details.get('body', '')
        if not body:
            return None
        
        # Search for issue references in the format #123 or org/repo#123
        import re
        issue_pattern = r'(?:https://github\.com/[\w-]+/[\w-]+/issues/\d+|#[\d]+|[\w-]+/[\w-]+#[\d]+)'
        matches = re.findall(issue_pattern, body)
        
        if matches:
            # If the first match is a full URL, return it
            if matches[0].startswith('http'):
                return matches[0]
            # If it's a short reference like #123, convert to full URL
            if matches[0].startswith('#'):
                # Safely get repo information with null checks at each level
                head = pr_details.get('head', {})
                repo = head.get('repo', {}) if head else {}
                owner = repo.get('owner', {}).get('login', '') if repo else ''
                repo_name = repo.get('name', '') if repo else ''
                
                if owner and repo_name:
                    issue_number = matches[0][1:]
                    return f"https://github.com/{owner}/{repo_name}/issues/{issue_number}"
            # If it's in the format owner/repo#123
            if '/' in matches[0] and '#' in matches[0]:
                parts = matches[0].split('#')
                repo_part = parts[0]
                issue_number = parts[1]
                return f"https://github.com/{repo_part}/issues/{issue_number}"
            return matches[0]
        
        return None
    
    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Get PR code changes (diff)
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
        
        Returns:
            Formatted string containing the PR diff
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        # We need to set a different accept header to get the diff
        diff_headers = self.headers.copy()
        diff_headers["Accept"] = "application/vnd.github.v3.diff"
        
        response = requests.get(url, headers=diff_headers)
        response.raise_for_status()
        
        # Return the diff content
        return response.text
    
    def export_to_excel(self, owner: str, repo: str, pr_number: int, output_file: str) -> None:
        """Export PR data to Excel file
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            output_file: Output Excel file path
        """
        # Get PR details
        pr_details = self.get_pr_details(owner, repo, pr_number)
        pr_description = self._remove_ansi_escape(pr_details.get('body', ''))
        pr_title = pr_details.get('title', '')
        
        # Combine title and description for the description column
        full_description = f"{pr_title}\n\n{pr_description}"
        
        # Get all comments
        issue_comments = self.get_pr_comments(owner, repo, pr_number)
        review_comments = self.get_pr_review_comments(owner, repo, pr_number)
        general_comments = self.get_general_comments(owner, repo, pr_number)
        
        # Extract linked issue
        issue_link = self.extract_issue_link(pr_details)
        
        # Get PR code changes (diff)
        pr_diff = self.get_pr_diff(owner, repo, pr_number)
        
        # Format issue comments and general comments
        formatted_issue_comments = self._format_comments(issue_comments)
        formatted_general_comments = self._format_comments(general_comments)
        
        # Group review comments by thread (file and line)
        # Remove ANSI escape sequences from review comments body
        for comment in review_comments:
            if 'body' in comment:
                comment['body'] = self._remove_ansi_escape(comment['body'])
        grouped_review_comments = self._group_review_comments_by_thread(review_comments)
        
        # If there are no review comments, create an empty list
        if not grouped_review_comments:
            review_comment_threads = ['']
        else:
            # Format each review comment thread for individual cells
            review_comment_threads = []
            thread_count = 1
            for thread_key, comments in grouped_review_comments.items():
                # Extract file path and line number from thread key
                if ':' in thread_key:
                    path, line = thread_key.split(':', 1)
                else:
                    path, line = 'unknown_file', 'unknown_line'
                
                # Format the thread content
                thread_content = f"[ Thread #{thread_count} - File: {path}, Line: {line} ]\n\n"
                thread_content += f"[Reviewed Changes] \n\n {comments[0].get('diff_hunk', 'No diff chunk ')}\n---\n\n"
                for comment in comments:
                    user = comment.get('user', {}).get('login', 'Unknown')
                    created_at = comment.get('created_at', 'Unknown')
                    body = comment.get('body', 'No content')
                    
                    # Check if comment is resolved
                    resolved_info = "[Resolved] " if comment.get('resolved_at') else ""
                    
                    thread_content += f"{resolved_info}{user} ({created_at})\n{body}\n---\n\n"
                
                review_comment_threads.append(thread_content.strip())
                thread_count += 1
        
        # Create DataFrame with appropriate number of rows based on review comment threads
        num_rows = max(1, len(review_comment_threads))
        
        # Create data with PR id, description, etc. repeated across rows
        # These will be merged later in Excel
        pr_rows_value = f"{num_rows}"  # Store the number of rows for this PR
        new_data = {
            'PR id': [pr_number] * num_rows,
            'PR_rows': [pr_rows_value] * num_rows,
            'description': [full_description] * num_rows,
            'general comments': [formatted_general_comments] * num_rows,
            'review comments': review_comment_threads + [''] * (num_rows - len(review_comment_threads)),
            'issue comments': [formatted_issue_comments] * num_rows,
            'issue id/url': [issue_link if issue_link else ''] * num_rows,
            'code changes': [pr_diff] * num_rows
        }
        
        new_df = pd.DataFrame(new_data)
        
        # Check if the output file exists
        if os.path.exists(output_file):
            # Read existing data
            try:
                existing_df = pd.read_excel(output_file, sheet_name='PR Data')
                
                # Initialize PR exists flag
                pr_exists = False
                
                # Check if 'PR_rows' column exists in the existing DataFrame
                if 'PR_rows' in existing_df.columns:
                    # Find the first occurrence of the PR id
                    pr_id_mask = existing_df['PR id'] == pr_number
                    
                    if pr_id_mask.any():
                        pr_exists = True
                        # Get the index of the first occurrence
                        first_index = existing_df.index[pr_id_mask][0]
                        
                        # Get the number of rows for this PR
                        pr_rows_count = int(existing_df.loc[first_index, 'PR_rows'])
                        
                        # Create a mask to remove all rows from first_index to first_index + pr_rows_count - 1
                        rows_to_remove = []
                        for i in range(pr_rows_count):
                            if first_index + i < len(existing_df):
                                rows_to_remove.append(first_index + i)
                        
                        # Remove all rows for this PR
                        existing_df = existing_df.drop(rows_to_remove)
                        print(f"Removed {len(rows_to_remove)} rows for PR #{pr_number}")
                else:
                    # If 'PR_rows' column doesn't exist, use the old method
                    pr_id_mask = existing_df['PR id'] == pr_number
                    
                    if pr_id_mask.any():
                        pr_exists = True
                        # PR exists, update it
                        # Remove existing rows for this PR
                        existing_df = existing_df[~pr_id_mask]
                
                # Append new data
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                
                # Print appropriate message
                if pr_exists:
                    print(f"PR #{pr_number} data updated in {output_file}")
                else:
                    print(f"PR #{pr_number} data appended to {output_file}")
            except Exception as e:
                # If reading existing file fails, use only new data
                print(f"Error reading existing file: {str(e)}. Creating new file.")
                combined_df = new_df
        else:
            # File doesn't exist, create new
            combined_df = new_df
            print(f"Creating new file {output_file} with PR #{pr_number} data")
        
        # Export to Excel
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                combined_df.to_excel(writer, index=False, sheet_name='PR Data')
                
                # Get the worksheet object
                worksheet = writer.sheets['PR Data']
                
                # Set all cells to wrap text
                for column_cells in worksheet.columns:
                    for cell in column_cells:
                        cell.alignment = cell.alignment.copy(wrapText=True)
                
                # Merge cells for all PRs in the DataFrame
                self._merge_pr_cells(worksheet, combined_df)
            
            print(f"PR data successfully exported to {output_file}")
        except Exception as e:
            print(f"Error exporting to Excel. Attempting to recover existing data.")
            # If error occurs during export, try to save just the existing data if available
            if 'existing_df' in locals() and not existing_df.empty:
                # 尝试从combined_df中减去new_df，如果available
                # 检查combined_df和new_df是否存在
                if 'combined_df' in locals() and 'new_df' in locals():
                    # 从combined_df中移除new_df的数据
                    # 获取当前PR的ID
                    pr_ids_to_remove = new_df['PR id'].unique()
                    # 从combined_df中过滤掉这些PR ID
                    recovered_df = combined_df[~combined_df['PR id'].isin(pr_ids_to_remove)]
                    print(f"Recovered data by removing current PR from combined data")
                else:
                    # 如果combined_df或new_df不存在，回退到使用existing_df
                    recovered_df = existing_df
                    print("Using original existing data for recovery")
                
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    recovered_df.to_excel(writer, index=False, sheet_name='PR Data')
                    # Get the worksheet object
                    worksheet = writer.sheets['PR Data']
                    # Set all cells to wrap text
                    for column_cells in worksheet.columns:
                        for cell in column_cells:
                            cell.alignment = cell.alignment.copy(wrapText=True)
                    # Merge cells for all PRs in the DataFrame
                    self._merge_pr_cells(worksheet, recovered_df)
                print(f"Successfully saved existing PR data to {output_file}")
            else:
                print("No existing data to save")
            raise e
        
    def _merge_pr_cells(self, worksheet, df):
        """Merge cells for all PR entries in the worksheet
        
        Args:
            worksheet: Excel worksheet object
            df: DataFrame containing PR data
        """
        if len(df) == 0:
            return
        
        current_pr_id = None
        start_row = 2  # Excel is 1-indexed, header is row 1
        
        # Iterate through the DataFrame to find PR boundaries
        for i, pr_id in enumerate(df['PR id'], start=2):
            if pd.isna(pr_id):
                continue
                
            if current_pr_id is None:
                current_pr_id = pr_id
                start_row = i
            elif pr_id != current_pr_id:
                # End of current PR, merge cells
                end_row = i - 1
                if end_row > start_row:
                    self._merge_cells_for_pr(worksheet, start_row, end_row)
                # Start of new PR
                current_pr_id = pr_id
                start_row = i
        
        # Merge cells for the last PR
        if current_pr_id is not None and start_row <= len(df) + 1:
            end_row = len(df) + 1  # +1 because DataFrame is 0-indexed, Excel is 1-indexed
            if end_row > start_row:
                self._merge_cells_for_pr(worksheet, start_row, end_row)
        
    def _merge_cells_for_pr(self, worksheet, start_row, end_row):
        """Merge cells for a single PR entry
        
        Args:
            worksheet: Excel worksheet object
            start_row: Start row index (1-indexed)
            end_row: End row index (1-indexed)
        """
        # Merge PR id column
        worksheet.merge_cells(start_row=start_row, end_row=end_row, start_column=1, end_column=1)
        
        # Merge PR_rows column
        worksheet.merge_cells(start_row=start_row, end_row=end_row, start_column=2, end_column=2)
        
        # Merge description column
        worksheet.merge_cells(start_row=start_row, end_row=end_row, start_column=3, end_column=3)
        
        # Merge general comments column
        worksheet.merge_cells(start_row=start_row, end_row=end_row, start_column=4, end_column=4)
        
        # Merge issue comments column
        worksheet.merge_cells(start_row=start_row, end_row=end_row, start_column=6, end_column=6)
        
        # Merge issue id/url column
        worksheet.merge_cells(start_row=start_row, end_row=end_row, start_column=7, end_column=7)
        
        # Merge diff column
        worksheet.merge_cells(start_row=start_row, end_row=end_row, start_column=8, end_column=8)
        
    def _remove_ansi_escape(self, text: str) -> str:
        """Remove ANSI escape sequences and Excel-incompatible characters from text
        
        Args:
            text: Input text that may contain ANSI escape sequences or incompatible characters
        
        Returns:
            Cleaned text without problematic characters
        """
        import re
        # Handle None or non-string inputs
        if text is None:
            return ''
        # Convert to string if it's not already
        if not isinstance(text, (str, bytes)):
            text = str(text)
        # ANSI escape sequence regex pattern
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)
        
        # Remove Excel-incompatible control characters
        # These are characters with ASCII codes 0-31 (except 9=tab, 10=newline, 13=carriage return)
        # and some other problematic characters
        excel_incompatible_chars = re.compile(r'[\x00-\x08\x0B-\x1F\x7F]')
        text = excel_incompatible_chars.sub('', text)
        
        # Replace specific problematic characters
        problematic_chars = {
            '\x08': '',  # Backspace
            '\r': '\n',  # Carriage return -> newline
        }
        for char, replacement in problematic_chars.items():
            text = text.replace(char, replacement)
            
        return text
    
    def _format_grouped_review_comments(self, grouped_review_comments: Dict[str, List[Dict]]) -> str:
        """Format grouped review comments for Excel display
        
        Args:
            grouped_review_comments: Dictionary of grouped review comments
        
        Returns:
            Formatted string of grouped review comments
        """
        if not grouped_review_comments:
            return ''
        
        formatted = []
        thread_count = 1
        
        # Process each thread
        for thread_key, comments in grouped_review_comments.items():
            # Extract file path and line number from thread key
            if ':' in thread_key:
                path, line = thread_key.split(':', 1)
            else:
                path, line = 'unknown_file', 'unknown_line'
            
            # Add thread header
            formatted.append(f"[ Thread #{thread_count} - File: {path}, Line: {line} ]\n")
            
            # Add each comment in the thread
            for comment in comments:
                user = comment.get('user', {}).get('login', 'Unknown')
                created_at = comment.get('created_at', 'Unknown')
                body = self._remove_ansi_escape(comment.get('body', 'No content'))
                
                # Check if comment is resolved
                resolved_info = "[Resolved] " if comment.get('resolved_at') else ""
                
                formatted.append(f"{resolved_info}{user} ({created_at})\n{body}\n---\n")
            
            formatted.append("\n")  # Add space between threads
            thread_count += 1
        
        return ''.join(formatted)
    
    def _format_comments(self, comments: List[Dict]) -> str:
        """Format comments for Excel display
        
        Args:
            comments: List of comments
        
        Returns:
            Formatted string of comments
        """
        if not comments:
            return ''
        
        formatted = []
        for comment in comments:
            user = comment.get('user', {}).get('login', 'Unknown')
            created_at = comment.get('created_at', 'Unknown')
            body = self._remove_ansi_escape(comment.get('body', 'No content'))
            
            # For review comments, add file and line information
            file_info = ''
            if 'path' in comment:
                file_info = f"File: {comment.get('path')}, Line: {comment.get('line', 'Unknown')}\n"
            
            # Check if comment is resolved (for review comments)
            resolved_info = ''
            if comment.get('resolved_at'):
                resolved_info = "[Resolved] "
            
            formatted.append(f"{resolved_info}{user} ({created_at})\n{file_info}{body}\n---\n")
        
        return ''.join(formatted)
        
    def _group_review_comments_by_thread(self, review_comments: List[Dict]) -> Dict[str, List[Dict]]:
        """Group review comments by file and line (thread)
        
        Args:
            review_comments: List of review comments
        
        Returns:
            Dictionary where keys are file:line identifiers and values are lists of comments in that thread
        """
        grouped = {}
        
        for comment in review_comments:
            # Create a unique key for the thread based on file path and line number
            path = comment.get('path', 'unknown_file')
            line = comment.get('line', comment.get('position', 'unknown_line'))
            thread_key = f"{path}:{line}"
            
            if thread_key not in grouped:
                grouped[thread_key] = []
            grouped[thread_key].append(comment)
        
        # Sort comments within each thread by creation time
        for thread_key in grouped:
            grouped[thread_key].sort(key=lambda x: x.get('created_at', ''))
        
        return grouped


def main():
    """Command line entry function"""
    parser = argparse.ArgumentParser(description="Export GitHub PR data to Excel")
    parser.add_argument("--owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument("--pr", type=int, required=True, help="PR number")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--output", default="pr_data.xlsx", help="Output Excel file path")
    
    args = parser.parse_args()
    if not args.token:
        args.token = os.environ.get("GITHUB_TOKEN")
    
    try:
        # Initialize exporter
        exporter = GitHubPRToExcelExporter(args.token)
        
        print(f"Exporting PR #{args.pr} data from {args.owner}/{args.repo} to {args.output}...")
        exporter.export_to_excel(args.owner, args.repo, args.pr, args.output)
        
    except Exception as e:
        print(f"Error occurred: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()