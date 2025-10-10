from typing import List, Optional
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatDashScope


# Data model for code review results
class CodeReviewResult(BaseModel):
    """Model for storing code review results."""
    
    overall_evaluation: str = Field(
        ..., 
        description="Brief summary of the overall view of the code change"
    )
    
    specific_issues: List[str] = Field(
        default_factory=list, 
        description="Detailed list of identified issues, including specific line numbers and code snippets"
    )
    
    improvement_suggestions: List[str] = Field(
        default_factory=list, 
        description="Specific modification suggestions for each identified issue"
    )
    
    code_examples: Optional[List[str]] = Field(
        None, 
        description="Optimized code examples if necessary"
    )


# LLM with structured output
llm = ChatDashScope(model="qwen3-coder-plus", temperature=0)
structured_llm_reviewer = llm.with_structured_output(CodeReviewResult)

# Code review prompt template
system_prompt = """# Code Review Prompt Template

## Task Description
Please act as an experienced software engineer to review the following code changes. Please comprehensively analyze the quality of the code changes, potential issues, and areas for improvement, and provide specific feedback and suggestions.

## Change Information
- **PR Title**: {pr_title} (Optional)

## Original File Content Before Changes
```
{original_file_content}
```

## Code Change Diff
```diff
{code_diff}
```

## Review Requirements
Please conduct a comprehensive review from the following aspects:

### 1. Change Purpose Analysis
- What problem is this change trying to solve?
- Is the intent of the change clear and reasonable?

### 2. Implementation Method Evaluation
- Does the implementation method follow best practices?
- Is there a more concise and efficient implementation method?
- Does the code style remain consistent with the overall project?

### 3. Potential Issue Identification
- Are there any bugs or logical errors in the code?
- Are there any hidden risks in terms of performance, security, or maintainability?
- Are boundary conditions and exception handling sufficient?

### 4. Readability and Maintainability
- Is the code easy to understand?
- Do more comments or documentation need to be added?
- Are variable and function names clear?

### 5. Compatibility and Dependencies
- Will the change affect existing functionality?
- Are new dependencies or compatibility issues introduced?

### 6. Test Coverage
- Does the change require corresponding test cases?
- Is the existing test coverage sufficient for this change?

## Output Requirements
Please provide the review results in the following format:
- **Overall Evaluation**: Briefly summarize your overall view of this code change
- **Specific Issues**: List the identified issues in detail, indicating the specific line numbers and code snippets where the issues are located
- **Improvement Suggestions**: Provide specific modification suggestions for each issue
- **Code Examples**: If necessary, provide optimized code examples"""

# Create prompt template
review_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt)
])

# Create the code review chain
general_reviewer = review_prompt | structured_llm_reviewer

# Example usage (commented out)
# example_input = {
#     "file_path": "/path/to/example.py",
#     "pr_title": "Update model to use qwen-plus",
#     "original_file_content": "import ...\n# LLM\nllm = ChatOpenAI(model_name='gpt-4o-mini', temperature=0)",
#     "code_diff": "- llm = ChatOpenAI(model_name='gpt-4o-mini', temperature=0)\n+ llm = ChatDashScope(model='qwen-plus', temperature=0)"
# }
# 
# review_result = general_reviewer.invoke(example_input)
# print("Overall Evaluation:", review_result.overall_evaluation)
# print("Specific Issues:", review_result.specific_issues)
# print("Improvement Suggestions:", review_result.improvement_suggestions)
# if review_result.code_examples:
#     print("Code Examples:", review_result.code_examples)