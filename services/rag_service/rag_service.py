from abc import ABC, abstractmethod
import os
from abc import ABC, abstractmethod
from typing import Optional
from fastapi import HTTPException
from services.repo_manager.repo_manager import repo_service_manager
from libs.rag.langgraph_wrapper import LangGraphWrapper

class RAGService(ABC):
    """RAG服务的抽象基类"""
    
    @abstractmethod
    async def answer_query(self, owner: str, repo: str, query: str) -> str:
        """回答关于特定仓库的问题"""
        pass

class DefaultRAGService(RAGService):
    """默认的RAG服务实现"""
    
    async def answer_query(self, owner: str, repo: str, query: str) -> str:
        """使用LangGraph回答问题"""
        
        # 获取服务实例
        service = repo_service_manager.get_service(owner, repo)
        
        # 检查服务是否已初始化
        if not service["initialized"] or not service["vectorstore"]:
            raise ValueError("服务尚未初始化，请先构建vectorstore")
        
        # 使用LangGraph回答问题
        langgraph_wrapper = LangGraphWrapper(service["vectorstore"])
        return await langgraph_wrapper.query(query)

# 默认的RAG服务实例
default_rag_service = DefaultRAGService()

async def review_pr(owner: str, repo: str, pr_id: str = None, question: str = None):
    """PR review服务接口的实现"""
    if not owner or not repo:
        raise HTTPException(status_code=400, detail="Owner and repo parameters are required")
    
    # 获取服务实例
    service = repo_service_manager.get_service(owner, repo)
    
    # 检查服务是否已初始化
    if not service["initialized"] or not service["vectorstore"]:
        # 如果服务未初始化，尝试从Excel文件构建vectorstore
        repo_service_manager.update_service_vectorstore(owner, repo)
        service = repo_service_manager.get_service(owner, repo)
        
        if not service["initialized"]:
            # 如果仍未初始化，可能是因为没有Excel文件或构建失败
            if not service["excel_file_path"] or not os.path.exists(service["excel_file_path"]):
                raise HTTPException(status_code=404, detail=f"未找到 {owner}/{repo} 的PR数据文件，请先调用收集PR的接口")
            else:
                raise HTTPException(status_code=500, detail=f"构建vectorstore失败，请检查日志")
    
    # 构建查询
    if pr_id:
        # 如果指定了PR ID，构建关于该PR的问题
        #query = f"请审查PR {pr_id}，并给出评论"
        query = pr_id
    elif question:
        # 如果提供了自定义问题，使用该问题
        query = question
    else:
        raise HTTPException(status_code=400, detail="Either pr_id or question parameter is required")
    
    try:
        # 使用RAG服务回答问题
        answer = await default_rag_service.answer_query(owner, repo, query)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")

import os