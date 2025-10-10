import re
import os
from typing import List

from typing_extensions import TypedDict
from libs.rag_base.LLMs.router_question_llm import question_router
from libs.rag_base.LLMs.retrieval_grader_llm import retrieval_grader
from libs.rag_base.LLMs.generater_llm import format_docs, rag_chain
from libs.rag_base.LLMs.hallucination_grader_llm import hallucination_grader
from libs.rag_base.LLMs.answer_grader_llm import answer_grader
from libs.rag_base.knowledge_base.build_rag_base import retriever
from libs.rag_base.LLMs.general_reviewer_llm import general_reviewer
from libs.rag_base.LLMs.general_question_llm import general_question_chain
from pprint import pprint
from langchain.schema import Document

# Import PR tools
from github_pr_to_excel import GitHubPRToExcelExporter
from pr_files_pre_downloader import PRFilesPreDownloader

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
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
    print("---GET PR INFO---")
    pr_url = state["question"]
    
    # Parse PR URL to extract owner, repo and pr_number
    # Example URL: https://github.com/owner/repo/pull/123
    pattern = r'https://github\.com/([\w-]+)/([\w-]+)/pull/(\d+)'
    match = re.match(pattern, pr_url)
    
    if not match:
        print("---ERROR: INVALID PR URL---")
        return {"question": pr_url, "error": "Invalid PR URL format"}
    
    owner, repo, pr_number = match.groups()
    pr_number = int(pr_number)
    
    # Get GitHub token from environment if available
    github_token = os.environ.get("GITHUB_TOKEN", None)
    
    try:
        # Initialize exporters
        pr_exporter = GitHubPRToExcelExporter(token=github_token)
        pr_downloader = PRFilesPreDownloader(token=github_token)
        
        # Get PR details
        print(f"---GETTING PR #{pr_number} DETAILS---")
        pr_details = pr_exporter.get_pr_details(owner, repo, pr_number)
        
        # Get PR status (open/closed)
        pr_state = pr_details.get("state", "unknown")
        print(f"---PR STATUS: {pr_state.upper()}---")
        
        # Get PR title, description and diff
        pr_title = pr_details.get("title", "")
        pr_description = pr_details.get("body", "")
        pr_diff = pr_exporter.get_pr_diff(owner, repo, pr_number)
        
        # Download PR base code files
        pr_id = str(pr_number)
        base_code_dir = os.path.join(".", "pr_base_code", pr_id)
        print(f"---DOWNLOADING PR BASE CODE TO {base_code_dir}---")
        
        # Ensure the base code directory exists
        os.makedirs(base_code_dir, exist_ok=True)
        
        # Download files
        downloaded_files = pr_downloader.download_pr_files_before(
            owner, repo, pr_number, base_code_dir
        )
        
        print(f"---SUCCESSFULLY DOWNLOADED {len(downloaded_files)} FILES---")
        
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
        print(f"---ERROR GETTING PR INFO: {str(e)}---")
        return {"question": pr_url, "error": str(e)}


def retriever_node(state):
    """
    Retrieve documents using question and PR diff (if available).

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    original_question = state["question"]
    pr_diff = state.get("pr_diff", "")
    pr_title = state.get("pr_title", "")
    pr_files = state.get("pr_files", "")
    
    # Create a combined query using the original question and PR diff if available
    if pr_diff:
        print("---USING PR DIFF AS PART OF THE QUERY---")
        # Extract a snippet of the PR diff for the query (to avoid making it too long)
        # We'll take the first 500 characters as a sample
        diff_snippet = pr_diff[:500] if len(pr_diff) > 500 else pr_diff
        search_question = f"{original_question}\n\nRelated PR code changes:\n{diff_snippet}"
    else:
        search_question = original_question
    
    # Retrieval
    documents = retriever.invoke(search_question)
    print(f"---RETRIEVED {len(documents)} DOCUMENTS---")
    
    # Return original question to maintain consistency with the rest of the workflow
    return {"documents": documents, "question": original_question, "pr_diff": pr_diff, "pr_title": pr_title, "pr_files": pr_files}


def grader_node(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
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
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            continue
    return {"documents": filtered_docs, "question": question, "pr_diff": pr_diff, "pr_title": pr_title, "pr_files": pr_files}


def generate_node(state):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = f"Please review PR {state["question"]}, and give your comments on this PR"
    documents = state["documents"]

    # RAG generation
    docs_txt = format_docs(documents)
    generation = rag_chain.invoke({"context": docs_txt, "question": question})
    return {"documents": documents, "question": question, "generation": generation}


def review_by_llm_node(state):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """

    print("---GENERAL REVIEW---")
    question = f"Please review PR {state["question"]}, and give your comments on this PR"

    # Re-write question
    pr_title = state['pr_title']
    files = state['pr_files']
    original_file_content = ""
    for file in files:
        with open(file, 'r') as f:
            original_file_content += f.read() + "\n\n"
    code_diff = state['pr_diff']
    general_comments = general_reviewer.invoke({"question": question, "pr_title": pr_title, "pr_files": original_file_content, "pr_diff": code_diff})
    
    return {"question": question, "generation": general_comments}


def general_question_node(state):
    """
    Web search based on the re-phrased question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with appended web results
    """

    print("---GENERAL QUESTION---")
    question = state["question"]

    # Web search
    docs = general_question_chain.invoke({"query": question})
    web_results = "\n".join([d["content"] for d in docs])

    return {"documents": [web_results], "question": question}


### Edges ###

def condition_route_question(state):
    """
    Route question to web search or RAG.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """

    print("---ROUTE QUESTION---")
    question = state["question"]
    source = question_router.invoke({"question": question})
    if source.datasource == "general_question":
        print("---ROUTE QUESTION TO GENERAL QUESTION---")
        return "general_question"
    elif source.datasource == "vectorstore":
        print("---ROUTE QUESTION TO RAG---")
        return "vectorstore"


def condition_check_pr_state(state):
    """
    Check PR state to determine if it's valid.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call based on PR state
    """

    print("---CHECK PR STATE---")
    pr_state = state.get("pr_state", "unknown")
    
    if pr_state == "open":
        print("---DECISION: PR IS OPEN, CONTINUE PROCESSING---")
        return "valid_pr"
    else:
        print(f"---DECISION: PR IS {pr_state.upper()}, STOP PROCESSING---")
        return "invalid_pr"


def condition_decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    print("---ASSESS GRADED DOCUMENTS---")
    state["question"]
    filtered_documents = state["documents"]

    if not filtered_documents:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print(
            "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "review_by_llm"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "generate"


def condition_hallucination_evaluation(state):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]

    score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )
    grade = score.binary_score

    # Check hallucination
    if grade == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        return "no_hallucination"
    else:
        pprint("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "hallucination"
