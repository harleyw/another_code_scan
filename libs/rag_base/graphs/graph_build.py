from graph_defs import GraphState, get_pr_node, general_question_node, retriever_node, grader_node, generate_node, review_by_llm_node, condition_route_question, condition_check_pr_state, condition_decide_to_generate, condition_hallucination_evaluation
from langgraph.graph import END, StateGraph, START

workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("get_pr_node", get_pr_node)          # 获取PR信息
workflow.add_node("general_question_node", general_question_node)  # 处理一般问题
workflow.add_node("retriever_node", retriever_node)      # 检索相关文档
workflow.add_node("grader_node", grader_node)          # 评估文档相关性
workflow.add_node("generate_node", generate_node)        # 生成PR审查评论
workflow.add_node("review_by_llm_node", review_by_llm_node)  # 直接LLM审查

# Build graph - 开始路由
workflow.add_conditional_edges(
    START,
    condition_route_question,
    {
        "general_question": "general_question_node",
        "vectorstore": "get_pr_node",
    },
)

# 处理一般问题路径
workflow.add_edge("general_question_node", END)

# PR处理路径
workflow.add_conditional_edges(
    "get_pr_node",
    condition_check_pr_state,
    {
        "valid_pr": "retriever_node",
        "invalid_pr": "review_by_llm_node",
    },
)

# 检索和评估路径
workflow.add_edge("retriever_node", "grader_node")

# 决策生成还是直接审查
workflow.add_conditional_edges(
    "grader_node",
    condition_decide_to_generate,
    {
        "review_by_llm": "review_by_llm_node",
        "generate": "generate_node",
    },
)

# 幻觉检测路径
workflow.add_conditional_edges(
    "generate_node",
    condition_hallucination_evaluation,
    {
        "no_hallucination": END,
        "hallucination": "review_by_llm_node",
    },
)

# 最终路径到结束
workflow.add_edge("review_by_llm_node", END)

# Compile
app = workflow.compile()
