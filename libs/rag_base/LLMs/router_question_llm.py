### Router

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatDashScope

from pydantic import BaseModel, Field


# Data model
class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    datasource: Literal["vectorstore", "general_question"] = Field(
        ...,
        description="Given a user question choose to route it to general question answer or a vectorstore.",
    )


# LLM with function call
llm = ChatDashScope(model="qwen-plus", temperature=0)
structured_llm_router = llm.with_structured_output(RouteQuery)

# Prompt
system = """You are an expert at routing a user query to the most appropriate datasource.
Your task is to determine whether a query is about a GitHub Pull Request (PR) or a general question.

## Classification Rules:
- **ROUTE TO vectorstore** if the query:
  - Contains a GitHub PR URL (e.g., "https://github.com/org/repo/pull/123")
  - Mentions a specific PR by number (e.g., "PR #123", "Pull Request 456")
  - Contains terms like "PR", "pull request", "PR review", "PR comments" along with specific identifiers or context
  - Asks about code changes, review comments, or details of a specific PR
  
- **ROUTE TO general_question** if the query:
  - Is a general question not related to any specific GitHub PR
  - Asks about concepts, theories, or general knowledge
  - Requests information not tied to a specific repository or PR

## Vectorstore Content:
The vectorstore contains merged PRs data including PR IDs, descriptions, general comments, review comments, issue comments, and code changes.

## Response Format:
Respond with the appropriate datasource based strictly on the above rules."""
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

question_router = route_prompt | structured_llm_router

# example:
# print(
#     question_router.invoke(
#         {"question": "Who will the Bears draft first in the NFL draft?"}
#     )
# )
# print(question_router.invoke({"question": "What are the types of agent memory?"}))
