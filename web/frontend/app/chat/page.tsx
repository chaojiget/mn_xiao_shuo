"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card } from "@/components/ui/card"
import { Send, User, Bot, Settings, BookOpen, Sparkles, Wand2, Loader2 } from "lucide-react"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"

interface Message {
  role: "user" | "assistant" | "system"
  content: string
  timestamp: Date
  isStreaming?: boolean
  character?: string
}

interface NPC {
  id: string
  name: string
  role: string
  personality: string
  background: string
}

interface NovelSettings {
  id?: string
  title: string
  type: "scifi" | "xianxia"
  protagonist: string
  background: string
  protagonistName?: string
  protagonistRole?: string
  protagonistAbilities?: string[]
  npcs?: NPC[]
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [showSettings, setShowSettings] = useState(true)
  const [novels, setNovels] = useState<any[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 小说设定
  const [settings, setSettings] = useState<NovelSettings>({
    title: "",
    type: "scifi",
    protagonist: "",
    background: "",
    npcs: []
  })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 加载已有小说列表
  useEffect(() => {
    loadNovels()
  }, [])

  const loadNovels = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/novels")
      if (response.ok) {
        const data = await response.json()
        setNovels(data.novels || [])
      }
    } catch (error) {
      console.error("加载小说列表失败:", error)
      setNovels([])
    }
  }

  // 自动生成设定
  const handleAutoGenerate = async () => {
    if (!settings.title.trim()) {
      alert("请先输入小说标题")
      return
    }

    setIsGenerating(true)

    try {
      const response = await fetch("http://localhost:8000/api/generate-setting", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: settings.title,
          novel_type: settings.type
        })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          const generated = data.setting

          // 更新设定
          setSettings({
            ...settings,
            background: generated.world_setting,
            protagonist: generated.protagonist.background,
            protagonistName: generated.protagonist.name,
            protagonistRole: generated.protagonist.role,
            protagonistAbilities: generated.protagonist.abilities,
            npcs: generated.npcs
          })

          // 显示成功消息
          setMessages([
            {
              role: "system",
              content: `✅ 自动生成成功！\n\n📖 世界观已创建\n👤 主角：${generated.protagonist.name}（${generated.protagonist.role}）\n🎭 NPC：${generated.npcs.map((n: NPC) => n.name).join("、")}`,
              timestamp: new Date()
            }
          ])
        } else {
          alert(`生成失败: ${data.error}`)
        }
      }
    } catch (error) {
      console.error("生成设定失败:", error)
      alert("生成失败，请稍后重试")
    } finally {
      setIsGenerating(false)
    }
  }

  // 开始创作
  const handleStartCreating = () => {
    if (!settings.title || !settings.background) {
      alert("请先填写完整设定或使用自动生成")
      return
    }

    setShowSettings(false)

    // 发送欢迎消息
    const welcomeMessage = `欢迎来到《${settings.title}》的世界！\n\n${settings.background}\n\n你现在是${settings.protagonistName || "主角"}，${settings.protagonistRole || settings.protagonist}。\n\n故事即将开始...`

    setMessages([
      {
        role: "assistant",
        content: welcomeMessage,
        timestamp: new Date()
      }
    ])
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    await generateContent(input.trim())
    setInput("")
  }

  const generateContent = async (userInput: string) => {
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

      const response = await fetch("http://localhost:8000/api/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: userInput,
          novel_settings: settings,
          history: history
        })
      })

      if (!response.ok) {
        throw new Error("请求失败")
      }

      // 读取流式响应
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      let assistantContent = ""

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split("\n\n")

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6))

                if (data.type === "text") {
                  assistantContent += data.content

                  // 更新最后一条消息
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
      console.error("发送消息失败:", error)
      setMessages(prev => [
        ...prev.slice(0, -1),
        {
          role: "assistant",
          content: "抱歉,发生了错误。请稍后重试。",
          timestamp: new Date()
        }
      ])
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto max-w-7xl h-screen flex gap-4 p-4">
        {/* 左侧:小说设定面板 */}
        {showSettings && (
          <div className="w-[500px] flex flex-col gap-4">
            {/* 主标题区域 */}
            <Card className="p-6 bg-white/5 border-white/10 backdrop-blur-sm">
              <div className="text-center mb-6">
                <h1 className="text-3xl font-bold text-white mb-2 flex items-center justify-center gap-2">
                  <Sparkles className="w-8 h-8 text-yellow-400" />
                  AI 跑团小说
                </h1>
                <p className="text-gray-400 text-sm">输入标题，一键生成完整的世界观和角色设定</p>
              </div>

              {/* 标题输入 - 突出显示 */}
              <div className="mb-4">
                <Label className="text-white mb-2 block text-lg font-semibold">📖 小说标题</Label>
                <input
                  value={settings.title}
                  onChange={(e) => setSettings({ ...settings, title: e.target.value })}
                  placeholder="例如：星际迷航、修仙者传说..."
                  className="w-full px-4 py-3 bg-white/10 border-2 border-white/20 rounded-lg text-white text-lg placeholder:text-gray-400 focus:border-purple-500 focus:outline-none transition-all"
                />
              </div>

              {/* 类型选择 */}
              <div className="mb-4">
                <Label className="text-white mb-2 block font-semibold">🎨 类型</Label>
                <RadioGroup
                  value={settings.type}
                  onValueChange={(value: "scifi" | "xianxia") =>
                    setSettings({ ...settings, type: value })
                  }
                  className="flex gap-4"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 p-3 rounded-lg bg-white/10 border border-white/20 hover:bg-white/20 transition-colors cursor-pointer">
                      <RadioGroupItem value="scifi" id="scifi" />
                      <Label htmlFor="scifi" className="text-white cursor-pointer flex-1">🚀 科幻</Label>
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 p-3 rounded-lg bg-white/10 border border-white/20 hover:bg-white/20 transition-colors cursor-pointer">
                      <RadioGroupItem value="xianxia" id="xianxia" />
                      <Label htmlFor="xianxia" className="text-white cursor-pointer flex-1">⚔️ 玄幻</Label>
                    </div>
                  </div>
                </RadioGroup>
              </div>

              {/* 一键生成按钮 */}
              <Button
                onClick={handleAutoGenerate}
                disabled={isGenerating || !settings.title.trim()}
                className="w-full py-6 text-lg font-bold bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 transition-all disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-6 h-6 mr-2 animate-spin" />
                    AI 正在创作中...
                  </>
                ) : (
                  <>
                    <Wand2 className="w-6 h-6 mr-2" />
                    ✨ 一键生成完整设定
                  </>
                )}
              </Button>
            </Card>

            {/* 生成的详细设定 */}
            {(settings.background || settings.npcs?.length) && (
              <Card className="p-4 bg-white/5 border-white/10 backdrop-blur-sm flex-1 overflow-y-auto">
                <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  生成的设定
                </h3>

                <div className="space-y-4 text-white text-sm">
                  {/* 主角信息 */}
                  {settings.protagonistName && (
                    <div className="p-3 rounded-lg bg-blue-500/20 border border-blue-500/30">
                      <div className="font-bold text-blue-300 mb-1">👤 主角</div>
                      <div className="font-semibold">{settings.protagonistName}</div>
                      <div className="text-gray-300 text-xs">{settings.protagonistRole}</div>
                      {settings.protagonistAbilities && settings.protagonistAbilities.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {settings.protagonistAbilities.map((ability, i) => (
                            <span key={i} className="px-2 py-1 rounded bg-blue-600/30 text-xs">
                              {ability}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* 世界观 */}
                  {settings.background && (
                    <div>
                      <div className="font-bold text-purple-300 mb-1">🌍 世界观</div>
                      <div className="text-gray-300 text-xs leading-relaxed whitespace-pre-wrap">
                        {settings.background}
                      </div>
                    </div>
                  )}

                  {/* NPC 列表 */}
                  {settings.npcs && settings.npcs.length > 0 && (
                    <div>
                      <div className="font-bold text-green-300 mb-2">🎭 NPC 角色</div>
                      <div className="space-y-2">
                        {settings.npcs.map(npc => (
                          <div key={npc.id} className="p-2 rounded bg-white/10 border border-white/10">
                            <div className="font-semibold">{npc.name} <span className="text-xs text-gray-400">({npc.role})</span></div>
                            <div className="text-xs text-gray-400 mt-1">{npc.personality}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 开始创作按钮 */}
                  <Button
                    onClick={handleStartCreating}
                    className="w-full py-4 bg-green-600 hover:bg-green-700 transition-all"
                  >
                    <Sparkles className="w-5 h-5 mr-2" />
                    开始创作
                  </Button>
                </div>
              </Card>
            )}

            {/* 已有小说列表（折叠） */}
            {novels.length > 0 && (
              <Card className="p-4 bg-white/5 border-white/10 backdrop-blur-sm">
                <details>
                  <summary className="text-white font-bold cursor-pointer flex items-center gap-2">
                    <BookOpen className="w-5 h-5" />
                    我的小说 ({novels.length})
                  </summary>
                  <div className="mt-3 space-y-2 max-h-40 overflow-y-auto">
                    {novels.map(novel => (
                      <button
                        key={novel.id}
                        onClick={() => {/* TODO: loadNovel(novel.id) */}}
                        className="w-full text-left px-3 py-2 rounded bg-white/10 hover:bg-white/20 transition-colors text-white text-sm"
                      >
                        <div className="font-medium">{novel.title}</div>
                        <div className="text-xs text-gray-400">
                          {novel.type === "scifi" ? "🚀 科幻" : "⚔️ 玄幻"}
                        </div>
                      </button>
                    ))}
                  </div>
                </details>
              </Card>
            )}
          </div>
        )}

        {/* 右侧:聊天区域 */}
        <div className="flex-1 flex flex-col">
          <Card className="flex-1 flex flex-col bg-white/5 border-white/10 backdrop-blur-sm overflow-hidden">
            {/* 顶部栏 */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between">
              <div>
                <h2 className="text-white font-bold text-lg">{settings.title || "AI 跑团"}</h2>
                {settings.protagonistName && (
                  <p className="text-gray-400 text-sm">扮演: {settings.protagonistName}</p>
                )}
              </div>
              {!showSettings && (
                <Button
                  onClick={() => setShowSettings(true)}
                  variant="outline"
                  size="sm"
                  className="text-white border-white/20"
                >
                  <Settings className="w-4 h-4 mr-2" />
                  设定
                </Button>
              )}
            </div>

            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="h-full flex items-center justify-center text-gray-400">
                  {showSettings ? (
                    <div className="text-center">
                      <Wand2 className="w-16 h-16 mx-auto mb-4 text-purple-400" />
                      <p>输入标题，点击"一键生成"开始创作</p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <p>开始你的冒险吧...</p>
                    </div>
                  )}
                </div>
              ) : (
                messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {message.role !== "user" && (
                      <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center flex-shrink-0">
                        {message.role === "system" ? "📢" : <Bot className="w-5 h-5 text-white" />}
                      </div>
                    )}
                    <div
                      className={`max-w-[70%] rounded-lg p-3 ${
                        message.role === "user"
                          ? "bg-purple-600 text-white"
                          : message.role === "system"
                          ? "bg-yellow-600/20 text-yellow-200 border border-yellow-600/30"
                          : "bg-white/10 text-white"
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{message.content}</div>
                      {message.isStreaming && (
                        <span className="inline-block w-2 h-4 bg-white/50 ml-1 animate-pulse" />
                      )}
                    </div>
                    {message.role === "user" && (
                      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                        <User className="w-5 h-5 text-white" />
                      </div>
                    )}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* 输入框 */}
            {!showSettings && (
              <div className="p-4 border-t border-white/10">
                <div className="flex gap-2">
                  <Textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="输入你的行动或对话..."
                    className="flex-1 min-h-[60px] max-h-[120px] bg-white/10 border-white/20 text-white placeholder:text-gray-400 focus:border-purple-500 resize-none"
                  />
                  <Button
                    onClick={handleSend}
                    disabled={isLoading || !input.trim()}
                    className="px-6 bg-purple-600 hover:bg-purple-700"
                  >
                    <Send className="w-5 h-5" />
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
