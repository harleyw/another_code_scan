# PR Review System

An intelligent PR review and Q&A system based on LangGraph and RAG technologies, helping developers analyze and understand GitHub Pull Request history more efficiently.

## 🚀 Project Overview

This system helps teams improve code review efficiency through the following core functions:
- Automatically collect all merged PRs from GitHub repositories and generate Excel data files
- Build knowledge base based on RAG (Retrieval-Augmented Generation) technology
- Provide intelligent Q&A functionality for quick查询 of PR-related information
- Support multi-repository management and data persistence

## 🛠 Technology Stack

- **Backend Framework**: FastAPI + Uvicorn
- **RAG Technology**: LangChain, LangGraph, LangChain-OpenAI
- **Vector Storage**: ChromaDB
- **Embedding Model**: DashScope
- **Data Processing**: OpenPyXL, Pandas
- **API Calls**: Requests
- **Frontend**: Vue.js (located in the frontend directory)

## 📋 System Architecture

```
├── backend_app.py                 # Main application entry
├── services/              # Core service modules
│   ├── pr_collector/      # PR collection service
│   ├── rag_service/       # RAG Q&A service
│   └── repo_manager/      # Repository management service
├── libs/                  # Tool libraries
│   ├── pr_helper/         # PR processing tools
│   └── rag_base/          # RAG base components
├── util/                  # Common utilities
├── cfg/                   # Configuration files directory
└── frontend/              # Frontend code
```

## ⚙️ Configuration Instructions

### Configuration File

All configuration keys are stored in a single JSON file: `./cfg/config.json`

The configuration file contains the following keys:
- `github_token`: GitHub personal access token for accessing repositories
- `dashscope_api_key`: API key for DashScope embeddings
- `openai_api_key`: API key for OpenAI services (if used)

### Configuration Priority

The system reads configuration in the following priority order:
1. Values explicitly passed to functions/classes
2. Values from the configuration file (`./cfg/config.json`)
3. Environment variables (as fallback)

### Environment Variable Fallback

If a key is not found in the configuration file, the system will attempt to read it from the following environment variables:
- `GITHUB_TOKEN` for GitHub token
- `DASHSCOPE_API_KEY` for DashScope API key
- `OPENAI_API_KEY` for OpenAI API key

This ensures backward compatibility with existing setups that rely on environment variables.

## 🚀 Deployment Guide

### 1. Clone the Project

```bash
git clone https://github.com/harleyw/another_code_scan.git
cd another_code_scan
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# If frontend development is needed, install frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Configure API Keys

Create or edit the configuration file `./cfg/config.json`:

```json
{
  "github_token": "your_github_token_here",
  "dashscope_api_key": "your_dashscope_api_key_here",
  "openai_api_key": "your_openai_api_key_here"
}
```

### 4. Run the Backend Service

```bash
# Run directly
python backend_app.py

# Or run with uvicorn (supports more configurations)
uvicorn backend_app:app --host 0.0.0.0 --port 8000
```

### 5. Run the Frontend Service (Optional)

```bash
cd frontend
npm run dev
```

## 🔧 Development Guide

### Project Structure Description

- **backend_app.py**: Main application entry, defines API routes and service startup logic
- **services/**: Contains core business logic
- **libs/**: Provides underlying functional support and utility classes
- **util/**: Common utility functions and configuration management
- **cfg/**: Stores configuration files

### Main API Interfaces

1. **Home Page**
   - Path: GET `/`
   - Description: System home page

2. **Collect PR Data**
   - Path: POST `/api/collect_prs`
   - Parameters: `owner` (repository owner), `repo` (repository name)
   - Description: Asynchronously collect all merged PRs from the specified repository and generate Excel file

3. **PR Review**
   - Path: POST `/api/review_pr`
   - Parameters: `owner`, `repo`, `pr_id` (optional), `question` (optional)
   - Description: Conduct intelligent review for the specified repository or specific PR

4. **Get Repository Service**
   - Path: GET `/api/review/{owner}/{repo}`
   - Description: Get or create a review service instance for the specified repository

## 📊 Usage Flow

1. **Collect PR Data**: Call the `/api/collect_prs` endpoint, providing the repository owner and name
2. **Wait for Data Processing**: The system will asynchronously process PR data and generate an Excel file
3. **Query Review Service**: Call `/api/review/{owner}/{repo}` to check the service initialization status
4. **Conduct PR Review**: Call the `/api/review_pr` endpoint for intelligent Q&A and review

## 📝 Notes

- Ensure that the API keys in the configuration file have sufficient permissions
- When running for the first time, the system may need some time to collect data and build the vector store
- PR data will be saved in the `{owner}/{repo}` folder under the project directory
- To customize the port or host, modify the `uvicorn.run` parameters in `backend_app.py` or use command-line arguments

## 🤝 Contribution Guide

Contributions to improve this project are welcome through Issues and Pull Requests. Before submitting code, please ensure:
- Code style is consistent with existing code
- Necessary comments and documentation are added
- New features are tested to ensure compatibility

## 📄 License

This project is licensed under the [BSD 3-clause License](LICENSE)
