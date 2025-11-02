import { useState, useCallback, useRef, useEffect } from "react"
import { Message, NovelSettings } from "@/types"
import { apiClient } from "@/lib/api-client"

export const useChat = (settings: NovelSettings) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const generateContent = useCallback(async (userInput: string) => {
    if (isLoading || !userInput.trim()) return

    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    abortControllerRef.current = new AbortController()
    setIsLoading(true)

    try {
      // 添加用户消息
      const userMessage: Message = {
        role: "user",
        content: userInput,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, userMessage])

      // 添加空的助手消息（用于流式更新）
      const assistantMessage: Message = {
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isStreaming: true
      }
      setMessages(prev => [...prev, assistantMessage])

      // 构建对话历史
      const history = messages
        .filter(msg => msg.role !== "system")
        .slice(-10)
        .map(msg => ({
          role: msg.role,
          content: msg.content
        }))

      const response = await apiClient.streamChat({
        message: userInput,
        novel_settings: settings,
        history: history
      })

      if (!response.ok) {
        throw new Error("请求失败")
      }

      // 读取流式响应
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      let assistantContent = ""

      if (reader && !abortControllerRef.current.signal.aborted) {
        while (true) {
          const { done, value } = await reader.read()
          if (done || abortControllerRef.current.signal.aborted) break

          const chunk = decoder.decode(value)
          const lines = chunk.split("\n\n")

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6))

                if (data.type === "text") {
                  assistantContent += data.content

                  // 批量更新消息内容
                  setMessages(prev => {
                    const newMessages = [...prev]
                    const lastMessage = newMessages[newMessages.length - 1]
                    if (lastMessage && lastMessage.role === "assistant") {
                      lastMessage.content = assistantContent
                    }
                    return newMessages
                  })
                } else if (data.type === "done") {
                  // 流式结束
                  setMessages(prev => {
                    const newMessages = [...prev]
                    const lastMessage = newMessages[newMessages.length - 1]
                    if (lastMessage) {
                      lastMessage.isStreaming = false
                    }
                    return newMessages
                  })
                }
              } catch (e) {
                console.error("解析 SSE 数据失败:", e)
              }
            }
          }
        }
      }

      setIsLoading(false)
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        console.error("发送消息失败:", error)

        // 移除最后一条消息并添加错误消息
        setMessages(prev => [
          ...prev.slice(0, -1),
          {
            role: "assistant",
            content: "抱歉，发生了错误。请稍后重试。",
            timestamp: new Date()
          }
        ])
      }
      setIsLoading(false)
    }
  }, [messages, settings, isLoading])

  const sendMessage = useCallback(async (input: string) => {
    if (!input.trim() || isLoading) return
    await generateContent(input.trim())
  }, [generateContent, isLoading])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    setIsLoading(false)
  }, [])

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  return {
    messages,
    isLoading,
    isGenerating,
    sendMessage,
    clearMessages,
    stopGeneration,
    messagesEndRef,
    scrollToBottom
  }
}