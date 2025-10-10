from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatDashScope
from pydantic import BaseModel, Field

# Data model
class GeneralAnswer(BaseModel):
    """General answer to a user question."""
    
    answer: str = Field(
        ...,
        description="A comprehensive and accurate answer to the user's question.",
    )

# LLM with function call
llm = ChatDashScope(model="qwen-plus", temperature=0)
structured_llm_answer = llm.with_structured_output(GeneralAnswer)

# Prompt
system = """You are an AI assistant that provides comprehensive and accurate answers to user questions.
Your answers should be clear, concise, and based on your knowledge.
If you don't know the answer to a question, simply state that you don't know."""
general_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

general_question_chain = general_prompt | structured_llm_answer

# Test code (commented out)
# print(
#     general_question_chain.invoke(
#         {"question": "什么是人工智能？"}
#     )
# )
# print(
#     general_question_chain.invoke(
#         {"question": "请解释机器学习的基本原理。"}
#     )
# )