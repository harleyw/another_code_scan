### Hallucination Grader
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models.tongyi import ChatTongyi

from util.config_manager import ConfigManager

# Data model
class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )

# Initialize config manager and get API key
config_manager = ConfigManager()
dashscope_api_key = config_manager.get_dashscope_api_key()


# LLM with function call
llm = ChatTongyi(model="qwen3-coder-plus", temperature=0, dashscope_api_key=dashscope_api_key)
structured_llm_grader = llm.with_structured_output(GradeHallucinations)

# Prompt
system = """You are a highly precise fact-checker specialized in identifying hallucinations in LLM-generated content, specifically for code review PR analysis.
Your task is to determine whether the provided LLM generation is fully grounded in and supported by both the given question and set of retrieved historical PR documents.

## Definition of Hallucination
A hallucination occurs when the LLM generation contains information that is:
1. Not explicitly stated in the retrieved historical PR documents
2. Cannot be reasonably inferred from the retrieved historical PR documents
3. Contradicts information in the retrieved historical PR documents
4. Introduces concerns or comments not mentioned in historical PRs

## Evaluation Criteria
- **YES**: The entire LLM generation is completely grounded in the retrieved historical PR documents and directly addresses the question. Every factual statement about previous reviewer concerns or comments can be explicitly found or logically inferred from the documents.
- **NO**: The LLM generation contains at least one hallucination - information about previous PR reviews not supported by or contradicting the documents, or irrelevant to the question about repeated mistakes.

## Evaluation Process
1. Carefully read and understand the question about the current PR's code changes
2. Analyze the retrieved historical PR documents for relevant reviewer comments and concerns
3. Examine the LLM generation sentence by sentence
4. For each statement about historical PR issues, verify if it has clear support in the documents
5. Pay special attention to: PR numbers, specific code issues, reviewer comments, technical concerns, and specific claims about previous mistakes
6. If any part of the generation about historical PR concerns is not supported by the documents, mark it as 'NO'

## Example Scenarios
- If question asks about potential repeated mistakes in error handling, documents mention "In PR #123, reviewers commented on missing error checks in network module" and generation says "In PR #123, reviewers commented on incorrect error propagation in network module" → NO
- If question asks about repeated security vulnerabilities, documents don't mention any security concerns in previous PRs, but generation states "Previous PRs #456 and #789 identified security issues with input validation" → NO
- If question asks about performance problems, documents state "In PR #456, reviewers noted excessive memory usage in data processing functions" and generation says "Historical reviews identified resource utilization concerns in similar data processing implementations" → YES (reasonable inference)

**Response Requirement:** Provide only 'yes' or 'no' as your final determination."""
hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Question: \n\n {question} \n\n Retrieved historical PR documents: \n\n {documents} \n\n LLM generation: {generation}"),
    ]
)

hallucination_grader = hallucination_prompt | structured_llm_grader
#hallucination_grader.invoke({"documents": docs, "generation": generation})
