### Generate

from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatDashScope

# Prompt
prompt = hub.pull("rlm/rag-prompt")

# LLM
llm = ChatDashScope(model="qwen-plus", temperature=0)


# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# Chain
rag_chain = prompt | llm | StrOutputParser()

# Run
#docs_txt = format_docs(docs)
#generation = rag_chain.invoke({"context": docs_txt, "question": question})
#print(generation)
