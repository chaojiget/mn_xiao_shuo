"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ArrowLeft, CheckCircle, AlertTriangle, Download, Upload, Play } from "lucide-react"
import { WorldOverview } from "@/components/worlds/world-overview"
import { LocationsList } from "@/components/worlds/locations-list"
import { NpcsList } from "@/components/worlds/npcs-list"
import { QuestsList } from "@/components/worlds/quests-list"
import { LoreViewer } from "@/components/worlds/lore-viewer"

interface WorldPack {
  meta: {
    id: string
    title: string
    seed: number
    tone: string
    difficulty: string
    created_at: string
  }
  locations: any[]
  npcs: any[]
  quests: any[]
  loot_tables: any[]
  encounter_tables: any[]
  lore: Record<string, string>
  index_version: number
}

export default function WorldDetailPage() {
  const params = useParams()
  const router = useRouter()
  const worldId = params.id as string

  const [world, setWorld] = useState<WorldPack | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [validating, setValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<any>(null)

  useEffect(() => {
    loadWorld()
  }, [worldId])

  const loadWorld = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/worlds/${worldId}`)
      if (!response.ok) {
        throw new Error("加载世界失败")
      }
      const data = await response.json()
      setWorld(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知错误")
    } finally {
      setLoading(false)
    }
  }

  const handleValidate = async () => {
    try {
      setValidating(true)
      const response = await fetch(`/api/worlds/${worldId}/validate`, {
        method: "POST",
      })
      if (!response.ok) {
        throw new Error("校验失败")
      }
      const result = await response.json()
      setValidationResult(result)
    } catch (err) {
      console.error("校验失败:", err)
    } finally {
      setValidating(false)
    }
  }

  const handlePublish = async () => {
    try {
      const response = await fetch(`/api/worlds/${worldId}/publish`, {
        method: "POST",
      })
      if (!response.ok) {
        throw new Error("发布失败")
      }
      await loadWorld()
    } catch (err) {
      console.error("发布失败:", err)
    }
  }

  const handleSnapshot = async () => {
    try {
      const tag = prompt("快照标签:", `v${Date.now()}`)
      if (!tag) return

      const response = await fetch(`/api/worlds/${worldId}/snapshot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tag }),
      })
      if (!response.ok) {
        throw new Error("创建快照失败")
      }
      alert("快照创建成功")
    } catch (err) {
      console.error("创建快照失败:", err)
    }
  }

  const handleStartAdventure = async () => {
    try {
      // 检查是否有自动保存
      const autoSaveResponse = await fetch("/api/game/saves/auto")
      if (autoSaveResponse.ok) {
        const autoSaveData = await autoSaveResponse.json()

        if (autoSaveData.success && autoSaveData.game_state) {
          const savedWorldId = autoSaveData.game_state.metadata?.worldPackId

          // 如果保存的世界与当前世界相同
          if (savedWorldId === worldId) {
            const shouldContinue = confirm(
              `检测到该世界的游戏进度（第 ${autoSaveData.game_state.turn_number || 0} 回合）。\n\n` +
              `点击"确定"继续游戏\n` +
              `点击"取消"重新开始`
            )

            if (shouldContinue) {
              // 继续游戏，不带reset参数
              router.push(`/game/play?worldId=${worldId}`)
            } else {
              // 重新开始，带reset参数
              router.push(`/game/play?worldId=${worldId}&reset=true`)
            }
            return
          }
        }
      }

      // 没有自动保存或不同世界，直接开始
      router.push(`/game/play?worldId=${worldId}`)
    } catch (err) {
      console.error("开始冒险失败:", err)
      // 发生错误时也尝试直接跳转
      router.push(`/game/play?worldId=${worldId}`)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white">加载中...</div>
      </div>
    )
  }

  if (error || !world) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-red-400">错误: {error || "世界不存在"}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => router.push("/worlds")}
            className="mb-4 text-gray-300 hover:text-white"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回列表
          </Button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">{world.meta.title}</h1>
              <p className="text-gray-400 mt-2">
                种子: {world.meta.seed} | 基调: {world.meta.tone} | 难度:{" "}
                {world.meta.difficulty}
              </p>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleStartAdventure}
                size="lg"
                className="bg-purple-600 hover:bg-purple-700"
              >
                <Play className="mr-2 h-5 w-5" />
                开始冒险
              </Button>
              <Button
                variant="outline"
                onClick={handleValidate}
                disabled={validating}
              >
                {validating ? "校验中..." : "校验世界"}
              </Button>
              <Button variant="outline" onClick={handleSnapshot}>
                <Download className="mr-2 h-4 w-4" />
                创建快照
              </Button>
              <Button
                onClick={handlePublish}
                className="bg-green-600 hover:bg-green-700"
              >
                <Upload className="mr-2 h-4 w-4" />
                发布
              </Button>
            </div>
          </div>

          {/* Validation Result */}
          {validationResult && (
            <div className="mt-4">
              {validationResult.ok ? (
                <div className="bg-green-900/20 border border-green-500 rounded-lg p-4 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-green-400">
                    世界校验通过！无错误。
                  </span>
                </div>
              ) : (
                <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="h-5 w-5 text-red-500" />
                    <span className="text-red-400 font-medium">
                      发现 {validationResult.summary.total} 个问题
                    </span>
                  </div>
                  <ul className="text-sm text-red-300 space-y-1 ml-7">
                    {validationResult.problems.slice(0, 5).map((p: any, i: number) => (
                      <li key={i}>
                        [{p.severity}] {p.message}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Content Tabs */}
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="bg-slate-800 border-slate-700">
            <TabsTrigger value="overview">概览</TabsTrigger>
            <TabsTrigger value="locations">
              地点 ({world.locations.length})
            </TabsTrigger>
            <TabsTrigger value="npcs">NPC ({world.npcs.length})</TabsTrigger>
            <TabsTrigger value="quests">
              任务 ({world.quests.length})
            </TabsTrigger>
            <TabsTrigger value="lore">
              Lore ({Object.keys(world.lore).length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <WorldOverview world={world} />
          </TabsContent>

          <TabsContent value="locations">
            <LocationsList locations={world.locations} />
          </TabsContent>

          <TabsContent value="npcs">
            <NpcsList npcs={world.npcs} locations={world.locations} />
          </TabsContent>

          <TabsContent value="quests">
            <QuestsList quests={world.quests} />
          </TabsContent>

          <TabsContent value="lore">
            <LoreViewer lore={world.lore} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
