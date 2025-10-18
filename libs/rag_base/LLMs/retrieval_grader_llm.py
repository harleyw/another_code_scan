### Retrieval Grader

from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models.tongyi import ChatTongyi
from pydantic import BaseModel, Field

from util.config_manager import ConfigManager

# Data model
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


# Initialize config manager and get API key
config_manager = ConfigManager()
dashscope_api_key = config_manager.get_dashscope_api_key()

# LLM with function call
llm = ChatTongyi(model="qwen-plus", temperature=0, dashscope_api_key=dashscope_api_key)
structured_llm_grader = llm.with_structured_output(GradeDocuments)

# Prompt
system = """You are a grader assessing relevance of a retrieved review comment to current PR code changes. 
Your task is to determine if a historical PR review comment might be relevant to the current PR's code changes,
particularly if it indicates the same or similar code errors or implementation issues.

Consider the following when grading:
1. Does the review comment discuss similar code patterns, structures, or functions?
2. Does it identify errors or issues that might also exist in the current code changes?
3. Are there common implementation approaches or anti-patterns being discussed?
4. Is there semantic similarity between the reviewed code context and current code changes?

Grade 'yes' if the comment appears relevant to the current code changes, especially if it suggests the current PR
might be repeating a mistake that was previously identified in another PR. Grade 'no' only if the comment is clearly unrelated.

Give a binary score 'yes' or 'no' to indicate relevance."""
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Retrieved review comment: \n\n {document} \n\n Current PR code changes: {question}"),
    ]
)

retrieval_grader = grade_prompt | structured_llm_grader
# Test code (commented out)
# question = "agent memory"
# docs = retriever.invoke(question)
# doc_txt = docs[1].page_content
# print(retrieval_grader.invoke({"question": question, "document": doc_txt}))
