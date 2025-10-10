import os
from typing import Dict
from util.config_manager import ConfigManager
from langchain_community.embeddings import DashScopeEmbeddings
from libs.rag_base.knowledge_base.build_rag_base import load_excel_pr_data
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# 单例服务管理器，用于缓存不同repo的服务实例
class RepoServiceManager:
    _instance = None
    _repo_services: Dict[str, Dict] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RepoServiceManager, cls).__new__(cls)
        return cls._instance
    
    def get_service(self, owner: str, repo: str) -> Dict:
        """获取指定owner/repo的服务实例"""
        key = f"{owner}/{repo}"
        if key not in self._repo_services:
            # 创建新的服务实例
            self._repo_services[key] = self._create_service(owner, repo)
        return self._repo_services[key]
    
    def _create_service(self, owner: str, repo: str) -> Dict:
        """创建新的服务实例"""
        print(f"创建新的服务实例: {owner}/{repo}")
        
        # 初始化配置管理器（使用自动计算的默认路径）和获取DashScope API密钥
        config_manager = ConfigManager()
        dashscope_api_key = config_manager.get_dashscope_api_key()
        
        if not dashscope_api_key:
            raise ValueError("DashScope API key not found. Please set it in the config file or as an environment variable.")
        
        # 创建嵌入模型
        embd = DashScopeEmbeddings(model="text-embedding-v4", dashscope_api_key=dashscope_api_key)
        
        # 获取Excel文件路径 - 使用当前目录下的owner/repo结构
        excel_file_path = f"./{owner}/{repo}/all_merged_prs.xlsx"
        
        # 创建服务实例字典
        service = {
            "owner": owner,
            "repo": repo,
            "vectorstore": None,
            "embedding_model": embd,
            "excel_file_path": excel_file_path,
            "initialized": False
        }
        
        return service
    
    def update_service_vectorstore(self, owner: str, repo: str):
        """更新服务的vectorstore"""
        key = f"{owner}/{repo}"
        if key in self._repo_services:
            service = self._repo_services[key]
            self._build_vectorstore(service)
    
    def _build_vectorstore(self, service: Dict):
        """从Excel文件构建vectorstore"""
        excel_file_path = service["excel_file_path"]
        
        # 检查Excel文件是否存在
        if not os.path.exists(excel_file_path):
            print(f"Excel文件不存在: {excel_file_path}")
            service["initialized"] = False
            return
        
        try:
            # 加载PR数据
            pr_docs = load_excel_pr_data(excel_file_path)
            
            if not pr_docs:
                print("没有加载到PR数据")
                service["initialized"] = False
                return
            
            # 将数据转换为LangChain Document对象
            documents = [Document(page_content=doc['page_content'], metadata=doc['metadata']) for doc in pr_docs]
            
            # 分割文档
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, 
                chunk_overlap=200
            )
            doc_splits = text_splitter.split_documents(documents)
            
            # 创建vectorstore
            vectorstore = Chroma.from_documents(
                documents=doc_splits,
                collection_name=f"rag-chroma-{service['owner']}-{service['repo']}",
                embedding=service["embedding_model"],
            )
            
            service["vectorstore"] = vectorstore
            service["initialized"] = True
            print(f"成功为 {service['owner']}/{service['repo']} 构建vectorstore")
        except Exception as e:
            print(f"构建vectorstore时出错: {str(e)}")
            service["initialized"] = False

# 初始化服务管理器
global repo_service_manager
repo_service_manager = RepoServiceManager()