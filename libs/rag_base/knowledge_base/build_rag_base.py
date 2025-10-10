### Build Index

import os
import sys
import pandas as pd
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

from util.config_manager import ConfigManager

# Initialize config manager (using auto-calculated default path) and get DashScope API key
config_manager = ConfigManager()
dashscope_api_key = config_manager.get_dashscope_api_key()

if not dashscope_api_key:
    raise ValueError("DashScope API key not found. Please set it in the config file or as an environment variable.")

embd = DashScopeEmbeddings(model="text-embedding-v4", dashscope_api_key=dashscope_api_key)

# 加载Excel文件中的PR数据
def load_excel_pr_data(excel_file_path: str) -> List[Dict[str, Any]]:
    """从Excel文件加载PR数据
    
    Args:
        excel_file_path: Excel文件路径
        
    Returns:
        PR数据列表
    """
    if not os.path.exists(excel_file_path):
        print(f"Error: Excel file {excel_file_path} does not exist.")
        return []
    
    try:
        df = pd.read_excel(excel_file_path, sheet_name='PR Data')
        
        # 检查必要的列是否存在
        required_columns = ['PR id', 'description', 'general comments', 'review comments', 
                           'issue comments', 'issue id/url', 'code changes']
        for col in required_columns:
            if col not in df.columns:
                print(f"Warning: Column '{col}' not found in Excel file.")
        
        # 处理PR数据
        pr_data_list = []
        
        # 处理PR_rows列以识别每个PR的多行数据
        if 'PR_rows' in df.columns:
            # 获取每个PR的起始索引
            pr_start_indices = df[~df['PR_rows'].isna()].index.tolist()
            
            for i, start_idx in enumerate(pr_start_indices):
                # 确定当前PR的行数
                try:
                    pr_rows_count = int(df.loc[start_idx, 'PR_rows'])
                except (ValueError, TypeError):
                    pr_rows_count = 1
                
                # 获取当前PR的所有行
                end_idx = min(start_idx + pr_rows_count - 1, len(df) - 1)
                pr_rows = df.iloc[start_idx:end_idx + 1]
                
                # 提取PR基本信息（第一行）
                pr_id = df.loc[start_idx, 'PR id']
                description = df.loc[start_idx, 'description'] if 'description' in df.columns else ''
                general_comments = df.loc[start_idx, 'general comments'] if 'general comments' in df.columns else ''
                issue_comments = df.loc[start_idx, 'issue comments'] if 'issue comments' in df.columns else ''
                issue_link = df.loc[start_idx, 'issue id/url'] if 'issue id/url' in df.columns else ''
                code_changes = df.loc[start_idx, 'code changes'] if 'code changes' in df.columns else ''
                
                # 提取所有review comments
                review_comments = []
                if 'review comments' in df.columns:
                    for _, row in pr_rows.iterrows():
                        comment = row['review comments']
                        if pd.notna(comment) and comment.strip():
                            review_comments.append(comment)
                
                # 构建PR文档内容
                document_content = f"PR ID: {pr_id}\n"
                if description and pd.notna(description):
                    document_content += f"Description:\n{description}\n\n"
                if code_changes and pd.notna(code_changes):
                    document_content += f"Code Changes:\n{code_changes}\n\n"
                if general_comments and pd.notna(general_comments):
                    document_content += f"General Comments:\n{general_comments}\n\n"
                if issue_comments and pd.notna(issue_comments):
                    document_content += f"Issue Comments:\n{issue_comments}\n\n"
                if review_comments:
                    document_content += f"Review Comments:\n" + "\n---\n".join(review_comments)
                
                # 添加元数据
                metadata = {
                    'pr_id': int(pr_id) if pd.notna(pr_id) else '',  # 转换为基本Python int类型
                    'source': str(excel_file_path)
                }
                if 'issue id/url' in row and pd.notna(row['issue id/url']):
                    metadata['issue_link'] = str(row['issue id/url'])
                
                pr_data_list.append({
                    'page_content': document_content,
                    'metadata': metadata
                })
        else:
            # 如果没有PR_rows列，假设每个PR只有一行
            for _, row in df.iterrows():
                pr_id = row['PR id']
                
                # 构建PR文档内容
                document_content = f"PR ID: {pr_id}\n"
                if 'description' in row and pd.notna(row['description']):
                    document_content += f"Description:\n{row['description']}\n\n"
                if 'code changes' in row and pd.notna(row['code changes']):
                    document_content += f"Code Changes:\n{row['code changes']}\n\n"
                if 'general comments' in row and pd.notna(row['general comments']):
                    document_content += f"General Comments:\n{row['general comments']}\n\n"
                if 'issue comments' in row and pd.notna(row['issue comments']):
                    document_content += f"Issue Comments:\n{row['issue comments']}\n\n"
                if 'review comments' in row and pd.notna(row['review comments']):
                    document_content += f"Review Comments:\n{row['review comments']}\n\n"
                
                # 添加元数据
                metadata = {
                    'pr_id': int(pr_id) if pd.notna(pr_id) else '',  # 转换为基本Python int类型
                    'source': str(excel_file_path)
                }
                if 'issue id/url' in row and pd.notna(row['issue id/url']):
                    metadata['issue_link'] = str(row['issue id/url'])
                
                pr_data_list.append({
                    'page_content': document_content,
                    'metadata': metadata
                })
        
        print(f"Successfully loaded {len(pr_data_list)} PRs from {excel_file_path}")
        return pr_data_list
        
    except Exception as e:
        print(f"Error loading Excel file: {str(e)}")
        return []

# Load PR data from Excel file
# Replace 'github_pr_data.xlsx' with the actual path to your Excel file
# excel_file_path = "github_pr_data.xlsx"
excel_file_path = "all_merged_prs.phase4.xlsx"

# Check if the Excel file exists
if not os.path.exists(excel_file_path):
    raise FileNotFoundError(f"Excel file {excel_file_path} not found. Please create the file with PR data.")

pr_docs = load_excel_pr_data(excel_file_path)

if not pr_docs:
    print("No PR data loaded. Exiting.")
    exit(1)
    
# 将数据转换为LangChain Document对象
from langchain.schema import Document
documents = [Document(page_content=doc['page_content'], metadata=doc['metadata']) for doc in pr_docs]
    
# Split
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, 
    chunk_overlap=200
)
doc_splits = text_splitter.split_documents(documents)

# Add to vectorstore
vectorstore = Chroma.from_documents(
    documents=doc_splits,
    collection_name="rag-chroma",
    embedding=embd,
)
retriever = vectorstore.as_retriever()
