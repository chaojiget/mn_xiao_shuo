"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Save, Upload, RotateCcw, Home, MapPin, Scroll, Heart, Coins, Zap, FolderOpen } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DmInterface } from "@/components/game/DmInterface"
import { QuestTracker } from "@/components/game/QuestTracker"
import { SaveGameDialog } from "@/components/game/SaveGameDialog"
import { useGameStore } from "@/stores/gameStore"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api-client"

export default function GamePlayPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { gameState, setGameState, resetGame } = useGameStore()
  const [sessionId, setSessionId] = useState<string>("")
  const [isInitializing, setIsInitializing] = useState(true)
  const [worldId, setWorldId] = useState<string | null>(null)
  const [forceReset, setForceReset] = useState(false)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const wid = params.get("worldId")
    const reset = params.get("reset") === "true"
    setWorldId(wid)
    setForceReset(reset)

    // 🔥 修复：立即加载游戏，而不是等待 worldId 的 useEffect
    loadOrInitGame(wid, reset)
  }, [])

  const loadOrInitGame = async (wid: string | null = null, reset: boolean = false) => {
    try {
      setIsInitializing(true)
      console.log("[GamePlay] 开始加载游戏, worldId:", wid, "reset:", reset)

      // 🔥 优先检查 localStorage 中是否有加载的存档（从存档列表加载时）
      const loadedGameState = localStorage.getItem('loadedGameState')
      if (loadedGameState && !reset) {
        try {
          const parsedState = JSON.parse(loadedGameState)
          console.log("[GamePlay] ✅ 从存档页加载游戏进度")
          console.log("[GamePlay] 📊 存档数据:", {
            turn: parsedState.turn_number || parsedState.world?.time,
            location: parsedState.player?.location,
            hp: parsedState.player?.hp
          })

          setGameState(parsedState)
          setSessionId(parsedState.session_id || `session_${Date.now()}`)

          // 🔥 延迟清除 localStorage，避免 React Strict Mode 重复执行时找不到数据
          setTimeout(() => {
            localStorage.removeItem('loadedGameState')
            console.log("[GamePlay] 🗑️  已清除临时存档标记")
          }, 1000)

          toast({
            title: "✅ 存档已加载",
            description: `继续第 ${parsedState.turn_number || parsedState.world?.time || 0} 回合的冒险`,
            duration: 3000,
          })
          return
        } catch (error) {
          console.error("[GamePlay] ❌ 解析存档失败:", error)
          localStorage.removeItem('loadedGameState')
        }
      }

      // 如果没有从存档加载，检查自动保存
      const autoSave = await apiClient.getLatestAutoSave()
      console.log("[GamePlay] 自动保存检查结果:", autoSave.success)

      if (autoSave.success && autoSave.game_state && !reset) {
        const savedWorldId = autoSave.game_state.metadata?.worldPackId

        if (wid && savedWorldId !== wid) {
          console.log("[GamePlay] 🆕 worldId 不匹配，初始化新游戏")
          await initGame(wid || undefined)
        } else {
          console.log("[GamePlay] ✅ 恢复自动保存进度")
          setGameState(autoSave.game_state)
          setSessionId(autoSave.game_state.session_id || `session_${Date.now()}`)

          toast({
            title: "✅ 进度已恢复",
            description: `继续第 ${autoSave.game_state.turn_number || 0} 回合的冒险`,
            duration: 3000,
          })
        }
      } else {
        console.log("[GamePlay] 🆕 初始化新游戏")
        await initGame(wid || undefined)
      }
    } catch (error) {
      console.error("[GamePlay] ❌ 加载失败:", error)
      await initGame(wid || undefined)
    } finally {
      setIsInitializing(false)
    }
  }

  const initGame = async (worldIdParam?: string) => {
    const response = await fetch("/api/game/init", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        worldId: worldIdParam || null,
        storyId: null,
        playerConfig: null,
      }),
    })

    if (!response.ok) {
      throw new Error(`初始化失败: ${response.status}`)
    }

    const data = await response.json()

    if (data.success) {
      setGameState(data.state)
      setSessionId(data.state.session_id || `session_${Date.now()}`)

      toast({
        title: "🎮 游戏开始",
        description: data.narration,
        duration: 5000,
      })
    } else {
      throw new Error(data.error || "初始化失败")
    }
  }

  const handleSaveToSlot = async (slotId: number, saveName: string) => {
    if (!gameState) return

    try {
      const response = await apiClient.request<any>("/api/game/save", {
        method: "POST",
        body: JSON.stringify({
          user_id: "default_user",
          slot_id: slotId,
          save_name: saveName,
          game_state: gameState,
        }),
      })

      if (response.success) {
        toast({
          title: "✅ 保存成功",
          description: `已保存到槽位 ${slotId}: ${saveName}`,
        })
      }
    } catch (error) {
      console.error("[GamePlay] 保存失败:", error)
      toast({
        title: "错误",
        description: "保存游戏失败",
        variant: "destructive",
      })
    }
  }

  const handleLoadFromSlot = async (slotId: number) => {
    try {
      const response = await apiClient.request<any>("/api/game/saves/default_user")

      if (response.success && response.saves) {
        const save = response.saves.find((s: any) => s.slot_id === slotId)

        if (save) {
          const loadResponse = await apiClient.request<any>(`/api/game/save/${save.save_id}`)

          if (loadResponse.success && loadResponse.game_state) {
            setGameState(loadResponse.game_state)
            setSessionId(loadResponse.game_state.session_id || `session_${Date.now()}`)

            toast({
              title: "✅ 读取成功",
              description: `已加载: ${save.save_name}`,
            })
          }
        } else {
          toast({
            title: "❌ 槽位为空",
            description: `槽位 ${slotId} 没有存档`,
            variant: "destructive",
          })
        }
      }
    } catch (error) {
      console.error("[GamePlay] 读取失败:", error)
      toast({
        title: "错误",
        description: "读取存档失败",
        variant: "destructive",
      })
    }
  }

  const handleResetGame = () => {
    if (confirm("确定要重新开始吗？当前进度将被清除。")) {
      resetGame()
      window.location.reload()
    }
  }

  if (isInitializing) {
    return (
      <div className="h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-lg font-semibold text-white">正在初始化游戏...</p>
        </div>
      </div>
    )
  }

  const worldTitle = (gameState?.metadata as any)?.worldPackTitle || "未知世界"
  const currentLocation = gameState?.map?.nodes?.find(
    (n: any) => n.id === gameState.map.currentNodeId
  )?.name || "未知地点"

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* 顶部状态栏 */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-purple-500/30 px-4 py-3">
        <div className="flex items-center justify-between">
          {/* 左侧：世界信息 */}
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              className="text-purple-400 hover:text-purple-300 hover:bg-purple-500/10"
              onClick={() => router.push("/")}
            >
              <Home className="w-5 h-5" />
            </Button>
            <div className="hidden md:block">
              <h1 className="text-lg font-bold text-white">{worldTitle}</h1>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <MapPin className="w-4 h-4" />
                <span>{currentLocation}</span>
                <span className="text-purple-400">·</span>
                <span>第 {gameState?.turn_number || 0} 回合</span>
              </div>
            </div>
          </div>

          {/* 右侧：操作按钮 */}
          <div className="flex items-center gap-2">
            {/* 使用新的 SaveGameDialog 组件 */}
            {gameState && (
              <SaveGameDialog
                gameState={gameState}
                onSaveSuccess={() => {
                  toast({
                    title: "✅ 保存成功",
                    description: "游戏进度已保存",
                  })
                }}
                trigger={
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-gray-300 hover:text-white hover:bg-slate-800"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    保存
                  </Button>
                }
              />
            )}

            <Button
              variant="ghost"
              size="sm"
              className="text-gray-300 hover:text-white hover:bg-slate-800"
              onClick={() => router.push('/saves')}
            >
              <FolderOpen className="w-4 h-4 mr-2" />
              存档管理
            </Button>

            <Button
              variant="ghost"
              size="sm"
              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
              onClick={handleResetGame}
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              重新开始
            </Button>
          </div>
        </div>
      </header>

      {/* 主要内容区域 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧边栏 - 玩家状态 */}
        <aside className="w-80 bg-slate-900/50 backdrop-blur-sm border-r border-purple-500/30 p-4 overflow-y-auto hidden lg:block">
          <div className="space-y-4">
            {/* 玩家状态卡片 */}
            <Card className="bg-slate-800/50 border-purple-500/30">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg text-white">角色状态</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* HP */}
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <div className="flex items-center gap-2 text-red-400">
                      <Heart className="w-4 h-4" />
                      <span>生命值</span>
                    </div>
                    <span className="text-white font-medium">
                      {gameState?.player?.hp || 0}/{gameState?.player?.maxHp || 0}
                    </span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-red-500 to-red-400 transition-all"
                      style={{
                        width: `${((gameState?.player?.hp || 0) / (gameState?.player?.maxHp || 1)) * 100}%`,
                      }}
                    />
                  </div>
                </div>

                {/* 体力 */}
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <div className="flex items-center gap-2 text-blue-400">
                      <Zap className="w-4 h-4" />
                      <span>体力</span>
                    </div>
                    <span className="text-white font-medium">
                      {gameState?.player?.stamina || 0}/{gameState?.player?.maxStamina || 0}
                    </span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all"
                      style={{
                        width: `${((gameState?.player?.stamina || 0) / (gameState?.player?.maxStamina || 1)) * 100}%`,
                      }}
                    />
                  </div>
                </div>

                {/* 金币 */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-700">
                  <div className="flex items-center gap-2 text-yellow-400">
                    <Coins className="w-4 h-4" />
                    <span className="text-sm">金币</span>
                  </div>
                  <span className="text-white font-medium">
                    {gameState?.player?.inventory?.find((i: any) => i.id === "gold_coin")?.quantity || 0}
                  </span>
                </div>

                {/* 特质 */}
                {gameState?.player?.traits && gameState.player.traits.length > 0 && (
                  <div className="pt-2 border-t border-slate-700">
                    <div className="text-sm text-gray-400 mb-2">特质</div>
                    <div className="flex flex-wrap gap-2">
                      {gameState.player.traits.map((trait: string, i: number) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-purple-500/20 text-purple-300 text-xs rounded-md border border-purple-500/30"
                        >
                          {trait}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 背包 */}
            <Card className="bg-slate-800/50 border-purple-500/30">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg text-white">背包</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {gameState?.player?.inventory && gameState.player.inventory.length > 0 ? (
                    gameState.player.inventory.map((item: any, i: number) => (
                      <div
                        key={i}
                        className="flex items-center justify-between p-2 bg-slate-700/50 rounded-lg"
                      >
                        <div className="flex-1">
                          <div className="text-sm text-white">{item.name}</div>
                          {item.description && (
                            <div className="text-xs text-gray-400">{item.description}</div>
                          )}
                        </div>
                        <div className="text-sm text-gray-300">×{item.quantity}</div>
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-gray-500 text-center py-4">背包为空</div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </aside>

        {/* 中间主要内容 - DM 界面 */}
        <main className="flex-1 overflow-hidden">
          <DmInterface sessionId={sessionId} className="h-full border-0 rounded-none" />
        </main>

        {/* 右侧边栏 - 任务 */}
        <aside className="w-96 bg-slate-900/50 backdrop-blur-sm border-l border-purple-500/30 overflow-hidden hidden xl:flex flex-col">
          <div className="flex-1 min-h-0">
            <QuestTracker className="h-full border-0 rounded-none" />
          </div>
        </aside>
      </div>
    </div>
  )
}
