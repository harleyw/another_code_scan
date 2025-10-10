from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import sys
import asyncio
from typing import Dict, Optional, List
from pprint import pprint

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 注意：这行代码暂时保留，因为项目中部分文件使用了相对路径引用
# 例如services/pr_collector/pr_collector.py中使用了../../cfg/config.json

# 导入服务模块
from services.pr_collector.pr_collector import collect_prs_task
from services.rag_service.rag_service import review_pr
from services.repo_manager.repo_manager import repo_service_manager

# 初始化 FastAPI 应用
app = FastAPI(title="PR审查系统", description="基于 LangGraph 的PR审查和问答系统")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 服务1：收集一个repo的所有merged PR并生成excel文件
@app.post("/api/collect_prs")
async def collect_prs(background_tasks: BackgroundTasks, owner: str, repo: str):
    """收集一个repo的所有merged PR的服务接口"""
    if not owner or not repo:
        raise HTTPException(status_code=400, detail="Owner and repo parameters are required")
    
    # 创建异步任务
    background_tasks.add_task(collect_prs_task, owner, repo)
    
    return JSONResponse(content={
        "message": f"开始收集 {owner}/{repo} 的所有merged PR，请稍后查看 {owner}/{repo} 目录下的Excel文件"
    })

# 服务2：PR review功能
@app.post("/api/review_pr")
async def api_review_pr(owner: str, repo: str, pr_id: str = None, question: str = None):
    """PR review服务接口"""
    return await review_pr(owner, repo, pr_id, question)

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