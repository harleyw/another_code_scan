from fastapi import FastAPI, Request, Form
from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import sys
import asyncio
from typing import Dict, Optional, List
from pprint import pprint

# 添加项目根目录和相关路径
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, 'libs', 'pr_helper'))
sys.path.append(os.path.join(base_dir, 'libs', 'rag_base'))
sys.path.append(os.path.join(base_dir, 'libs', 'rag_base', 'graphs'))

# 导入现有的问答系统组件
import setup
from libs.rag_base.graphs.graph_build import app as graph_app

# 导入PR相关工具
from libs.pr_helper.export_all_prs_to_excel import GitHubAllPRsExporter
from util.config_manager import ConfigManager

# 导入RAG相关组件
from libs.rag_base.knowledge_base.build_rag_base import load_excel_pr_data
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

# 初始化 FastAPI 应用
app = FastAPI(title="PR审查系统", description="基于 LangGraph 的PR审查和问答系统")

templates = Jinja2Templates(directory="templates")

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
repo_service_manager = RepoServiceManager()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 服务1：收集一个repo的所有merged PR并生成excel文件
def collect_merged_prs_task(owner: str, repo: str):
    """异步任务：收集指定仓库的所有merged PR并生成excel文件"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager("../../cfg/config.json")
        token = config_manager.get_github_token()
        
        # 创建输出目录 - 使用当前目录下的owner/repo结构
        output_dir = f"./{owner}/{repo}"
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化PR导出器
        exporter = GitHubAllPRsExporter(token)
        
        # 导出所有merged PR到excel
        output_file = f"{output_dir}/all_merged_prs.xlsx"
        exporter.export_all_prs_to_excel(owner, repo, output_file, state="merged")
        
        # 导出完成后，更新对应的服务实例的vectorstore
        repo_service_manager.update_service_vectorstore(owner, repo)
    except Exception as e:
        print(f"收集PR时出错: {str(e)}")

@app.post("/api/collect_prs")
async def collect_prs(background_tasks: BackgroundTasks, owner: str, repo: str):
    """收集一个repo的所有merged PR的服务接口"""
    if not owner or not repo:
        raise HTTPException(status_code=400, detail="Owner and repo parameters are required")
    
    # 创建异步任务
    background_tasks.add_task(collect_merged_prs_task, owner, repo)
    
    return JSONResponse(content={
        "message": f"开始收集 {owner}/{repo} 的所有merged PR，请稍后查看 {owner}/{repo} 目录下的Excel文件"
    })

# 服务2：PR review功能
@app.post("/api/review_pr")
async def review_pr(owner: str, repo: str, pr_id: str = None, question: str = None):
    """PR review服务接口"""
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
            if not os.path.exists(service["excel_file_path"]):
                raise HTTPException(status_code=404, detail=f"未找到 {owner}/{repo} 的PR数据文件，请先调用收集PR的接口")
            else:
                raise HTTPException(status_code=500, detail=f"构建vectorstore失败，请检查日志")
    
    # 构建查询
    if pr_id:
        # 如果指定了PR ID，构建关于该PR的问题
        query = f"请审查PR {pr_id}，并给出评论"
    elif question:
        # 如果提供了自定义问题，使用该问题
        query = question
    else:
        raise HTTPException(status_code=400, detail="Either pr_id or question parameter is required")
    
    try:
        # 使用LangGraph回答问题
        inputs = {"question": query}
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
        
        return JSONResponse(content={"answer": generation})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")

# 服务3：单例服务+动态路由参数
@app.get("/api/review/{owner}/{repo}")
async def get_review_service(owner: str, repo: str):
    """获取或创建指定仓库的review服务接口"""
    # 获取服务实例（如果不存在则创建）
    service = repo_service_manager.get_service(owner, repo)
    
    # 检查是否存在Excel文件
    has_excel = os.path.exists(service["excel_file_path"])
    
    # 如果有Excel文件但服务未初始化，尝试构建vectorstore
    if has_excel and not service["initialized"]:
        repo_service_manager.update_service_vectorstore(owner, repo)
        service = repo_service_manager.get_service(owner, repo)
    
    return JSONResponse(content={
        "service_url": f"/api/review/{owner}/{repo}",
        "owner": owner,
        "repo": repo,
        "has_excel_file": has_excel,
        "vectorstore_initialized": service["initialized"],
        "excel_file_path": service["excel_file_path"],
        "message": "服务已准备就绪" if service["initialized"] else "服务已创建，请先导入PR数据并构建vectorstore"
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)