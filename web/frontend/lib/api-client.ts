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

  // ==================== 游戏API ====================

  /**
   * 初始化新游戏
   */
  async initGame(config?: { storyId?: string; playerConfig?: any }): Promise<{
    success: boolean
    state: any
    narration: string
    suggestions?: string[]
  }> {
    return this.request('/api/game/init', {
      method: 'POST',
      body: JSON.stringify(config || {}),
    })
  }

  /**
   * 处理游戏回合（非流式）
   */
  async processTurn(data: {
    playerInput: string
    currentState: any
  }): Promise<{
    success: boolean
    narration: string
    actions: any[]
    hints?: string[]
    suggestions?: string[]
    metadata?: any
    updatedState: any
  }> {
    return this.request('/api/game/turn', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  /**
   * 处理游戏回合（流式）
   */
  async processTurnStream(data: {
    playerInput: string
    currentState: any
  }): Promise<Response> {
    const url = `${this.baseUrl}/api/game/turn/stream`
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`流式处理失败: ${response.status}`)
    }

    return response
  }

  /**
   * 获取可用工具列表
   */
  async getGameTools(): Promise<{ tools: any[] }> {
    return this.request('/api/game/tools')
  }

  // ==================== 世界管理API ====================

  /**
   * 生成世界脚手架
   */
  async generateWorld(data: {
    novelId: string
    theme: string
    tone: string
    novelType: "scifi" | "xianxia"
    numRegions?: number
    locationsPerRegion?: number
    poisPerLocation?: number
  }): Promise<{
    world: any
    regions: any[]
    message: string
  }> {
    return this.request('/api/world/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  /**
   * 根据小说ID获取世界
   */
  async getWorldByNovel(novelId: string): Promise<any> {
    return this.request(`/api/world/by-novel/${novelId}`)
  }

  /**
   * 获取世界详情
   */
  async getWorld(worldId: string): Promise<any> {
    return this.request(`/api/world/scaffold/${worldId}`)
  }

  /**
   * 获取区域列表
   */
  async getRegions(worldId: string): Promise<any[]> {
    return this.request(`/api/world/scaffold/${worldId}/regions`)
  }

  /**
   * 获取地点列表
   */
  async getLocations(regionId: string): Promise<any[]> {
    return this.request(`/api/world/region/${regionId}/locations`)
  }

  /**
   * 细化地点（触发4-Pass流水线）
   */
  async refineLocation(data: {
    locationId: string
    turn?: number
    targetDetailLevel?: number
    passes?: string[]
    characterState?: any
  }): Promise<{
    location: any
    layers: any[]
    affordances: any[]
    narrative_text: string
  }> {
    const { locationId, turn = 0, targetDetailLevel = 2, passes = ['structure', 'sensory', 'affordance', 'cinematic'], characterState } = data
    return this.request(`/api/world/location/${locationId}/refine`, {
      method: 'POST',
      body: JSON.stringify({
        location_id: locationId,
        turn,
        target_detail_level: targetDetailLevel,
        passes,
        character_state: characterState
      }),
    })
  }

  /**
   * 提取可供性chips
   */
  async extractAffordances(data: {
    locationId: string
    characterState?: any
  }): Promise<{
    affordances: any[]
    suggested_actions: string[]
  }> {
    const { locationId, characterState } = data
    return this.request(`/api/world/location/${locationId}/affordances`, {
      method: 'POST',
      body: JSON.stringify({
        location_id: locationId,
        character_state: characterState
      }),
    })
  }

  /**
   * 获取派系列表
   */
  async getFactions(worldId: string): Promise<any[]> {
    return this.request(`/api/world/scaffold/${worldId}/factions`)
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
