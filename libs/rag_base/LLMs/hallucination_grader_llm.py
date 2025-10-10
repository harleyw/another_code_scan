### Hallucination Grader
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatDashScope

# Data model
class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )


# LLM with function call
llm = ChatDashScope(model="qwen3-coder-plus", temperature=0)
structured_llm_grader = llm.with_structured_output(GradeHallucinations)

# Prompt
# system = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. 
#      Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""
system = """You are a highly precise fact-checker specialized in identifying hallucinations in LLM-generated content.
Your task is to determine whether the provided LLM generation is fully grounded in and supported by the given set of retrieved facts.

## Definition of Hallucination
A hallucination occurs when the LLM generation contains information that is:
1. Not explicitly stated in the retrieved facts
2. Cannot be reasonably inferred from the retrieved facts
3. Contradicts information in the retrieved facts

## Evaluation Criteria
- **YES**: The entire LLM generation is completely grounded in the retrieved facts. Every factual statement in the generation can be explicitly found or logically inferred from the facts.
- **NO**: The LLM generation contains at least one hallucination - information not supported by or contradicting the retrieved facts.

## Evaluation Process
1. Carefully read and understand the retrieved facts
2. Analyze the LLM generation sentence by sentence
3. For each statement in the generation, verify if it has clear support in the facts
4. Pay special attention to: names, numbers, dates, technical details, and specific claims
5. If any part of the generation is not supported by the facts, mark it as 'NO'

## Example Scenarios
- If facts mention "Project A was completed in 2023" and generation says "Project A was completed in 2022" → NO
- If facts don't mention anything about "Project B" but generation discusses "Project B's features" → NO
- If facts state "Team X consists of 5 members" and generation says "Team X has several members" → YES (reasonable inference)

**Response Requirement:** Provide only 'yes' or 'no' as your final determination."""
hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
    ]
)

hallucination_grader = hallucination_prompt | structured_llm_grader
#hallucination_grader.invoke({"documents": docs, "generation": generation})
