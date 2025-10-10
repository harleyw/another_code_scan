<template>
  <div class="repo-rag-container">
    <header class="repo-header">
      <h1>仓库分析助手</h1>
      <div class="repo-info">
        <span class="owner-repo">{{ repoInfo.owner }} / {{ repoInfo.repo }}</span>
      </div>
    </header>

    <main class="main-content">
      <div class="pr-input-section">
        <label for="prUrl">PR 地址 (可选):</label>
        <input
          id="prUrl"
          v-model="prUrlInput"
          type="text"
          placeholder="https://github.com/owner/repo/pull/123"
          @input="updatePrUrl"
        />
        <button @click="collectPRs" :disabled="isLoading || !canCollectPRs">
          {{ isLoading ? '收集PR中...' : '收集PR数据' }}
        </button>
      </div>

      <div v-if="repoStatus" class="status-section">
        <div class="status-item">
          <span class="status-label">PR数据状态:</span>
          <span :class="['status-value', repoStatus.has_pr_data ? 'status-available' : 'status-unavailable']">
            {{ repoStatus.has_pr_data ? '可用' : '不可用' }}
          </span>
        </div>
        <div class="status-item">
          <span class="status-label">RAG服务状态:</span>
          <span :class="['status-value', repoStatus.initialized ? 'status-available' : 'status-unavailable']">
            {{ repoStatus.initialized ? '已初始化' : '未初始化' }}
          </span>
        </div>
      </div>

      <div class="chat-section">
        <div class="messages-container" ref="messagesContainer">
          <div v-if="isEmpty" class="empty-state">
            <p>请输入问题开始对话</p>
          </div>
          <div v-else v-for="message in messages" :key="message.id" :class="['message', message.type]">
            <div class="message-content">{{ message.content }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
          <div v-if="isLoading" class="loading-message">
            <div class="loading-spinner"></div>
            <span>思考中...</span>
          </div>
        </div>

        <div class="input-container">
          <textarea
            v-model="messageInput"
            placeholder="请输入您的问题..."
            @keydown.enter.prevent="sendMessage"
            :disabled="isLoading"
          ></textarea>
          <button @click="sendMessage" :disabled="isLoading || !messageInput.trim()">
            发送
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { useRoute } from 'vue-router';
import { useChatStore } from '../stores/chatStore';
import { storeToRefs } from 'pinia';
import { onMounted, ref, watch } from 'vue';

export default {
  name: 'RepoRag',
  setup() {
    const route = useRoute();
    const chatStore = useChatStore();
    const { messages, isLoading, error, repoInfo } = storeToRefs(chatStore);
    const { hasMessages, isEmpty } = chatStore;
    const messageInput = ref('');
    const prUrlInput = ref('');
    const repoStatus = ref(null);
    const messagesContainer = ref(null);

    // 初始化仓库信息
    const initializeRepoInfo = async () => {
      const { owner, repo } = route.params;
      chatStore.setRepoInfo(owner, repo);
      await checkRepoStatus();
    };

    // 检查仓库状态
    const checkRepoStatus = async () => {
      try {
        const status = await chatStore.checkRepoStatus();
        repoStatus.value = status;
        // 如果有PR URL，更新输入框
        if (status.pr_url) {
          prUrlInput.value = status.pr_url;
        }
      } catch (err) {
        console.error('获取仓库状态失败:', err);
      }
    };

    // 发送消息
    const sendMessage = async () => {
      if (!messageInput.value.trim()) return;
      await chatStore.sendMessage(messageInput.value.trim());
      messageInput.value = '';
      scrollToBottom();
    };

    // 收集PR数据
    const collectPRs = async () => {
      try {
        await chatStore.collectPRs();
        // 重新检查状态
        await checkRepoStatus();
      } catch (err) {
        // 错误处理已在store中完成
      }
    };

    // 更新PR URL
    const updatePrUrl = () => {
      // 这里可以添加验证逻辑
    };

    // 滚动到底部
    const scrollToBottom = () => {
      setTimeout(() => {
        if (messagesContainer.value) {
          messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
        }
      }, 100);
    };

    // 格式化时间
    const formatTime = (timestamp) => {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    // 监听消息变化，自动滚动到底部
    watch(messages, () => {
      scrollToBottom();
    }, { deep: true });

    // 计算是否可以收集PR
    const canCollectPRs = () => {
      return repoInfo.value.owner && repoInfo.value.repo;
    };

    onMounted(() => {
      initializeRepoInfo();
    });

    return {
      messages,
      isLoading,
      error,
      repoInfo,
      messageInput,
      prUrlInput,
      repoStatus,
      messagesContainer,
      hasMessages,
      isEmpty,
      sendMessage,
      collectPRs,
      updatePrUrl,
      formatTime,
      canCollectPRs
    };
  }
};
</script>

<style scoped>
.repo-rag-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

.repo-header {
  padding: 20px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  text-align: center;
}

.repo-header h1 {
  margin: 0 0 10px 0;
  color: #2c3e50;
  font-size: 24px;
}

.repo-info {
  font-size: 18px;
  color: #495057;
}

.owner-repo {
  font-weight: 600;
  color: #007bff;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.pr-input-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pr-input-section label {
  font-weight: 600;
  color: #2c3e50;
}

.pr-input-section input {
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.pr-input-section button {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.pr-input-section button:hover:not(:disabled) {
  background-color: #0056b3;
}

.pr-input-section button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.status-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #e9ecef;
  border-radius: 8px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.status-item:last-child {
  margin-bottom: 0;
}

.status-label {
  font-weight: 500;
}

.status-value {
  font-weight: 600;
}

.status-available {
  color: #28a745;
}

.status-unavailable {
  color: #dc3545;
}

.chat-section {
  display: flex;
  flex-direction: column;
  height: 60vh;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #ffffff;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6c757d;
}

.message {
  margin-bottom: 16px;
}

.message.user {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message.assistant {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.message.error {
  color: #dc3545;
  text-align: center;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px;
  word-wrap: break-word;
}

.message.user .message-content {
  background-color: #007bff;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
  background-color: #f1f3f5;
  color: #2c3e50;
  border-bottom-left-radius: 4px;
}

.message-time {
  margin-top: 4px;
  font-size: 12px;
  color: #adb5bd;
}

.loading-message {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  color: #6c757d;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.input-container {
  display: flex;
  padding: 16px;
  background-color: #f8f9fa;
  border-top: 1px solid #dee2e6;
}

.input-container textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #ced4da;
  border-radius: 20px;
  resize: none;
  font-size: 14px;
  line-height: 1.4;
  max-height: 100px;
}

.input-container button {
  margin-left: 12px;
  padding: 12px 24px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  align-self: flex-end;
}

.input-container button:hover:not(:disabled) {
  background-color: #0056b3;
}

.input-container button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .repo-rag-container {
    height: 100vh;
  }
  
  .main-content {
    padding: 10px;
  }
  
  .message-content {
    max-width: 85%;
  }
}
</style>