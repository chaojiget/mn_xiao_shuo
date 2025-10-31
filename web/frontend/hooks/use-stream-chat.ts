/**
 * 流式聊天 Hook
 */

import { useState, useCallback } from 'react'
import { apiClient } from '@/lib/api-client'
import type { NovelSettings, Message } from '@/lib/types'
import { useNovelStore } from '@/stores/novel-store'
import { useToast } from './use-toast'

export function useStreamChat() {
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()

  const messages = useNovelStore((state) => state.messages)
  const addMessage = useNovelStore((state) => state.addMessage)
  const updateLastMessage = useNovelStore((state) => state.updateLastMessage)
  const currentNovel = useNovelStore((state) => state.currentNovel)

  /**
   * 发送消息并处理流式响应
   */
  const sendMessage = useCallback(
    async (text: string, settings?: NovelSettings) => {
      if (!text.trim() || isLoading) return

      setIsLoading(true)

      try {
        // 添加用户消息
        const userMessage: Message = {
          role: 'user',
          content: text,
          timestamp: new Date(),
        }
        addMessage(userMessage)

        // 添加空的助手消息（用于流式更新）
        const assistantMessage: Message = {
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          isStreaming: true,
        }
        addMessage(assistantMessage)

        // 构建对话历史（只取最近 10 条）
        const history = messages
          .filter((msg) => msg.role !== 'system')
          .slice(-10)
          .map((msg) => ({
            role: msg.role,
            content: msg.content,
          }))

        // 调用流式 API
        const response = await apiClient.streamChat({
          message: text,
          novel_settings: settings || currentNovel || undefined,
          history,
        })

        // 读取流式响应
        const reader = response.body?.getReader()
        const decoder = new TextDecoder()

        let assistantContent = ''

        if (reader) {
          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            const chunk = decoder.decode(value)
            const lines = chunk.split('\n\n')

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6))

                  if (data.type === 'text') {
                    assistantContent += data.content
                    updateLastMessage(assistantContent)
                  } else if (data.type === 'done') {
                    // 流式结束，标记为非流式
                    updateLastMessage(assistantContent)
                  }
                } catch (e) {
                  console.error('解析 SSE 数据失败:', e)
                }
              }
            }
          }
        }

        setIsLoading(false)
      } catch (error: any) {
        console.error('发送消息失败:', error)

        toast({
          title: '发送失败',
          description: error.message || '请稍后重试',
          variant: 'destructive',
        })

        setIsLoading(false)
      }
    },
    [isLoading, messages, addMessage, updateLastMessage, currentNovel, toast]
  )

  return {
    messages,
    isLoading,
    sendMessage,
  }
}
