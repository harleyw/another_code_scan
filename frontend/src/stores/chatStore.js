import { defineStore } from 'pinia';
import axios from 'axios';

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],
    isLoading: false,
    error: null,
    repoInfo: {
      owner: '',
      repo: '',
      prUrl: ''
    }
  }),

  actions: {
    async sendMessage(message) {
      this.addMessage(message, 'user');
      this.isLoading = true;
      this.error = null;

      try {
        // 构建请求参数
        const payload = {
          question: message,
          pr_id: this.repoInfo.prUrl || '',
          owner: this.repoInfo.owner,
          repo: this.repoInfo.repo
        };

        const response = await axios.post('/api/review_pr', payload);
        this.addMessage(response.data.answer, 'assistant');
      } catch (err) {
        console.error('发送消息失败:', err);
        this.error = '发送消息失败，请重试';
        this.addMessage('发送消息失败，请重试', 'error');
      } finally {
        this.isLoading = false;
      }
    },

    addMessage(content, type = 'message') {
      this.messages.push({
        id: Date.now(),
        content,
        type,
        timestamp: new Date()
      });
    },

    setRepoInfo(owner, repo, prUrl = '') {
      this.repoInfo.owner = owner;
      this.repoInfo.repo = repo;
      this.repoInfo.prUrl = prUrl;
      this.clearMessages();
    },

    clearMessages() {
      this.messages = [];
    },

    async collectPRs() {
      this.isLoading = true;
      this.error = null;

      try {
        const response = await axios.post('/api/collect_prs', {
          owner: this.repoInfo.owner,
          repo: this.repoInfo.repo
        });
        return response.data;
      } catch (err) {
        console.error('收集PR失败:', err);
        this.error = '收集PR失败，请重试';
        throw err;
      } finally {
        this.isLoading = false;
      }
    },

    async checkRepoStatus() {
      try {
        const response = await axios.get(`/api/review/${this.repoInfo.owner}/${this.repoInfo.repo}`);
        return response.data;
      } catch (err) {
        console.error('检查仓库状态失败:', err);
        throw err;
      }
    }
  },

  getters: {
    hasMessages: (state) => state.messages.length > 0,
    isEmpty: (state) => state.messages.length === 0
  }
});