### Generate

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models.tongyi import ChatTongyi

from util.config_manager import ConfigManager

# Custom RAG prompt focused on analyzing historical PR comments in relation to current PR code changes
system_prompt = """You are a professional code review expert, responsible for analyzing the relevance of historical PR comments to current PR code changes.

Your tasks are:
1. Analyze the provided historical PR review comments to identify code errors, issues, or improvement suggestions mentioned
2. Evaluate whether these issues might reappear in the current PR
3. Present your findings in a clear, structured manner

Please follow these principles:
- Focus on code errors and issues that might be repeated
- Provide specific, actionable recommendations rather than general remarks
- Clearly indicate which comments are most relevant to the current PR and why
- When possible, offer specific suggestions on how to fix these issues
- Use professional but easy-to-understand language

Output format:
1. First provide a brief summary stating whether you've found the current PR might be repeating errors from historical PRs
2. Then list the specific issues found, each including:
   - Issue description
   - Relevant historical comments
   - Why this issue is relevant to the current PR
   - Specific improvement suggestions
3. Finally provide a brief conclusion and overall recommendations"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "Historical PR comments:\n\n{context}\n\nCurrent PR review request:\n\n{question}"),
    ]
)

# Initialize config manager and get API key
config_manager = ConfigManager()
dashscope_api_key = config_manager.get_dashscope_api_key()

# LLM
llm = ChatTongyi(model="qwen-plus", temperature=0, dashscope_api_key=dashscope_api_key)


# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# Chain
rag_chain = prompt | llm | StrOutputParser()

# Run
#docs_txt = format_docs(docs)
#generation = rag_chain.invoke({"context": docs_txt, "question": question})
#print(generation)
