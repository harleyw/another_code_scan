<template>
  <div class="repo-rag-container">
    <header class="repo-header">
      <h1>代码仓库 {{ repoInfo.owner }}/{{ repoInfo.repo }} PR评审助手</h1>
      <div class="repo-info">
        <span class="owner-repo">{{ repoInfo.owner }} / {{ repoInfo.repo }}</span>
      </div>
    </header>

    <main class="main-content">
      <div class="status-and-action-container">
        <div v-if="repoStatus" class="status-container">
          <div class="status-item">
            <span class="status-label">历史PR数据状态:</span>
            <span :class="['status-value', getStatusClass(repoStatus.pr_data_status)]">
              {{ repoStatus.pr_data_status === 'historical_pr_ready' ? '已就绪' : '未就绪' }}
            </span>
          </div>
          <div class="status-item">
            <span class="status-label">向量库服务状态:</span>
            <span :class="['status-value', repoStatus.vectorstore_status === 'rag_ready' ? 'status-available' : 'status-unavailable']">
              {{ repoStatus.vectorstore_status === 'rag_ready' ? '已就绪' : '未就绪' }}
            </span>
          </div>
        </div>
        <div class="action-container">
          <button @click="collectPRs" :disabled="isLoading || !canCollectPRs" class="update-pr-btn">
            {{ isLoading ? '更新中...' : '更新历史PR数据' }}
          </button>
        </div>
      </div>

      <div class="pr-input-action-container">
        <div class="pr-input-content">
          <label for="prUrl">PR 地址:</label>
          <input
            id="prUrl"
            v-model="prUrlInput"
            type="text"
            :placeholder="`https://github.com/${repoInfo.owner}/${repoInfo.repo}/pull/123`"
            @input="updatePrUrl"
            @blur="completePrUrl"
            @keyup.enter="completePrUrl"
          />
        </div>
        <div class="pr-review-action-container">
          <button @click="submitPRUrl" :disabled="isLoading || !prUrlInput.trim()" class="submit-question-btn">
            提交PR评审
          </button>
        </div>
      </div>


      <div class="chat-section">
        <div v-if="messages.length > 0" class="answer-section">
          <div class="answer-header">
            <span class="answer-check">✓</span>
            <span class="answer-title">PR评审结果</span>
          </div>
          <div class="answer-content">
            <!-- 只显示最后一条消息（当前问题的回答） -->
            <div v-if="messages.length > 0" class="review-content" v-html="lastMessageContent"></div>
          </div>
        </div>
        
        <div v-if="isLoading" class="loading-message">
          <div class="loading-spinner"></div>
          <span>思考中...</span>
        </div>

        <!-- 输入问题文本框和发送按钮已移除 -->
      </div>
    </main>
  </div>
</template>

<script>
import { useRoute } from 'vue-router';
import { useChatStore } from '../stores/chatStore';
import { storeToRefs } from 'pinia';
import { onMounted, ref, watch, computed } from 'vue';
import { marked } from 'marked';

export default {
  name: 'RepoRag',
  setup() {
    const route = useRoute();
    const chatStore = useChatStore();
    const { messages, isLoading, error, repoInfo, hasMessages, isEmpty } = storeToRefs(chatStore);

    const prUrlInput = ref('');
    
    // 预处理函数：解析和修复嵌套代码块的特殊格式
    const processNestedCodeBlocks = (content) => {
      if (!content) return '';
      
      try {
        let processedContent = content;
        console.log('原始内容:', processedContent);
        // 处理代码示例部分中的嵌套JSON数组格式
        // 匹配模式1：```python ["``` 
        // ...需要保留的内容... 
        // ```"] 
        // ```
        const nestedCodeWithTripleBacktickRegex = /`{3}python\s*\n\s*\["`{3}\s*([\s\S]*?)\s*`{3}"\]\s*\n\s*`{3}/g;
        
        // 匹配模式2：```python [" 
        // ...需要保留的内容... 
        // "] 
        // ```
        const nestedCodeWithoutTripleBacktickRegex = /`{3}python\s*\n\s*\["\s*([\s\S]*?)\s*"\]\s*\n\s*`{3}/g;
        
        // 处理第一种模式
        if (nestedCodeWithTripleBacktickRegex.test(processedContent)) {
          processedContent = processedContent.replace(nestedCodeWithTripleBacktickRegex, (match, capture) => {
            // 处理捕获的内容：移除JSON字符串的引号，处理转义字符
            let innerContent = capture;
            
            // 处理转义字符序列
            innerContent = innerContent.replace(/\\\\/g, '\\').replace(/\\"/g, '"').replace(/\\n/g, '\n');
            
            // 确保返回正确的代码块格式（简单的```python代码块）
            return '```' + innerContent + '\n```';
          });
        }
        
        // 重置正则表达式的lastIndex，以便可以重新测试
        nestedCodeWithTripleBacktickRegex.lastIndex = 0;
        
        // 处理第二种模式
        if (nestedCodeWithoutTripleBacktickRegex.test(processedContent)) {
          processedContent = processedContent.replace(nestedCodeWithoutTripleBacktickRegex, (match, capture) => {
            // 处理捕获的内容：移除JSON字符串的引号，处理转义字符
            let innerContent = capture;
            
            // 处理转义字符序列
            innerContent = innerContent.replace(/\\\\/g, '\\').replace(/\\"/g, '"').replace(/\\n/g, '\n');
            
            // 确保返回正确的代码块格式（简单的```代码块）
            return '```python\n' + innerContent + '\n```';
          });
        }
        
        // 重置正则表达式的lastIndex
        nestedCodeWithoutTripleBacktickRegex.lastIndex = 0;
        
        // 处理其他可能的数组格式内容
        if (processedContent.startsWith('["') && processedContent.endsWith('"]')) {
          // 提取数组中的字符串
          processedContent = processedContent.slice(2, -2);
          
          // 处理转义字符
          processedContent = processedContent.replace(/\\\\/g, '\\');
          processedContent = processedContent.replace(/\\"/g, '"');
          processedContent = processedContent.replace(/\\n/g, '\n');
        }
        
        // 确保所有转义字符都被正确处理
        processedContent = processedContent.replace(/\\n/g, '\n');
        processedContent = processedContent.replace(/\\"/g, '"');
        processedContent = processedContent.replace(/\\\\/g, '\\');
        
        // 移除可能的多余空白字符
        processedContent = processedContent.trim();
        
        console.log('处理后的内容:', processedContent);
        return processedContent;
      } catch (e) {
        console.error('处理嵌套代码块时出错:', e);
        // 错误情况下尝试简单的转义字符处理作为后备
        return content.replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\\\/g, '\\');
      }
    };
    
    // 计算属性：获取最后一条消息并转换为HTML格式
    const lastMessageContent = computed(() => {
      if (messages.value.length === 0) return '';
      
      // 获取最后一条消息
      const lastMessage = messages.value[messages.value.length - 1];
      
      // 如果是助手或错误消息，使用marked进行Markdown渲染
      if (lastMessage.type === 'assistant' || lastMessage.type === 'error') {
        // 先预处理消息内容，修复嵌套代码块格式
        const processedContent = processNestedCodeBlocks(lastMessage.content || '');
        return marked(processedContent);
      }
      
      return '';
    });
    const repoStatus = ref(null);
    const messagesContainer = ref(null);
    
    // 根据PR数据状态返回对应的CSS类
    const getStatusClass = (status) => {
      if (status === 'historical_pr_ready') {
        return 'status-available';
      } else if (status === 'historical_pr_collecting' || status === 'historical_pr_updating') {
        return 'status-collecting';
      } else {
        return 'status-unavailable';
      }
    };

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



    // 提交PR URL进行评审
    const submitPRUrl = async () => {
      if (!prUrlInput.value.trim() || isLoading.value) return;
      
      // 调用store的sendMessage方法，传入PR URL作为问题
      await chatStore.sendMessage(prUrlInput.value.trim());
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
      chatStore.repoInfo.prUrl = prUrlInput.value;
    };
    
    // 补全PR URL
    const completePrUrl = () => {
      const input = prUrlInput.value.trim();
      
      // 自动补全逻辑：如果输入的是数字（可能是PR编号），且不是以完整URL开头
      if (/^\d+$/.test(input) && !input.startsWith('http')) {
        // 自动补全为完整的PR URL格式
        prUrlInput.value = `https://github.com/${repoInfo.value.owner}/${repoInfo.value.repo}/pull/${input}`;
        chatStore.repoInfo.prUrl = prUrlInput.value;
      }
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
      prUrlInput,
      repoStatus,
      messagesContainer,
      hasMessages,
      isEmpty,
      submitPRUrl,
      collectPRs,
      updatePrUrl,
      completePrUrl,
      formatTime,
      canCollectPRs,
      getStatusClass,
      lastMessageContent
    };
  }
};
</script>

<style scoped>
.repo-rag-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
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

.pr-input-action-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 15px;
}

.pr-input-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background-color: #e9ecef;
}

.pr-input-content input {
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  background-color: #ffffff;
}

.pr-input-content label {
  font-weight: 600;
  color: #2c3e50;
}

.submit-question-btn {
  width: 180px;
  padding: 12px 24px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.submit-question-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.status-and-action-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 15px;
}

.status-container {
  flex: 1;
  padding: 15px;
  background-color: #e9ecef;
  border-radius: 8px;
}

.action-container {
  white-space: nowrap;
}

.pr-review-action-container {
  white-space: nowrap;
}

.update-pr-btn {
  width: 180px;
  padding: 12px 24px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.update-pr-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.update-pr-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
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
  gap: 20px;
}

.answer-section {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
}

.answer-header {
  background-color: #f8f9fa;
  padding: 15px 20px;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  align-items: center;
  gap: 8px;
}

.answer-check {
  color: #28a745;
  font-size: 18px;
  font-weight: bold;
}

.answer-title {
  font-weight: 600;
  color: #2c3e50;
  font-size: 16px;
}

.answer-content {
  padding: 20px;
  background-color: #ffffff;
  min-height: 100px;
}

.review-content {
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  color: #2c3e50;
  line-height: 1.6;
  font-size: 16px;
  margin-bottom: 20px;
  /* 增强自动换行功能 */
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: pre-wrap;
  max-width: 100%;
  box-sizing: border-box;
}

/* 为代码块添加自动换行功能 */
.review-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
}

.review-content code {
  word-wrap: break-word;
  overflow-wrap: break-word;
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

/* 输入问题文本框和发送按钮的样式已移除 */

@media (max-width: 768px) {
  .repo-rag-container {
    height: 100vh;
  }
  
  .main-content {
    padding: 10px;
  }
}
</style>
