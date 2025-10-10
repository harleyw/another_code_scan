<template>
  <div class="repo-chat-container">
    <div class="header">
      <h1>{{ owner }} / {{ repo }} - RAG 问答系统</h1>
      <button @click="goBack" class="back-button">返回首页</button>
    </div>
    
    <!-- RAG 建立中动画 -->
    <div v-if="isBuildingRAG" class="building-rag-overlay">
      <div class="building-rag-content">
        <div class="spinner"></div>
        <p>RAG 系统正在建立中，请稍候...</p>
      </div>
    </div>
    
    <div class="chat-container">
      <div class="chat-history">
        <div v-for="message in messages" :key="message.id" class="message" :class="{ 'user-message': message.from === 'user', 'bot-message': message.from === 'bot' }">
          <div class="message-content">{{ message.content }}</div>
        </div>
      </div>
      
      <div class="input-container">
        <input
          v-model="inputMessage"
          @keyup.enter="sendMessage"
          placeholder="请输入 PR 地址或提问..."
          class="input-field"
          :disabled="isSending"
        />
        <button @click="sendMessage" :disabled="isSending || !inputMessage.trim()" class="send-button">
          {{ isSending ? '发送中...' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const owner = route.params.owner
const repo = route.params.repo

const messages = ref([])
const inputMessage = ref('')
const isSending = ref(false)
const isBuildingRAG = ref(false)

// 检查 RAG 系统状态
const checkRAGStatus = async () => {
  try {
    const response = await axios.get(`/api/review/${owner}/${repo}`)
    const data = response.data
    
    // 如果 RAG 正在建立，显示动画
    if (!data.vectorstore_initialized && data.has_excel_file) {
      isBuildingRAG.value = true
      
      // 轮询检查 RAG 是否建立完成
      const pollInterval = setInterval(async () => {
        try {
          const pollResponse = await axios.get(`/api/review/${owner}/${repo}`)
          if (pollResponse.data.vectorstore_initialized) {
            isBuildingRAG.value = false
            clearInterval(pollInterval)
          }
        } catch (error) {
          console.error('轮询 RAG 状态失败:', error)
          clearInterval(pollInterval)
        }
      }, 3000)
    }
  } catch (error) {
    console.error('检查 RAG 状态失败:', error)
    // 如果系统中没有对应 repo 的 RAG，发送服务请求
    await initRepoService()
  }
}

// 初始化仓库服务
const initRepoService = async () => {
  try {
    isBuildingRAG.value = true
    await axios.post('/api/collect_prs', { owner, repo })
    
    // 轮询检查服务是否初始化完成
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`/api/review/${owner}/${repo}`)
        if (response.data.vectorstore_initialized) {
          isBuildingRAG.value = false
          clearInterval(pollInterval)
        }
      } catch (error) {
        console.error('轮询服务初始化状态失败:', error)
        clearInterval(pollInterval)
      }
    }, 5000)
  } catch (error) {
    console.error('初始化仓库服务失败:', error)
    isBuildingRAG.value = false
    messages.value.push({
      id: Date.now(),
      from: 'bot',
      content: '初始化 RAG 系统失败，请稍后再试。'
    })
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isSending.value) return
  
  const userMessage = inputMessage.value.trim()
  messages.value.push({
    id: Date.now(),
    from: 'user',
    content: userMessage
  })
  
  inputMessage.value = ''
  isSending.value = true
  
  try {
    // 检查是否是 PR 地址
    const isPrUrl = checkIfPrUrl(userMessage)
    
    let response
    if (isPrUrl) {
      // 发送 PR 评审请求
      response = await axios.post('/api/review_pr', {
        owner,
        repo,
        pr_url: userMessage
      })
    } else {
      // 发送通用问题请求
      response = await axios.post('/api/review_pr', {
        owner,
        repo,
        question: userMessage
      })
    }
    
    messages.value.push({
      id: Date.now() + 1,
      from: 'bot',
      content: response.data.answer || '没有获取到回答，请重试。'
    })
  } catch (error) {
    console.error('发送请求失败:', error)
    messages.value.push({
      id: Date.now() + 1,
      from: 'bot',
      content: '请求失败，请稍后再试。'
    })
  } finally {
    isSending.value = false
  }
}

// 检查是否是 PR 地址
const checkIfPrUrl = (text) => {
  const prUrlRegex = /github\.com\/(\w+)\/(\w+)\/pull\/(\d+)/i
  return prUrlRegex.test(text)
}

// 返回首页
const goBack = () => {
  router.push('/')
}

// 页面加载时执行
onMounted(() => {
  checkRAGStatus()
})
</script>

<style scoped>
.repo-chat-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  color: #333;
  font-size: 24px;
  margin: 0;
}

.back-button {
  background-color: #666;
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.back-button:hover {
  background-color: #555;
}

.building-rag-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.building-rag-content {
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.chat-history {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f9f9f9;
}

.message {
  margin-bottom: 15px;
}

.user-message {
  text-align: right;
}

.bot-message {
  text-align: left;
}

.message-content {
  display: inline-block;
  padding: 10px 15px;
  border-radius: 18px;
  max-width: 70%;
}

.user-message .message-content {
  background-color: #42b983;
  color: white;
}

.bot-message .message-content {
  background-color: #e9e9e9;
  color: #333;
}

.input-container {
  display: flex;
  padding: 15px;
  border-top: 1px solid #ddd;
  background-color: white;
}

.input-field {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px 0 0 4px;
  font-size: 14px;
}

.send-button {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.send-button:hover:not(:disabled) {
  background-color: #3aa876;
}

.send-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>