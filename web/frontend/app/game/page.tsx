"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { useGameState } from "@/hooks/use-game-state"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api-client"
import { Toaster } from "@/components/ui/toaster"
import { GameState, GameAction } from "@/types/game"
import { Loader2, Play, Save, Upload, Download, Scroll, Heart, Zap, MapPin, Coins, Map } from "lucide-react"
import { StreamingText } from "@/components/chat/StreamingText"
import { SimpleMap } from "@/components/chat/SimpleMap"

export default function GameTestPage() {
  const [input, setInput] = useState("")
  const [narration, setNarration] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [currentStreaming, setCurrentStreaming] = useState<string | null>(null)
  const narrationEndRef = useRef<HTMLDivElement>(null)

  const { toast } = useToast()
  const {
    gameState,
    initGame,
    applyActions,
    saveGame,
    loadGame,
    exportGame,
    importGame,
    getPlayerState,
    getQuests
  } = useGameState()

  // 初始化游戏
  const handleInitGame = async () => {
    try {
      const response = await apiClient.initGame()

      if (response.success && response.state) {
        initGame(response.state as GameState)
        setNarration([response.narration])
        setSuggestions(response.suggestions || [])

        toast({
          title: "游戏已初始化",
          description: "开始你的冒险吧！"
        })
      }
    } catch (error) {
      toast({
        title: "初始化失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      })
    }
  }

  // 自动滚动到底部
  useEffect(() => {
    narrationEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [narration, currentStreaming])

  // 处理玩家输入
  const handlePlayerAction = async () => {
    if (!input.trim() || !gameState) return

    setIsProcessing(true)
    const userInput = input.trim()
    setInput("")

    // 立即显示玩家输入
    setNarration(prev => [...prev, `[你] ${userInput}`])

    try {
      // 序列化并反序列化以清理不可序列化的数据
      const cleanState = JSON.parse(JSON.stringify(gameState))

      const response = await apiClient.processTurn({
        playerInput: userInput,
        currentState: cleanState
      })

      if (response.success) {
        // 设置流式显示的文本
        setCurrentStreaming(response.narration)

        // 应用行动
        if (response.actions && response.actions.length > 0) {
          // 转换actions格式
          const gameActions: GameAction[] = response.actions.map((action: any) => ({
            type: action.type,
            ...action.arguments
          }))
          applyActions(gameActions)
        }

        // 更新建议
        setSuggestions(response.suggestions || [])

        // 显示提示
        if (response.hints && response.hints.length > 0) {
          toast({
            title: "提示",
            description: response.hints.join("\n")
          })
        }
      }
    } catch (error) {
      toast({
        title: "处理失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      })
      setIsProcessing(false)
      setCurrentStreaming(null)
    }
  }

  // 流式文本完成后的回调
  const handleStreamComplete = () => {
    if (currentStreaming) {
      setNarration(prev => [...prev, currentStreaming])
      setCurrentStreaming(null)
      setIsProcessing(false)
    }
  }

  // 快捷建议
  const handleSuggestion = (suggestion: string) => {
    setInput(suggestion)
  }

  // 存档
  const handleSave = () => {
    if (saveGame()) {
      toast({ title: "保存成功", description: "游戏已自动保存" })
    } else {
      toast({ title: "保存失败", variant: "destructive" })
    }
  }

  // 读档
  const handleLoad = () => {
    if (loadGame()) {
      toast({ title: "读取成功", description: "游戏已恢复" })
    } else {
      toast({ title: "读取失败", variant: "destructive" })
    }
  }

  // 导出
  const handleExport = () => {
    const data = exportGame()
    if (data) {
      const blob = new Blob([data], { type: "application/json" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `game_save_${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
      toast({ title: "导出成功" })
    }
  }

  const player = getPlayerState()
  const activeQuests = getQuests("active")

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="container mx-auto max-w-7xl">
        {/* 顶部工具栏 */}
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">AI 跑团游戏 - 核心协议测试</h1>
          <div className="flex gap-2">
            {!gameState && (
              <Button onClick={handleInitGame} className="bg-green-600 hover:bg-green-700">
                <Play className="w-4 h-4 mr-2" />
                开始游戏
              </Button>
            )}
            {gameState && (
              <>
                <Button onClick={handleSave} variant="outline">
                  <Save className="w-4 h-4 mr-2" />
                  保存
                </Button>
                <Button onClick={handleLoad} variant="outline">
                  <Upload className="w-4 h-4 mr-2" />
                  读取
                </Button>
                <Button onClick={handleExport} variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  导出
                </Button>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* 主区域 - 叙事 */}
          <div className="col-span-2 space-y-4">
            {/* 叙事区 */}
            <Card className="p-6 bg-gradient-to-b from-slate-900/90 to-slate-800/90 border-amber-500/20 backdrop-blur-sm min-h-[500px] max-h-[600px] overflow-y-auto shadow-2xl">
              <div className="flex items-center gap-2 mb-4 border-b border-amber-500/30 pb-3">
                <Scroll className="w-5 h-5 text-amber-400" />
                <h2 className="text-xl font-bold text-amber-100">冒险纪事</h2>
              </div>
              <div className="text-gray-300 space-y-4 font-serif">
                {narration.map((text, i) => (
                  <div
                    key={i}
                    className={
                      text.startsWith("[你]")
                        ? "text-cyan-300 font-semibold bg-cyan-950/30 p-3 rounded-lg border-l-4 border-cyan-500"
                        : "text-amber-50 leading-relaxed"
                    }
                  >
                    {text}
                  </div>
                ))}
                {currentStreaming && (
                  <StreamingText
                    text={currentStreaming}
                    speed={20}
                    onComplete={handleStreamComplete}
                    className="text-amber-50 leading-relaxed"
                  />
                )}
                {narration.length === 0 && !currentStreaming && (
                  <div className="text-gray-500 text-center py-20 italic">
                    点击"开始游戏"踏上冒险之旅...
                  </div>
                )}
                <div ref={narrationEndRef} />
              </div>
            </Card>

            {/* 输入区 */}
            {gameState && (
              <Card className="p-4 bg-white/5 border-white/10 backdrop-blur-sm">
                <div className="space-y-3">
                  <Textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault()
                        handlePlayerAction()
                      }
                    }}
                    placeholder="输入你的行动..."
                    className="bg-white/10 border-white/20 text-white min-h-[80px]"
                    disabled={isProcessing}
                  />
                  <div className="flex items-center justify-between">
                    <div className="flex flex-wrap gap-2">
                      {suggestions.map((sug, i) => (
                        <Button
                          key={i}
                          variant="outline"
                          size="sm"
                          onClick={() => handleSuggestion(sug)}
                          className="text-xs"
                        >
                          {sug}
                        </Button>
                      ))}
                    </div>
                    <Button
                      onClick={handlePlayerAction}
                      disabled={!input.trim() || isProcessing}
                      className="bg-purple-600 hover:bg-purple-700"
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          处理中...
                        </>
                      ) : (
                        "执行"
                      )}
                    </Button>
                  </div>
                </div>
              </Card>
            )}
          </div>

          {/* 侧边栏 - 状态 */}
          <div className="space-y-4">
            {/* 玩家状态 */}
            <Card className="p-4 bg-gradient-to-br from-rose-950/40 to-purple-950/40 border-rose-500/30 backdrop-blur-sm">
              <h3 className="text-lg font-bold text-rose-100 mb-3 flex items-center gap-2">
                <Heart className="w-4 h-4" />
                角色状态
              </h3>
              {player ? (
                <div className="space-y-3 text-sm">
                  {/* 生命值 */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-rose-200 flex items-center gap-1">
                        <Heart className="w-3 h-3" />
                        生命
                      </span>
                      <span className="text-rose-300 font-bold">{player.hp}/{player.maxHp}</span>
                    </div>
                    <div className="w-full bg-rose-950/50 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-rose-500 to-red-600 h-full transition-all duration-300"
                        style={{ width: `${(player.hp / player.maxHp) * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* 体力值 */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-green-200 flex items-center gap-1">
                        <Zap className="w-3 h-3" />
                        体力
                      </span>
                      <span className="text-green-300 font-bold">{player.stamina}/{player.maxStamina}</span>
                    </div>
                    <div className="w-full bg-green-950/50 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-green-500 to-emerald-600 h-full transition-all duration-300"
                        style={{ width: `${(player.stamina / player.maxStamina) * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* 位置 */}
                  <div className="flex justify-between items-center pt-2 border-t border-white/10">
                    <span className="text-amber-200 flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      位置
                    </span>
                    <span className="text-amber-300 font-semibold">{player.location}</span>
                  </div>

                  {/* 金钱 */}
                  <div className="flex justify-between items-center">
                    <span className="text-yellow-200 flex items-center gap-1">
                      <Coins className="w-3 h-3" />
                      金币
                    </span>
                    <span className="text-yellow-300 font-bold">{player.money || 0}</span>
                  </div>
                </div>
              ) : (
                <div className="text-gray-500 text-sm">未初始化</div>
              )}
            </Card>

            {/* 背包 */}
            <Card className="p-4 bg-white/5 border-white/10 backdrop-blur-sm">
              <h3 className="text-lg font-bold text-white mb-3">背包</h3>
              {player && player.inventory.length > 0 ? (
                <div className="space-y-1 text-sm text-gray-300">
                  {player.inventory.map((item, i) => (
                    <div key={i} className="flex justify-between">
                      <span>{item.name}</span>
                      <span className="text-gray-500">x{item.quantity}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-gray-500 text-sm">空</div>
              )}
            </Card>

            {/* 任务 */}
            <Card className="p-4 bg-white/5 border-white/10 backdrop-blur-sm">
              <h3 className="text-lg font-bold text-white mb-3">活跃任务</h3>
              {activeQuests.length > 0 ? (
                <div className="space-y-2 text-sm text-gray-300">
                  {activeQuests.map((quest, i) => (
                    <div key={i} className="border-l-2 border-blue-500 pl-2">
                      <div className="font-semibold">{quest.title}</div>
                      <div className="text-xs text-gray-400">{quest.description}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-gray-500 text-sm">无</div>
              )}
            </Card>

            {/* 地图 */}
            {gameState && (
              <Card className="p-4 bg-gradient-to-br from-slate-900/90 to-slate-800/90 border-amber-500/20 backdrop-blur-sm">
                <h3 className="text-lg font-bold text-amber-100 mb-3 flex items-center gap-2">
                  <Map className="w-4 h-4" />
                  探索地图
                </h3>
                <SimpleMap
                  nodes={gameState.map.nodes}
                  edges={gameState.map.edges}
                  currentNodeId={gameState.map.currentNodeId}
                />
              </Card>
            )}

            {/* 调试信息 */}
            <Card className="p-4 bg-white/5 border-white/10 backdrop-blur-sm">
              <h3 className="text-lg font-bold text-white mb-3">调试</h3>
              <div className="space-y-1 text-xs text-gray-400 font-mono">
                <div>回合: {gameState?.world.time || 0}</div>
                <div>版本: {gameState?.version || "N/A"}</div>
                <div>日志: {gameState?.log.length || 0} 条</div>
              </div>
            </Card>
          </div>
        </div>
      </div>
      <Toaster />
    </div>
  )
}
