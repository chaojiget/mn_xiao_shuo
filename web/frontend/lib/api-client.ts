/**
 * API 客户端 - 统一管理所有后端 API 调用
 */

import type { NovelSettings, Novel, Message } from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl
  }

  /**
   * 通用请求方法
   */
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`

    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          message: response.statusText,
        }))
        throw new Error(error.message || `请求失败: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error(`API 请求失败 [${endpoint}]:`, error)
      throw error
    }
  }

  // ==================== 小说管理 ====================

  /**
   * 获取所有小说列表
   */
  async getNovels(): Promise<{ novels: Novel[] }> {
    return this.request('/api/novels')
  }

  /**
   * 获取单个小说详情
   */
  async getNovel(novelId: string): Promise<Novel> {
    return this.request(`/api/novels/${novelId}`)
  }

  /**
   * 创建新小说
   */
  async createNovel(data: {
    title: string
    novel_type: string
    preference?: string
    settings?: NovelSettings
  }): Promise<{ novel_id: string; title: string; type: string }> {
    return this.request('/api/novels', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  /**
   * 更新小说设定
   */
  async updateNovel(
    novelId: string,
    updates: Partial<NovelSettings>
  ): Promise<{ success: boolean }> {
    return this.request(`/api/novels/${novelId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    })
  }

  /**
   * 删除小说
   */
  async deleteNovel(novelId: string): Promise<{ success: boolean }> {
    return this.request(`/api/novels/${novelId}`, {
      method: 'DELETE',
    })
  }

  /**
   * 导出小说为 Markdown
   */
  async exportNovel(novelId: string): Promise<{ markdown: string }> {
    return this.request(`/api/novels/${novelId}/export`)
  }

  // ==================== 章节管理 ====================

  /**
   * 获取指定章节
   */
  async getChapter(novelId: string, chapterNum: number) {
    return this.request(`/api/novels/${novelId}/chapters/${chapterNum}`)
  }

  // ==================== 设定生成 ====================

  /**
   * 自动生成小说设定
   */
  async generateSetting(data: {
    title: string
    novel_type: string
    user_prompt?: string
  }): Promise<{
    success: boolean
    setting?: any
    error?: string
    method?: string
  }> {
    return this.request('/api/generate-setting', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  /**
   * 优化已有设定
   */
  async optimizeSetting(data: {
    current_setting: NovelSettings
    optimization_request: string
  }): Promise<{
    success: boolean
    optimized_setting?: NovelSettings
    error?: string
  }> {
    return this.request('/api/optimize-setting', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // ==================== 聊天 ====================

  /**
   * 流式聊天 (返回 Response 用于流式读取)
   */
  async streamChat(data: {
    message: string
    novel_settings?: NovelSettings
    history?: Array<{ role: string; content: string }>
  }): Promise<Response> {
    const url = `${this.baseUrl}/api/chat/stream`
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`流式聊天失败: ${response.status}`)
    }

    return response
  }

  /**
   * 普通聊天 (非流式)
   */
  async chat(data: {
    message: string
    conversation_id?: string
    novel_settings?: NovelSettings
    history?: Message[]
  }): Promise<{ role: string; content: string }> {
    return this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // ==================== 工具方法 ====================

  /**
   * 健康检查
   */
  async healthCheck(): Promise<{ message: string; status: string }> {
    return this.request('/')
  }
}

// 导出单例
export const apiClient = new ApiClient()

// 也导出类，方便测试或自定义实例
export { ApiClient }
