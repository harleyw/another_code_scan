<template>
  <div class="home-container">
    <h1>Github Repo PR评审系统</h1>
    <div class="repo-list">
      <!-- 这里会显示所有已配置的仓库 PR 评审模块 -->
      <!-- 目前暂时使用硬编码的示例 -->
      <div class="repo-card" v-for="repo in repos" :key="repo.id">
        <h2>{{ repo.owner }} / {{ repo.name }}</h2>
        <p v-html="repo.description"></p>
        <button @click="goToRepoChat(repo.owner, repo.name)">进入问答系统</button>
      </div>
      
      <!-- 如果没有仓库数据，显示空状态 -->
      <div v-if="repos.length === 0" class="empty-state">
        <p>暂无可用的仓库 RAG 模块</p>
        <p>请在浏览器地址栏直接输入 http://host_url/owner/repo 来访问特定仓库的问答系统</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const repos = ref([])

// 初始化时获取已有的仓库列表
const fetchRepos = async () => {
  try {
    // 调用后端 API 获取实际的仓库列表
    const response = await axios.get('/api/review/all')
    // 将后端返回的数据转换为前端需要的格式
    repos.value = response.data.repositories.map((repo, index) => ({
      id: index + 1,
      owner: repo.owner,
      name: repo.repo,
      description: `仓库状态: <br>历史PR数据：${
        repo.pr_data_status === 'historical_pr_ready' ? '已就绪' : '未就绪'
      } | 向量库: ${
        repo.vectorstore_status === 'rag_ready' ? '已就绪' : '未就绪'
      }`
    }))
  } catch (error) {
    console.error('获取仓库列表失败:', error)
    // 如果API调用失败，显示示例数据
    repos.value = [
      {
        id: 1,
        owner: 'example',
        name: 'repo1',
        description: '示例仓库 1'
      },
      {
        id: 2,
        owner: 'example',
        name: 'repo2',
        description: '示例仓库 2'
      }
    ]
  }
}

// 跳转到仓库问答页面
const goToRepoChat = (owner, repo) => {
  router.push({ name: 'repoRag', params: { owner, repo } })
}

// 页面加载时执行
fetchRepos()
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

.repo-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.repo-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background-color: #f9f9f9;
  transition: transform 0.2s, box-shadow 0.2s;
}

.repo-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.repo-card h2 {
  margin-top: 0;
  color: #42b983;
}

.repo-card p {
  color: #666;
  margin-bottom: 15px;
}

.repo-card button {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.repo-card button:hover {
  background-color: #3aa876;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 50px 20px;
  color: #666;
}
</style>