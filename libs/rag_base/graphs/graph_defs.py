import os
import re
import json
import logging
from pprint import pformat
from typing import List

from typing_extensions import TypedDict
from libs.rag_base.LLMs.router_question_llm import question_router
from libs.rag_base.LLMs.retrieval_grader_llm import retrieval_grader
from libs.rag_base.LLMs.generater_llm import format_docs, rag_chain
from libs.rag_base.LLMs.hallucination_grader_llm import hallucination_grader
from libs.rag_base.LLMs.answer_grader_llm import answer_grader
from libs.rag_base.knowledge_base.build_rag_base import retriever_wrapper
from typing import Optional

# 全局vectorstore引用，可在初始化时设置
_global_vectorstore = None

def set_global_vectorstore(vectorstore):
    """设置全局vectorstore，供retriever_node使用"""
    global _global_vectorstore
    _global_vectorstore = vectorstore

def get_global_vectorstore():
    """获取全局vectorstore"""
    global _global_vectorstore
    return _global_vectorstore

from libs.rag_base.LLMs.general_reviewer_llm import general_reviewer
from libs.rag_base.LLMs.general_question_llm import general_question_chain
from pprint import pprint
from langchain.schema import Document
from util.config_manager import ConfigManager

# Import PR tools
from libs.pr_helper.github_pr_to_excel import GitHubPRToExcelExporter
from libs.pr_helper.pr_files_pre_downloader import PRFilesPreDownloader

# 配置日志
logger = logging.getLogger("PR_REVIEW_APP")

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
        pr_id: current PR id
        pr_title: current PR title
        pr_description: current PR description
        pr_state: current PR state
        pr_diff: current PR code changes
        pr_files: current PR files path
    """

    question: str
    generation: str
    documents: List[str]

    pr_id: str # current PR id
    pr_title: str # current PR title
    pr_description: str # current PR description
    pr_state: str # current PR state
    pr_diff: str # current PR code changes
    pr_files: str # current PR files path


### Nodes ###

def get_pr_node(state):
    """
    Get PR information and download base code files.

    Args:
        state (dict): The current graph state containing the PR URL in 'question'

    Returns:
        state (dict): Updated state with PR information and file paths
    """
    logger.info("---GET PR INFO---")
    pr_url = state["question"]
    
    # Parse PR URL to extract owner, repo and pr_number
    # Example URL: https://github.com/owner/repo/pull/123
    pattern = r'https://github\.com/([\w-]+)/([\w-]+)/pull/(\d+)'
    match = re.match(pattern, pr_url)
    
    if not match:
        logger.error(f"---ERROR: INVALID PR URL FORMAT: {pr_url}---")
        return {"question": pr_url, "error": f"Invalid PR URL format: {pr_url}"}
    
    owner, repo, pr_number = match.groups()
    pr_number = int(pr_number)
    
    # Get GitHub token from environment if available
    github_token = os.environ.get("GITHUB_TOKEN", None)
    
    try:
        # Initialize exporters
        pr_exporter = GitHubPRToExcelExporter(token=github_token)
        pr_downloader = PRFilesPreDownloader(token=github_token)
        
        # Get PR details
        logger.info(f"---GETTING PR #{pr_number} DETAILS---")
        pr_details = pr_exporter.get_pr_details(owner, repo, pr_number)
        
        # Get PR status (open/closed)
        pr_state = pr_details.get("state", "unknown")
        logger.info(f"---PR STATUS: {pr_state.upper()}---")
        
        # Get PR title, description and diff
        pr_title = pr_details.get("title", "")
        pr_description = pr_details.get("body", "")
        pr_diff = pr_exporter.get_pr_diff(owner, repo, pr_number)
        
        # Download PR base code files
        pr_id = str(pr_number)
        
        # 使用配置管理器获取PR审查数据目录路径
        config_manager = ConfigManager()
        data_dir = config_manager.get_pr_review_data_dir()
        base_code_dir = os.path.join(data_dir, owner, repo, "base_code", pr_id)
        logger.info(f"---DOWNLOADING PR BASE CODE TO {base_code_dir}---")
        
        # Ensure the base code directory exists
        os.makedirs(base_code_dir, exist_ok=True)
        
        # Download files
        downloaded_files = pr_downloader.download_pr_files_before(
            owner, repo, pr_number, base_code_dir
        )
        
        logger.info(f"---SUCCESSFULLY DOWNLOADED {len(downloaded_files)} FILES---")
        
        # Update state with PR information
        updated_state = {
            "question": pr_url,
            "pr_id": pr_id,
            "pr_title": pr_title,
            "pr_description": pr_description,
            "pr_state": pr_state,
            "pr_diff": pr_diff,
            "pr_files": base_code_dir
        }
        
        return updated_state
        
    except Exception as e:
        logger.error(f"---ERROR GETTING PR INFO: {str(e)}---")
        # 确保返回完整的状态，包含所有原始字段并添加error信息
        updated_state = state.copy() if isinstance(state, dict) else {}
        updated_state["question"] = pr_url
        updated_state["error"] = str(e)
        updated_state["pr_state"] = "unknown"
        return updated_state


def retriever_node(state):
    """
    Retrieve documents using question and PR diff (if available).

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    logger.info("---RETRIEVE---")
    original_question = state["question"]
    pr_diff = state.get("pr_diff", "")
    pr_title = state.get("pr_title", "")
    pr_files = state.get("pr_files", "")
    
    # Create a combined query using the original question and PR diff if available
    if pr_diff:
        logger.info("---USING PR DIFF AS PART OF THE QUERY---")
        # Extract code changes with context from PR diff
        # Focus on the most important parts of the diff
        diff_lines = pr_diff.split('\n')
        # Filter for actual code changes (lines starting with +, -, or @@ for diff headers)
        relevant_diff_lines = [line for line in diff_lines if line.startswith(('+', '-', '@@'))]
        # Take up to 30 lines to get good context without being too long
        filtered_diff = '\n'.join(relevant_diff_lines[:30])
        
        # Extract file names from diff headers
        file_names = []
        for line in diff_lines:
            if line.startswith('+++') or line.startswith('---'):
                parts = line.split('/')
                if len(parts) > 0:
                    file_names.append(parts[-1])
        
        # Create a targeted search prompt to find similar code changes and related review comments
        search_question = f"""Please find code changes similar to the following PR changes and their corresponding review comments:
            PR Title: {state["pr_title"]}
            PR Description: {state["pr_description"]}
            Code Changes:
            {pr_diff}

            Special Notes:
            1. Please retrieve the complete comment content between the markers ## REVIEW COMMENTS START ## and ## REVIEW COMMENTS END ##
            2. Ensure to include all comments and conversations from all reviewers
            3. Comments are usually after code changes, please prioritize finding documents containing complete comment threads"""
    else:
        search_question = original_question
    
    # Retrieval
    # 使用全局vectorstore（如果已设置）
    vectorstore = get_global_vectorstore()
    
    if vectorstore:
        logger.info(f"---Using global vectorstore for retrieval---")
        # 调整检索策略：先进行初步检索
        initial_docs = vectorstore.similarity_search(search_question, k=5)
        
        # 过滤并排序文档，优先保留包含评论的文档
        filtered_docs = []
        for doc in initial_docs:
            content = doc.page_content
            # 检查是否包含评论部分标记
            if '## REVIEW COMMENTS START ##' in content and '## REVIEW COMMENTS END ##' in content:
                filtered_docs.append(doc)
        
        # 如果找到了包含评论的文档，使用这些；否则使用原始检索结果的前2个
        if filtered_docs:
            documents = filtered_docs[:2]  # 最多使用2个最相关的包含评论的文档
        else:
            documents = initial_docs[:2]
    else:
        logger.info(f"---Using default retriever for retrieval---")
        documents = retriever.invoke(search_question)
    
    logger.info(f"---RETRIEVED {len(documents)} DOCUMENTS---")
    
    # 更新状态，保留owner和repo信息
    updated_state = {"documents": documents, "question": original_question, "pr_diff": pr_diff, "pr_title": pr_title, "pr_files": pr_files}
    return updated_state


def grader_node(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """

    logger.info("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]
    pr_diff = state.get("pr_diff", "")
    pr_title = state.get("pr_title", "")
    pr_files = state.get("pr_files", "")

    # Score each doc
    filtered_docs = []
    for d in documents:
        score = retrieval_grader.invoke(
            {"question": pr_diff, "document": d.page_content}
        )
        grade = score.binary_score
        if grade == "yes":
            logger.info("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            logger.info("---GRADE: DOCUMENT NOT RELEVANT---")
            continue
    return {"documents": filtered_docs, "question": question, "pr_diff": pr_diff, "pr_title": pr_title, "pr_files": pr_files}


def generate_node(state):
    """
    Generate answer based on relevant historical PR comments

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    logger.info("---GENERATE---")
    
    # Extract relevant information from state
    pr_url = state["question"]
    pr_title = state.get("pr_title", "")
    pr_diff = state.get("pr_diff", "")
    documents = state["documents"]
    
    # Extract PR IDs from documents and format documents with PR ID information
    formatted_docs_with_ids = []
    for doc in documents:
        # Try to get PR ID from metadata first
        pr_id = doc.metadata.get('pr_id', 'Unknown')
        
        # If not found in metadata, try to extract from page_content
        if pr_id == 'Unknown':
            import re
            match = re.search(r'PR ID: (\d+)', doc.page_content)
            if match:
                pr_id = match.group(1)
        
        # Format document with PR ID information
        formatted_docs_with_ids.append(f"PR ID: {pr_id}\n{doc.page_content}")
    
    # Create formatted documents text with PR IDs
    docs_txt = "\n\n---\n\n".join(formatted_docs_with_ids)
    
    # Create a comprehensive question that includes PR details and code changes
    # Extract key parts of the diff for better context
    diff_lines = pr_diff.split('\n')
    relevant_diff_lines = [line for line in diff_lines if line.startswith(('+', '-', '@@'))][:20]
    filtered_diff = '\n'.join(relevant_diff_lines)
    
    # Format the question to focus on identifying repeated issues and include PR ID requirements
    question = f"""Analyze whether the current PR repeats errors or issues already found in historical PRs:

PR Information:
- URL: {pr_url}
- Title: {pr_title}

Current PR key code changes:
```diff
{filtered_diff}
```

Please analyze whether questions or concerns mentioned in historical PR review comments might reappear in the current PR and provide relevant recommendations.

IMPORTANT REQUIREMENT: When referencing any historical PR review comments in your analysis, please always clearly indicate the corresponding historical PR ID from which the comment was extracted. For example: "From PR #123: 'This is a comment about...'"""
    
    # RAG generation
    generation = rag_chain.invoke({"context": docs_txt, "question": question})
    
    return {"documents": documents, "question": question, "generation": generation}


def format_as_mindmap(comments):
    """
    将代码审查结果格式化为思维导图样式的可读文本
    
    Args:
        comments: CodeReviewResult对象
    
    Returns:
        str: 格式化后的思维导图文本
    """
    result = []
    result.append("# 代码审查结果")
    result.append("\n## 总体评价")
    result.append(f"- {comments.overall_evaluation}")
    
    if comments.specific_issues:
        result.append("\n## 具体问题")
        for i, issue in enumerate(comments.specific_issues, 1):
            result.append(f"- 问题 {i}:")
            # 将问题文本按行分割，每行缩进展示
            for line in issue.split('\n'):
                if line.strip():
                    result.append(f"  └── {line.strip()}")
    
    if comments.improvement_suggestions:
        result.append("\n## 改进建议")
        for i, suggestion in enumerate(comments.improvement_suggestions, 1):
            result.append(f"- 建议 {i}:")
            for line in suggestion.split('\n'):
                if line.strip():
                    result.append(f"  └── {line.strip()}")
    
    if comments.code_examples:
        result.append("\n## 代码示例")
        examples = []
        
        logger.info(f"---CODE EXAMPLES: {comments.code_examples}---")
        # 处理可能包含JSON字符串的情况
        for item in comments.code_examples:
            if isinstance(item, str):   
                try:                
                    # 尝试解析为JSON
                    parsed_data = json.loads(item)
                    
                    # 如果解析成功并且是列表，直接扩展
                    if isinstance(parsed_data, list):
                        examples.extend(parsed_data)
                    else:
                        # 如果解析成功但不是列表，添加到示例中
                        examples.append(str(parsed_data))
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.info(f"---JSON解析失败，异常信息: {e}---")
                    # 检查是否包含bash字符串，如果是则尝试修复
                    if 'bash' in item:
                        try:
                            # 导入修复函数
                            from .audit_json_bash_fixed import audit_and_fix_bash_json
                            logger.info("---检测到bash命令，尝试修复JSON字符串---")
                            # 修复包含bash命令的JSON字符串
                            fixed_item = audit_and_fix_bash_json(item)
                            # 尝试重新解析修复后的字符串
                            parsed_fixed_data = json.loads(fixed_item)
                            # 如果修复后解析成功，添加修复后的数据
                            if isinstance(parsed_fixed_data, list):
                                examples.extend(parsed_fixed_data)
                            else:
                                examples.append(str(parsed_fixed_data))
                            continue
                        except Exception as fix_e:
                            logger.info(f"---修复JSON失败，异常信息: {fix_e}---")
                    # 如果不包含bash字符串或修复失败，添加原始内容
                    examples.append(item)
            else:
                # 如果不是字符串，转换为字符串后添加
                examples.append(str(item))
        
        # 遍历所有示例并格式化输出
        for i, example in enumerate(examples, 1):
            result.append(f"- 示例 {i}:")
            
            # 检测代码语言（如果示例开头有#标记）
            language = "python"  # 默认语言
            first_line = example.split('\n')[0].strip()
            example_lower = example.lower()
            
            # 检查是否包含Jinja2模板语法
            if any(['{%' in line or '{{' in line for line in example.split('\n')]):
                language = "jinja"
            # 检测bash脚本
            elif any([
                first_line.startswith('#!/bin/bash'),
                first_line.startswith('#!/bin/sh'),
                '$(' in example,
                'if [ ' in example,
                'echo ' in example_lower,
                'for ' in example_lower and 'do' in example_lower,
                'while ' in example_lower and 'do' in example_lower,
                '$' in example and ('{' in example or '}' in example),  # 检测变量引用如${var}
                'export ' in example_lower
            ]):
                language = "bash"
            # 检测C/C++代码
            elif any([
                '#include' in example,
                'int main' in example_lower,
                'void ' in example_lower,
                'class ' in example_lower,
                'struct ' in example_lower,
                'cout' in example_lower,
                'printf' in example_lower,
                'namespace std' in example_lower
            ]):
                # 简单区分C和C++
                if 'cout' in example_lower or 'namespace std' in example_lower or 'class' in example_lower:
                    language = "cpp"
                else:
                    language = "c"
            
            # 如果第一行是```，则直接添加代码内容
            if not first_line.startswith('```'):
                result.append(f"  ```{language}")
                logger.info(f"  ```{language}")
            
            code_lines = example.split('\n')
            for line in code_lines:
                if line.strip():
                    result.append(f"  {line}")
                    logger.info(f"  {line}")
            if not "```" in code_lines[-1]:
                result.append("  ```")
                logger.info("  ```")
    
    return '\n'.join(result)

def review_by_llm_node(state):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """

    logger.info("---REVIEW BY LLM---")
    #logger.info(f"当前状态信息: {pformat(state)}")
    question = f"Please review PR {state["question"]}, and give your comments on this PR"

    # Re-write question
    pr_title = state['pr_title']
    pr_files_path = state['pr_files']
    files = []
    # 遍历目录，找出所有文件
    for root, dirs, filenames in os.walk(pr_files_path):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    original_file_content = ""
    for file in files:
        with open(file, 'r') as f:
            original_file_content += f.read() + "\n\n"
    code_diff = state['pr_diff']
    general_comments = general_reviewer.invoke({"question": question, "pr_title": pr_title, "original_file_content": original_file_content, "code_diff": code_diff})
    
    # 处理code_examples字段，确保它是正确的类型
    if hasattr(general_comments, 'code_examples'):
        # 检查code_examples是否是字符串'None'
        if isinstance(general_comments.code_examples, str) and general_comments.code_examples.lower() == 'none':
            general_comments.code_examples = None
        # 如果不是列表，则转换为列表
        elif not isinstance(general_comments.code_examples, list) and general_comments.code_examples is not None:
            general_comments.code_examples = [general_comments.code_examples]
    
    # 将general_comments格式化为思维导图样式的可读文本
    formatted_output = format_as_mindmap(general_comments)
    
    return {"question": question, "generation": formatted_output}


def general_question_node(state):
    """
    Web search based on the re-phrased question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with appended web results
    """

    logger.info("---GENERAL QUESTION---")
    question = state["question"]

    # Web search
    docs = general_question_chain.invoke({"query": question})
    web_results = "\n".join([d["content"] for d in docs])

    return {"documents": [web_results], "question": question}

def binary_only_end_node(state):
    """
    Node to handle binary-only PRs, adds a message to state and returns.
    
    Args:
        state (dict): The current graph state
        
    Returns:
        dict: Updated state with generation message
    """
    # Add a message to state explaining why review is not needed
    logger.info("---PROCESSING BINARY-ONLY PR---")
    logger.debug(f"二进制PR状态信息: {pformat(state)}")
    state["generation"] = "PR只包含二进制文件的更改，不需要进行代码审查。"
    logger.info("---BINARY-ONLY PR PROCESSING COMPLETED---")
    return state


def invalid_pr_node(state):
    """
    Node to handle invalid PRs (non-open state), adds a message to state and returns.
    
    Args:
        state (dict): The current graph state
        
    Returns:
        dict: Updated state with generation message
    """
    # Add a message to state explaining why review is not needed
    logger.info("---PROCESSING INVALID PR---")
    logger.debug(f"无效PR状态信息: {pformat(state)}")
    state["generation"] = "当前PR非open状态，不需要进行代码审查。"
    logger.info(f"---INVALID PR PROCESSING COMPLETED: PR_STATE={state.get('pr_state', 'unknown')}---")
    return state


def error_pr_node(state):
    """
    Node to handle invalid PRs (non-open state), adds a message to state and returns.
    
    Args:
        state (dict): The current graph state
        
    Returns:
        dict: Updated state with generation message
    """
    # Add a message to state explaining why review is not needed
    logger.info("---PROCESSING ERROR PR---")
    logger.debug(f"错误PR状态信息: {pformat(state)}")
    error = state.get("error", "")
    state["generation"] = f"当前PR获取失败，错误信息：{error}。"
    logger.info(f"---ERROR PR PROCESSING COMPLETED: ERROR={error}---")
    return state


### Edges ###

def condition_route_question(state):
    """
    Route question to web search or RAG.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """

    logger.info("---ROUTE QUESTION---")
    logger.debug(f"当前状态信息: {pformat(state)}")
    question = state["question"]
    source = question_router.invoke({"question": question})
    if source.datasource == "general_question":
        logger.info("---ROUTE QUESTION TO GENERAL QUESTION---")
        return "general_question"
    elif source.datasource == "vectorstore":
        logger.info("---ROUTE QUESTION TO RAG---")
        return "vectorstore"


def condition_check_pr_state(state):
    """
    Check PR state to determine if it's valid.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call based on PR state
    """

    logger.info("---CHECK PR STATE---")
    pr_state = state.get("pr_state", "unknown")
    
    # Check if PR is open
    if pr_state == "open":
        # Get PR diff content
        pr_diff = state.get("pr_diff", "")
        code_diff = state.get("code_diff", "")
        
        # Combine all diff content for checking
        all_diff = pr_diff + code_diff
        
        # Count occurrences of 'Binary files' in diff
        binary_files_count = all_diff.count("Binary files")
        
        # Get PR files directory path
        pr_files_path = state.get("pr_files", "")
        
        # Count total files in PR files directory
        total_files_count = 0
        if pr_files_path and os.path.exists(pr_files_path):
            for root, dirs, files in os.walk(pr_files_path):
                total_files_count += len(files)
        
        # Check if number of binary files matches total files count
        if binary_files_count > 0 and binary_files_count == total_files_count:
            logger.info(f"---DECISION: PR CONTAINS ONLY BINARY CHANGES ({binary_files_count} files), STOP PROCESSING---")
            return "binary_only_pr"
        
        logger.info("---DECISION: PR IS OPEN AND CONTAINS CODE CHANGES, CONTINUE PROCESSING---")
        return "valid_pr"
    else:
        if pr_state == "unknown":
            error = state.get("error", "")
            logger.info(f"---DECISION: PR ERROR GOT WHICH IS {error.upper()}, STOP PROCESSING---")
            return "error_pr"
        else:
            logger.info(f"---DECISION: PR IS {pr_state.upper()}, STOP PROCESSING---")
            return "invalid_pr"


def condition_decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    logger.info("---ASSESS GRADED DOCUMENTS---")
    state["question"]
    filtered_documents = state["documents"]

    if not filtered_documents:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        logger.info(
            "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "review_by_llm"
    else:
        # We have relevant documents, so generate answer
        logger.info("---DECISION: GENERATE---")
        return "generate"


def condition_hallucination_evaluation(state):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    logger.info("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]

    score = hallucination_grader.invoke(
        {"question": question, "documents": documents, "generation": generation}
    )
    grade = score.binary_score

    # Check hallucination
    if grade == "yes":
        logger.info("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        return "no_hallucination"
    else:
        logger.warning("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "hallucination"
