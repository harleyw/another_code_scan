# PR 审查系统

基于 LangGraph 和 RAG 技术的智能 PR 审查和问答系统，帮助开发者更高效地分析和审查 GitHub Pull Request质量。

## 🚀 项目概述

本系统通过以下核心功能帮助团队提升代码审查效率：
- 自动收集 GitHub 仓库的所有已合并 PR 并生成 Excel 数据文件
- 基于 RAG (Retrieval-Augmented Generation) 技术构建知识库
- 提供智能问答功能，快速查询 PR 相关信息
- 支持多仓库管理和数据持久化

## 🛠 技术栈

- **后端框架**：FastAPI + Uvicorn
- **RAG 技术**：LangChain, LangGraph, LangChain-OpenAI
- **向量存储**：ChromaDB
- **嵌入模型**：DashScope
- **数据处理**：OpenPyXL, Pandas
- **API 调用**：Requests
- **前端**：Vue.js (位于 frontend 目录)

## 📋 系统架构

```
├── backend_app.py                 # 主应用入口
├── services/              # 核心服务模块
│   ├── pr_collector/      # PR 收集服务
│   ├── rag_service/       # RAG 问答服务
│   └── repo_manager/      # 仓库管理服务
├── libs/                  # 工具库
│   ├── pr_helper/         # PR 处理工具
│   └── rag_base/          # RAG 基础组件
├── util/                  # 通用工具
├── cfg/                   # 配置文件目录
└── frontend/              # 前端代码
```

## ⚙️ 配置说明

### 配置文件

所有配置键值均存储在统一的 JSON 文件中：`./cfg/config.json`

配置文件包含以下键：
- `github_token`: GitHub 个人访问令牌，用于访问仓库
- `dashscope_api_key`: DashScope 嵌入模型 API 密钥
- `openai_api_key`: OpenAI 服务 API 密钥（如需使用）

### 配置优先级

系统按以下优先级顺序读取配置：
1. 显式传递给函数/类的值
2. 配置文件中的值 (`./cfg/config.json`)
3. 环境变量（作为回退）

### 环境变量回退

如果在配置文件中未找到键，系统会尝试从以下环境变量读取：
- `GITHUB_TOKEN` 对应 GitHub token
- `DASHSCOPE_API_KEY` 对应 DashScope API key
- `OPENAI_API_KEY` 对应 OpenAI API key

这确保了与依赖环境变量的现有设置的向后兼容性。

## 🚀 部署指南

### 1. 克隆项目

```bash
git clone https://github.com/harleyw/another_code_scan.git
cd another_code_scan
```

### 2. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 如需前端开发，安装前端依赖
cd frontend
npm install
cd ..
```

### 3. 配置 API 密钥

创建或编辑配置文件 `./cfg/config.json`：

```json
{
  "github_token": "your_github_token_here",
  "dashscope_api_key": "your_dashscope_api_key_here",
  "openai_api_key": "your_openai_api_key_here"
}
```

### 4. 运行后端服务

```bash
# 直接运行
python backend_app.py

# 或使用 uvicorn 运行（支持更多配置）
uvicorn backend_app:app --host 0.0.0.0 --port 8000
```

### 5. 运行前端服务（可选）

```bash
cd frontend
npm run dev
```

## 🔧 开发指南

### 项目结构说明

- **backend_app.py**: 主应用入口，定义 API 路由和服务启动逻辑
- **services/**: 包含核心业务逻辑
- **libs/**: 提供底层功能支持和工具类
- **util/**: 通用工具函数和配置管理
- **cfg/**: 存放配置文件

### 主要 API 接口

1. **首页**
   - 路径: GET `/`
   - 描述: 系统首页

2. **收集 PR 数据**
   - 路径: POST `/api/collect_prs`
   - 参数: `owner` (仓库所有者), `repo` (仓库名称)
   - 描述: 异步收集指定仓库的所有已合并 PR 并生成 Excel 文件

3. **PR 审查**
   - 路径: POST `/api/review_pr`
   - 参数: `owner`, `repo`, `pr_id` (可选), `question` (可选)
   - 描述: 对指定仓库或特定 PR 进行智能审查

4. **获取仓库服务**
   - 路径: GET `/api/review/{owner}/{repo}`
   - 描述: 获取或创建指定仓库的审查服务实例

## 📊 使用流程

1. **收集 PR 数据**：调用 `/api/collect_prs` 接口，提供仓库所有者和仓库名称
2. **等待数据处理**：系统会异步处理 PR 数据并生成 Excel 文件
3. **查询审查服务**：调用 `/api/review/{owner}/{repo}` 检查服务初始化状态
4. **进行 PR 审查**：调用 `/api/review_pr` 接口进行智能问答和审查

## 📝 注意事项

- 确保配置文件中的 API 密钥具有足够的权限
- 首次运行时，系统可能需要一些时间来收集数据和构建向量存储
- PR 数据将保存在项目目录下的 `{owner}/{repo}` 文件夹中
- 如需自定义端口或主机，请修改 `backend_app.py` 中的 `uvicorn.run` 参数或使用命令行参数

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进此项目。在提交代码前，请确保：
- 代码风格与现有代码保持一致
- 添加必要的注释和文档
- 测试新功能以确保兼容性

## 📄 许可证

本项目使用 [BSD 3-clause 许可证](LICENSE)