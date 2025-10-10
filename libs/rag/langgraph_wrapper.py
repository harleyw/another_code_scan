from libs.rag_base.graphs.graph_build import app as graph_app

class LangGraphWrapper:
    """LangGraph的封装类，简化对LangGraph的调用"""
    
    def __init__(self, vectorstore=None):
        """初始化LangGraph包装器"""
        self.vectorstore = vectorstore
        # 如果需要传递vectorstore到graph_app，可以在这里实现
        
    async def query(self, question: str) -> str:
        """使用LangGraph执行查询并返回结果"""
        if not question:
            return "请提供有效的问题"
        
        try:
            # 构建输入参数
            inputs = {"question": question}
            generation = None
            
            # 执行图并获取结果
            for output in graph_app.stream(inputs):
                for key, value in output.items():
                    if "generation" in value:
                        generation = value["generation"]
                        break
                if generation:
                    break
            
            # 如果没有生成结果，使用默认值
            if not generation:
                generation = "抱歉，无法回答这个问题。"
            
            return generation
        except Exception as e:
            print(f"LangGraph查询出错: {str(e)}")
            return f"查询过程中发生错误: {str(e)}"
    
    def set_vectorstore(self, vectorstore):
        """设置vectorstore"""
        self.vectorstore = vectorstore
    
    def get_status(self) -> dict:
        """获取LangGraph的状态信息"""
        # 这里可以添加更多的状态信息
        return {
            "initialized": True,
            "vectorstore_available": self.vectorstore is not None
        }