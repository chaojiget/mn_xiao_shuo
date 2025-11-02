"use client"

import { useState, useEffect } from "react"
import { Novel } from "@/types"
import { useToast } from "@/hooks/use-toast"
import { useChat } from "@/hooks/use-chat"
import { useNovelSettings } from "@/hooks/use-novel-settings"
import { apiClient } from "@/lib/api-client"
import { SettingsPanel } from "@/components/chat/settings-panel"
import { ChatArea } from "@/components/chat/chat-area"
import { Toaster } from "@/components/ui/toaster"

export default function ChatPage() {
  const [showSettings, setShowSettings] = useState(true)
  const [novels, setNovels] = useState<Novel[]>([])
  const { toast } = useToast()

  // 使用自定义Hook管理小说设定
  const {
    settings,
    isGenerating,
    updateSetting,
    generateSetting,
    validateSettings
  } = useNovelSettings()

  // 使用自定义Hook管理聊天
  const {
    messages,
    isLoading,
    sendMessage,
    stopGeneration,
    messagesEndRef
  } = useChat(settings)

  // 输入状态
  const [input, setInput] = useState("")

  // 加载已有小说列表
  useEffect(() => {
    loadNovels()
  }, [])

  const loadNovels = async () => {
    try {
      const data = await apiClient.getNovels()
      setNovels(data.novels || [])
    } catch (error) {
      console.error("加载小说列表失败:", error)
      toast({
        title: "加载失败",
        description: "无法加载小说列表",
        variant: "destructive"
      })
      setNovels([])
    }
  }

  // 处理自动生成设定
  const handleAutoGenerate = async () => {
    try {
      const generated = await generateSetting(settings.title, settings.type)

      toast({
        title: "生成成功",
        description: `✅ 自动生成成功！\n\n📖 世界观已创建\n👤 主角：${generated.protagonist?.name}\n🎭 NPC：${generated.npcs?.map((n: any) => n.name).join("、")}`,
      })
    } catch (error) {
      toast({
        title: "生成失败",
        description: error instanceof Error ? error.message : "生成失败，请稍后重试",
        variant: "destructive"
      })
    }
  }

  // 开始创作
  const handleStartCreating = () => {
    const validationError = validateSettings()
    if (validationError) {
      toast({
        title: "设定不完整",
        description: validationError,
        variant: "destructive"
      })
      return
    }

    setShowSettings(false)
  }

  // 发送消息
  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    try {
      await sendMessage(input.trim())
      setInput("")
    } catch (error) {
      toast({
        title: "发送失败",
        description: "消息发送失败，请稍后重试",
        variant: "destructive"
      })
    }
  }

  // 加载小说
  const handleLoadNovel = async (novelId: string) => {
    try {
      const novel = await apiClient.getNovel(novelId)
      // TODO: 实现小说加载逻辑
      toast({
        title: "加载成功",
        description: `已加载小说: ${novel.title}`
      })
    } catch (error) {
      toast({
        title: "加载失败",
        description: "无法加载该小说",
        variant: "destructive"
      })
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto max-w-7xl h-screen flex flex-col lg:flex-row gap-4 p-4">
        {/* 左侧:小说设定面板 */}
        {showSettings && (
          <SettingsPanel
            settings={settings}
            novels={novels}
            isGenerating={isGenerating}
            onUpdateSetting={updateSetting}
            onGenerateSetting={handleAutoGenerate}
            onStartCreating={handleStartCreating}
            onLoadNovel={handleLoadNovel}
          />
        )}

        {/* 右侧:聊天区域 */}
        <ChatArea
          messages={messages}
          input={input}
          setInput={setInput}
          onSend={handleSend}
          onStop={stopGeneration}
          isLoading={isLoading}
          messagesEndRef={messagesEndRef}
          settings={settings}
          showSettings={showSettings}
          onToggleSettings={() => setShowSettings(!showSettings)}
        />
      </div>
      <Toaster />
    </div>
  )
}
