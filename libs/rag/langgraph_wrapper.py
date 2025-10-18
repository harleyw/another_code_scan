from libs.rag_base.graphs.graph_build import app as graph_app
import traceback

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
                try:
                    for key, value in output.items():
                        if "generation" in value:
                            generation = value["generation"]
                            break
                except Exception as inner_e:
                    # 捕获处理每个输出项时可能发生的错误
                    print(f"处理图输出时出错: {str(inner_e)}")
                    continue
                if generation:
                    break
            
            # 如果没有生成结果，使用默认值
            if not generation:
                generation = "抱歉，无法回答这个问题。"
            
            return generation
        except Exception as e:
            error_message = str(e)
            error_traceback = traceback.format_exc()
            print(f"LangGraph查询出错: {error_message}")
            print(f"错误详情:\n{error_traceback}")
            # 特殊处理binary_only_pr情况
            if "binary_only_pr" in error_message:
                return "PR只包含二进制文件的更改，不需要进行代码审查。"
            return f"查询过程中发生错误: {error_message}"
    
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