from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Body, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import asyncio
import logging
import time
from typing import Dict, Optional, List
from pprint import pprint

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("PR_REVIEW_APP")

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 注意：这行代码暂时保留，因为项目中部分文件使用了相对路径引用
# 例如services/pr_collector/pr_collector.py中使用了../../cfg/config.json

# 导入服务模块
from services.pr_collector.pr_collector import collect_merged_prs_task
from services.rag_service.rag_service import review_pr
from services.repo_manager.repo_manager import repo_service_manager
from util.config_manager import ConfigManager

# 初始化配置管理器
config_manager = ConfigManager()

# 检查未处理PR文件是否有内容
def has_unhandled_prs(owner: str, repo: str) -> bool:
    """检查指定仓库的未处理PR文件是否包含PR号码"""
    try:
        data_dir = config_manager.get_pr_review_data_dir()
        unhandled_prs_file = os.path.join(data_dir, owner, repo, "all_unhandled_prs_merged.txt")
        
        # 检查文件是否存在
        if not os.path.exists(unhandled_prs_file):
            return False
        
        # 检查文件是否有内容
        with open(unhandled_prs_file, 'r') as f:
            content = f.read().strip()
            # 文件不为空且包含数字（PR号码）则返回True
            return bool(content) and any(char.isdigit() for char in content)
    except Exception as e:
        logger.error(f"检查未处理PR文件失败: {str(e)}")
        return False

# 确定PR数据状态
def determine_pr_data_status(owner: str, repo: str, has_excel: bool, is_collecting: bool) -> str:
    """确定PR数据状态的可复用函数"""
    if not has_excel:
        return "historical_pr_uninitialized"
    elif is_collecting:
        # 检查是否有未处理的PR，用于区分是初始收集还是更新
        if has_unhandled_prs(owner, repo):
            return "historical_pr_updating"
        else:
            return "historical_pr_collecting"
    elif has_unhandled_prs(owner, repo):
        # 有Excel文件但有未处理的PR且没有活跃的收集任务
        return "historical_pr_outofdate"
    else:
        return "historical_pr_ready"

# 确定vectorstore状态
def determine_vectorstore_status(initialized: bool, is_vectorstore_building: bool, owner: str, repo: str) -> str:
    """确定vectorstore状态的可复用函数"""
    if not initialized and not is_vectorstore_building:
        return "rag_uninitialized"
    elif is_vectorstore_building:
        if has_unhandled_prs(owner, repo):
            return "rag_updating"
        else:
            return "rag_initializing"
    elif has_unhandled_prs(owner, repo):
        return "rag_outofdate"
    else:
        return "rag_ready"

# 创建PR收集任务的信号量，用于控制并发数
max_concurrent_pr_collection = config_manager.get_max_concurrent_pr_collection()
pr_collection_semaphore = asyncio.Semaphore(max_concurrent_pr_collection)

logger.info(f"PR收集任务最大并发数设置为: {max_concurrent_pr_collection}")

# 用于跟踪PR收集任务状态的字典
active_pr_collection_tasks = {}

# 用于跟踪vectorstore构建任务状态的字典
active_vectorstore_build_tasks = {}

# 创建vectorstore构建任务的信号量，用于控制并发数
max_concurrent_vectorstore_build = config_manager.get_max_concurrent_pr_collection()
vectorstore_build_semaphore = asyncio.Semaphore(max_concurrent_vectorstore_build)

logger.info(f"vectorstore构建任务最大并发数设置为: {max_concurrent_vectorstore_build}")


# 初始化 FastAPI 应用
app = FastAPI(title="PR审查系统", description="基于 LangGraph 的PR审查和问答系统")

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logger.info("访问根路径")
    return templates.TemplateResponse("index.html", {"request": request})

# 创建异步包装函数，使用信号量控制并发
async def run_collect_prs_with_semaphore(owner: str, repo: str):
    """使用信号量控制并发的PR收集任务包装函数"""
    task_key = f"{owner}/{repo}"
    
    # 获取当前活跃的任务数量（近似值）
    active_tasks = sum(1 for task in asyncio.all_tasks() if task.get_name().startswith("collect_prs") and not task.done())
    logger.info(f"当前活跃的PR收集任务数: {active_tasks}/{max_concurrent_pr_collection}")
    
    if active_tasks >= max_concurrent_pr_collection:
        logger.info(f"PR收集任务达到最大并发数 {max_concurrent_pr_collection}，{owner}/{repo} 任务将等待空闲槽位")
    
    # 记录任务状态为运行中
    active_pr_collection_tasks[task_key] = True
    
    # 使用信号量控制并发
    async with pr_collection_semaphore:
        try:
            logger.info(f"开始执行PR收集任务: {owner}/{repo}")
            # 调用实际的PR收集函数
            await asyncio.to_thread(collect_merged_prs_task, owner, repo)
            logger.info(f"PR收集任务完成: {owner}/{repo}")
        except Exception as e:
            logger.error(f"PR收集任务失败: {owner}/{repo}, 错误: {str(e)}")
        finally:
            # 任务完成后从活跃任务列表中移除
            if task_key in active_pr_collection_tasks:
                del active_pr_collection_tasks[task_key]
            # 任务完成后记录释放了一个并发槽位
            logger.info(f"PR收集任务槽位释放: {owner}/{repo}")

# 创建异步包装函数，使用信号量控制vectorstore构建并发
async def run_vectorstore_build_with_semaphore(owner: str, repo: str):
    """使用信号量控制并发的vectorstore构建任务包装函数"""
    task_key = f"{owner}/{repo}"
    
    # 获取当前活跃的任务数量（近似值）
    active_tasks = sum(1 for task in asyncio.all_tasks() if task.get_name().startswith("vectorstore_build") and not task.done())
    logger.info(f"当前活跃的vectorstore构建任务数: {active_tasks}/{max_concurrent_vectorstore_build}")
    
    if active_tasks >= max_concurrent_vectorstore_build:
        logger.info(f"vectorstore构建任务达到最大并发数 {max_concurrent_vectorstore_build}，{owner}/{repo} 任务将等待空闲槽位")
    
    # 记录任务状态为运行中
    active_vectorstore_build_tasks[task_key] = True
    
    # 使用信号量控制并发
    async with vectorstore_build_semaphore:
        try:
            logger.info(f"开始执行vectorstore构建任务: {owner}/{repo}")
            # 调用实际的vectorstore构建函数
            await asyncio.to_thread(repo_service_manager.update_service_vectorstore, owner, repo)
            logger.info(f"vectorstore构建任务完成: {owner}/{repo}")
        except Exception as e:
            logger.error(f"vectorstore构建任务失败: {owner}/{repo}, 错误: {str(e)}")
        finally:
            # 任务完成后从活跃任务列表中移除
            if task_key in active_vectorstore_build_tasks:
                del active_vectorstore_build_tasks[task_key]
            # 任务完成后记录释放了一个并发槽位
            logger.info(f"vectorstore构建任务槽位释放: {owner}/{repo}")

# 服务1：收集一个repo的所有merged PR并生成excel文件
@app.post("/api/collect_history_prs")
async def collect_history_prs(background_tasks: BackgroundTasks, owner: str = Body(...), repo: str = Body(...)):
    """收集一个repo的所有merged PR的历史数据服务接口"""
    logger.info(f"收到收集历史PR请求: owner={owner}, repo={repo}")
    
    if not owner or not repo:
        logger.warning("缺少必要参数: owner或repo为空")
        raise HTTPException(status_code=400, detail="Owner and repo parameters are required")
    
    try:
        # 创建一个命名任务，便于跟踪
        task_name = f"collect_history_prs_{owner}_{repo}_{int(time.time())}"
        task = asyncio.create_task(run_collect_prs_with_semaphore(owner, repo), name=task_name)
        logger.info(f"已创建并发控制的任务: {task_name}")
        
        return JSONResponse(content={
            "message": f"开始收集 {owner}/{repo} 的所有merged PR历史数据，当前最大并发数: {max_concurrent_pr_collection}，请稍后查看 {owner}/{repo} 目录下的Excel文件"
        })
    except Exception as e:
        logger.error(f"添加收集历史PR任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")

# 服务2：PR review功能
@app.post("/api/review_pr")
async def api_review_pr(owner: str = Body(...), repo: str = Body(...), pr_id: str = Body(None), question: str = Body(None)):
    """PR review服务接口"""
    logger.info(f"收到PR审查请求: owner={owner}, repo={repo}, pr_id={pr_id}, question={question}")
    
    try:
        result = await review_pr(owner, repo, pr_id, question)
        logger.info(f"PR审查请求处理完成: owner={owner}, repo={repo}")
        return result
    except Exception as e:
        logger.error(f"PR审查请求处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")

# 服务4：获取所有仓库的服务数据
@app.get("/api/review/all")
async def get_all_review_services():
    """获取所有已注册仓库的服务数据接口"""
    logger.info("收到获取所有仓库服务数据请求")
    
    try:
        # 获取所有已注册的服务
        all_services = repo_service_manager.get_all_services()
        logger.info(f"成功获取所有仓库服务数据，共 {len(all_services)} 个仓库")
        
        # 构建返回数据
        result = []
        for service_id, service_info in all_services.items():
            owner, repo = service_id.split('/')
            task_key = service_id
            has_excel = os.path.exists(service_info["excel_file_path"])
            is_collecting = task_key in active_pr_collection_tasks
            is_vectorstore_building = task_key in active_vectorstore_build_tasks
            
            # 使用可复用函数确定PR数据状态
            pr_data_status = determine_pr_data_status(owner, repo, has_excel, is_collecting)
            
            # 使用可复用函数确定vectorstore状态
            vectorstore_status = determine_vectorstore_status(
                service_info["initialized"], 
                is_vectorstore_building, 
                owner, 
                repo
            )
            
            repo_data = {
                "service_url": f"/api/review/{owner}/{repo}",
                "owner": owner,
                "repo": repo,
                "has_excel_file": has_excel,
                "vectorstore_initialized": service_info["initialized"],
                "excel_file_path": service_info["excel_file_path"],
                "pr_data_status": pr_data_status,
                "vectorstore_status": vectorstore_status,
                "is_collecting": is_collecting,
                "is_vectorstore_building": is_vectorstore_building
            }
            result.append(repo_data)
        
        return JSONResponse(content={
            "repositories": result,
            "total_count": len(result)
        })
    except Exception as e:
        logger.error(f"获取所有仓库服务数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")

# 服务3：单例服务+动态路由参数
@app.get("/api/review/{owner}/{repo}")
async def get_review_service(owner: str, repo: str):
    """获取或创建指定仓库的review服务接口"""
    logger.info(f"收到获取服务请求: owner={owner}, repo={repo}")
    
    try:
        # 获取服务实例（如果不存在则创建）
        service = repo_service_manager.get_service(owner, repo)
        logger.debug(f"获取服务实例成功: service_id={id(service)}")
        
        # 检查是否存在Excel文件
        has_excel = os.path.exists(service["excel_file_path"])
        logger.debug(f"Excel文件检查结果: {has_excel}, 路径: {service['excel_file_path']}")
        
        # 如果有Excel文件但服务未初始化，异步构建vectorstore
        task_key = f"{owner}/{repo}"
        is_vectorstore_building = task_key in active_vectorstore_build_tasks
        
        if has_excel and not service["initialized"] and not is_vectorstore_building:
            logger.info(f"发现Excel文件但服务未初始化，开始异步更新vectorstore: {owner}/{repo}")
            # 创建一个命名任务，便于跟踪
            build_task_name = f"vectorstore_build_{owner}_{repo}_{int(time.time())}"
            build_task = asyncio.create_task(run_vectorstore_build_with_semaphore(owner, repo), name=build_task_name)
            logger.info(f"已创建并发控制的vectorstore构建任务: {build_task_name}")
            
        # 检查是否有活跃的PR收集任务
        is_collecting = task_key in active_pr_collection_tasks
        
        # 使用可复用函数确定PR数据状态
        pr_data_status = determine_pr_data_status(owner, repo, has_excel, is_collecting)
            
        # 使用可复用函数确定vectorstore状态
        vectorstore_status = determine_vectorstore_status(
            service["initialized"], 
            is_vectorstore_building, 
            owner, 
            repo
        )
            
        response_data = {
            "service_url": f"/api/review/{owner}/{repo}",
            "owner": owner,
            "repo": repo,
            "has_excel_file": has_excel,
            "vectorstore_initialized": service["initialized"],
            "excel_file_path": service["excel_file_path"],
            "pr_data_status": pr_data_status,
            "vectorstore_status": vectorstore_status,
            "is_collecting": is_collecting,
            "is_vectorstore_building": is_vectorstore_building,
            "message": "服务已准备就绪" if service["initialized"] else "服务已创建，请先导入PR数据并构建vectorstore"
        }
        
        logger.info(f"服务请求处理完成: owner={owner}, repo={repo}, 状态={response_data['message']}")
        return JSONResponse(content=response_data)
    except Exception as e:
        logger.error(f"获取服务请求处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")

# 创建一个函数来异步更新所有已注册仓库的PR数据
def update_all_repos_pr_data():
    """更新所有已注册仓库的PR数据"""
    try:
        # 获取所有已注册的服务
        all_services = repo_service_manager.get_all_services()
        logger.info(f"开始更新所有已注册仓库的PR数据，共 {len(all_services)} 个仓库")
        
        if not all_services:
            logger.info("没有已注册的仓库服务，跳过PR数据更新")
            return
        
        # 创建一个事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 创建任务列表
        tasks = []
        for service_id in all_services.keys():
            owner, repo = service_id.split('/')
            task = loop.create_task(run_collect_prs_with_semaphore(owner, repo))
            tasks.append(task)
            logger.info(f"已创建PR数据更新任务: {owner}/{repo}")
        
        # 运行所有任务
        if tasks:
            logger.info(f"开始执行 {len(tasks)} 个PR数据更新任务，最大并发数: {max_concurrent_pr_collection}")
            loop.run_until_complete(asyncio.gather(*tasks))
        
        # 关闭事件循环
        loop.close()
        logger.info("所有仓库PR数据更新任务执行完成")
    except Exception as e:
        logger.error(f"更新所有仓库PR数据时出错: {str(e)}")

# 创建一个函数来初始化所有已注册仓库的vectorstore
def initialize_all_vectorstores():
    """在服务器启动前，检查并初始化所有已注册仓库的vectorstore"""
    try:
        # 获取所有已注册的服务
        all_services = repo_service_manager.get_all_services()
        logger.info(f"开始检查所有已注册仓库的vectorstore，共 {len(all_services)} 个仓库")
        
        if not all_services:
            logger.info("没有已注册的仓库服务，跳过vectorstore初始化")
            return
        
        # 创建一个事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 创建任务列表
        tasks = []
        for service_id, service_info in all_services.items():
            owner, repo = service_id.split('/')
            # 检查vectorstore是否已初始化
            if not service_info["initialized"]:
                # 检查是否存在Excel文件
                if os.path.exists(service_info["excel_file_path"]):
                    logger.info(f"发现未初始化的vectorstore，开始构建: {owner}/{repo}")
                    task = loop.create_task(run_vectorstore_build_with_semaphore(owner, repo))
                    tasks.append(task)
                else:
                    logger.info(f"仓库 {owner}/{repo} 缺少Excel文件，跳过vectorstore构建")
            else:
                logger.info(f"仓库 {owner}/{repo} 的vectorstore已初始化")
        
        # 运行所有任务
        if tasks:
            logger.info(f"开始执行 {len(tasks)} 个vectorstore初始化任务，最大并发数: {max_concurrent_vectorstore_build}")
            loop.run_until_complete(asyncio.gather(*tasks))
        
        # 关闭事件循环
        loop.close()
        logger.info("所有仓库vectorstore初始化任务执行完成")
    except Exception as e:
        logger.error(f"初始化所有仓库vectorstore时出错: {str(e)}")

if __name__ == "__main__":
    logger.info("PR审查系统启动中...")
    logger.info(f"当前工作目录: {os.getcwd()}")
    logger.info(f"项目根目录: {os.path.dirname(os.path.abspath(__file__))}")
    
    # 扫描PR数据目录，检查是否有可用的repo数据
    try:
        from util.config_manager import ConfigManager
        config_manager = ConfigManager()
        pr_review_data_dir = config_manager.get_pr_review_data_dir()
        
        logger.info(f"配置的PR数据目录: {pr_review_data_dir}")
        
        # 如果目录存在，扫描其中的仓库
        if os.path.exists(pr_review_data_dir):
            logger.info(f"开始扫描PR数据目录: {pr_review_data_dir}")
            
            # 遍历所有者目录
            for owner in os.listdir(pr_review_data_dir):
                owner_path = os.path.join(pr_review_data_dir, owner)
                if os.path.isdir(owner_path):
                    # 遍历所有者下的仓库目录
                    for repo in os.listdir(owner_path):
                        repo_path = os.path.join(owner_path, repo)
                        if os.path.isdir(repo_path):
                            # 检查是否存在all_merged_prs.xlsx文件
                            excel_file_path = os.path.join(repo_path, "all_merged_prs.xlsx")
                            if os.path.exists(excel_file_path):
                                logger.info(f"发现仓库数据: {owner}/{repo}，Excel文件: {excel_file_path}")
                                # 注册服务实例，但不立即构建vectorstore（按需构建）
                                try:
                                    repo_service_manager.get_service(owner, repo)
                                    logger.info(f"已注册仓库服务: {owner}/{repo}")
                                except Exception as e:
                                    logger.error(f"注册仓库服务失败 {owner}/{repo}: {str(e)}")
            
            logger.info("PR数据目录扫描完成")
        else:
            logger.info(f"PR数据目录不存在: {pr_review_data_dir}，系统将以空白状态启动")
            # 创建目录以便后续使用
            os.makedirs(pr_review_data_dir, exist_ok=True)
            logger.info(f"已创建PR数据目录: {pr_review_data_dir}")
            
    except Exception as e:
        logger.error(f"扫描PR数据目录时出错: {str(e)}")
        # 继续启动服务，不因目录扫描错误而中断
    
    # 在服务器启动前，更新所有已注册仓库的PR数据
    try:
        # 检查配置中是否启用了自动更新PR数据
        auto_update_pr_data = config_manager.get_config_value('auto_update_pr_data', False)
        if auto_update_pr_data:
            logger.info("配置启用了自动更新PR数据，开始更新所有已注册仓库的PR数据")
            update_all_repos_pr_data()
        else:
            logger.info("配置未启用自动更新PR数据，跳过PR数据更新")
    except Exception as e:
        logger.error(f"执行PR数据自动更新时出错: {str(e)}")
        # 继续启动服务，不因更新错误而中断
    
    # 在服务器启动前，初始化所有已注册仓库的vectorstore
    try:
        logger.info("在服务器启动前，开始初始化所有已注册仓库的vectorstore")
        initialize_all_vectorstores()
    except Exception as e:
        logger.error(f"执行vectorstore初始化时出错: {str(e)}")
        # 继续启动服务，不因初始化错误而中断
    
    try:
        logger.info("启动FastAPI服务器，监听地址: 0.0.0.0:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.critical(f"服务器启动失败: {str(e)}")
        raise