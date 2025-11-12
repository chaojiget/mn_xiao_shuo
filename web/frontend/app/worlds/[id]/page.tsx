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
import { LoreEditorDialog } from "@/components/worlds/lore-editor"
import { apiClient } from "@/lib/api-client"
import { useToast } from "@/hooks/use-toast"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "@/components/ui/select"

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
  const { toast } = useToast()

  const [world, setWorld] = useState<WorldPack | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [validating, setValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<any>(null)
  const [editOpen, setEditOpen] = useState(false)
  const [formTitle, setFormTitle] = useState("")
  const [formTone, setFormTone] = useState("epic")
  const [formDifficulty, setFormDifficulty] = useState("normal")
  const [editLoreOpen, setEditLoreOpen] = useState(false)

  useEffect(() => {
    loadWorld()
  }, [worldId])

  const loadWorld = async () => {
    try {
      setLoading(true)
      const data = await apiClient.request<any>(`/api/worlds/${worldId}`)
      setWorld(data)
      // 预填编辑表单
      try {
        setFormTitle(data?.meta?.title || "")
        setFormTone(data?.meta?.tone || "epic")
        setFormDifficulty(data?.meta?.difficulty || "normal")
      } catch {}
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知错误")
    } finally {
      setLoading(false)
    }
  }

  const handleValidate = async () => {
    try {
      setValidating(true)
      const result = await apiClient.request<any>(`/api/worlds/${worldId}/validate`, { method: "POST" })
      setValidationResult(result)
      // toast 反馈
      if (result?.ok) {
        toast({ title: "世界校验通过", description: "未发现问题" })
      } else if (result?.summary?.total) {
        toast({ title: `发现 ${result.summary.total} 个问题`, description: "请查看问题列表", variant: "destructive" })
      }
    } catch (err) {
      console.error("校验失败:", err)
      toast({ title: "校验失败", description: String(err), variant: "destructive" })
    } finally {
      setValidating(false)
    }
  }

  const handlePublish = async () => {
    try {
      const response = await apiClient.request<any>(`/api/worlds/${worldId}/publish`, { method: "POST" })
      await loadWorld()
      toast({ title: "发布成功", description: "该世界已设为默认世界" })
    } catch (err) {
      console.error("发布失败:", err)
      toast({ title: "发布失败", description: String(err), variant: "destructive" })
    }
  }

  const handleSnapshot = async () => {
    try {
      const tag = prompt("快照标签:", `v${Date.now()}`)
      if (!tag) return

      await apiClient.request<any>(`/api/worlds/${worldId}/snapshot`, {
        method: "POST",
        body: JSON.stringify({ tag }),
      })
      toast({ title: "快照创建成功", description: `标签: ${tag}` })
    } catch (err) {
      console.error("创建快照失败:", err)
      toast({ title: "创建快照失败", description: String(err), variant: "destructive" })
    }
  }

  const handleOpenEdit = () => {
    if (!world) return
    setFormTitle(world.meta?.title || "")
    setFormTone(world.meta?.tone || "epic")
    setFormDifficulty(world.meta?.difficulty || "normal")
    setEditOpen(true)
  }

  const handleSaveEdit = async () => {
    try {
      const resp = await apiClient.request<any>(`/api/worlds/${worldId}/meta`, {
        method: "PATCH",
        body: JSON.stringify({
          title: formTitle,
          tone: formTone,
          difficulty: formDifficulty,
        }),
      })
      if (resp?.success) {
        toast({ title: "保存成功", description: "世界信息已更新" })
        await loadWorld()
        setEditOpen(false)
      }
    } catch (e) {
      toast({ title: "保存失败", description: String(e), variant: "destructive" })
    }
  }

  const handleStartAdventure = async () => {
    try {
      // 统一使用 apiClient 获取自动保存
      const autoSaveData = await apiClient.getLatestAutoSave()
      if (autoSaveData.success && autoSaveData.game_state) {
        const savedWorldId = autoSaveData.game_state.metadata?.worldPackId
        if (savedWorldId === worldId) {
          const shouldContinue = confirm(
            `检测到该世界的游戏进度（第 ${autoSaveData.game_state.turn_number || 0} 回合）。\n\n` +
            `点击"确定"继续游戏\n` +
            `点击"取消"重新开始`
          )

          if (shouldContinue) {
            router.push(`/game/play?worldId=${worldId}`)
          } else {
            router.push(`/game/play?worldId=${worldId}&reset=true`)
          }
          return
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
      <div className="min-h-screen app-gradient flex items-center justify-center">
        <div className="text-white">加载中...</div>
      </div>
    )
  }

  if (error || !world) {
    return (
      <div className="min-h-screen app-gradient flex items-center justify-center">
        <div className="text-red-400">错误: {error || "世界不存在"}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen app-gradient pt-16 px-4 md:px-6 pb-8">
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
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline">更多操作</Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={handleOpenEdit}>编辑世界信息</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleValidate} disabled={validating}>
                    {validating ? "校验中..." : "校验世界"}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleSnapshot}>
                    创建快照
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handlePublish}>
                    发布
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Validation Result */}
          {validationResult && (
            <div className="mt-4">
              {validationResult.ok ? (
                <div className="surface-card border-l-2 border-green-500/60 rounded-lg p-4 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-green-400">
                    世界校验通过！无错误。
                  </span>
                </div>
              ) : (
                <div className="surface-card border-l-2 border-red-500/60 rounded-lg p-4">
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
          <TabsList className="bg-slate-800 border-slate-700 overflow-x-auto no-scrollbar -mx-1 px-1">
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
            <div className="flex items-center justify-between mb-3">
              <div className="text-gray-400 text-sm">共 {Object.keys(world.lore || {}).length} 条设定</div>
              <Button size="sm" variant="outline" onClick={() => setEditLoreOpen(true)}>编辑设定</Button>
            </div>
            <LoreViewer lore={world.lore} />
            <LoreEditorDialog
              open={editLoreOpen}
              onOpenChange={setEditLoreOpen}
              worldId={worldId}
              lore={world.lore}
              onSaved={loadWorld}
            />
          </TabsContent>
        </Tabs>

        {/* 编辑世界信息对话框 */}
        <Dialog open={editOpen} onOpenChange={setEditOpen}>
          <DialogContent className="bg-slate-800 border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-white">编辑世界信息</DialogTitle>
              <DialogDescription className="text-gray-400">修改标题、基调与难度</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label className="text-gray-300">标题</Label>
                <Input value={formTitle} onChange={(e) => setFormTitle(e.target.value)} className="bg-slate-700 border-slate-600 text-white" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-gray-300">基调</Label>
                  <Select value={formTone} onValueChange={setFormTone}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="epic">史诗</SelectItem>
                      <SelectItem value="dark">黑暗</SelectItem>
                      <SelectItem value="cozy">温馨</SelectItem>
                      <SelectItem value="mystery">神秘</SelectItem>
                      <SelectItem value="whimsical">奇幻</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-300">难度</Label>
                  <Select value={formDifficulty} onValueChange={setFormDifficulty}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="story">故事模式</SelectItem>
                      <SelectItem value="normal">普通</SelectItem>
                      <SelectItem value="hard">困难</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setEditOpen(false)}>
                取消
              </Button>
              <Button onClick={handleSaveEdit} className="bg-purple-600 hover:bg-purple-700">
                保存
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
