"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Eye, CheckCircle, Clock, AlertCircle, Trash2 } from "lucide-react"
import Link from "next/link"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { apiClient } from "@/lib/api-client"
import { useToast } from "@/hooks/use-toast"
import { Progress } from "@/components/ui/progress"

interface World {
  id: string
  title: string
  seed: number
  status: "draft" | "published" | "generating"
  created_at: string
}

export function WorldsList() {
  const [worlds, setWorlds] = useState<World[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [targetWorld, setTargetWorld] = useState<World | null>(null)
  const { toast } = useToast()
  const [statusMap, setStatusMap] = useState<Record<string, { phase: string; progress: number; error?: string }>>({})

  useEffect(() => {
    loadWorlds()
  }, [])

  const loadWorlds = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getWorlds()
      setWorlds(data.worlds || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知错误")
    } finally {
      setLoading(false)
    }
  }

  // 轮询生成中的世界进度
  useEffect(() => {
    const generatingIds = worlds.filter(w => w.status === 'generating').map(w => w.id)
    if (generatingIds.length === 0) return

    let active = true
    const tick = async () => {
      for (const id of generatingIds) {
        try {
          const s = await apiClient.request<any>(`/api/worlds/${id}/status`)
          if (!active) return
          setStatusMap(prev => ({ ...prev, [id]: { phase: s.phase, progress: s.progress, error: s.error } }))
          if (s.phase === 'READY') {
            // 刷新列表，显示最新状态
            loadWorlds()
          }
        } catch (e) {
          // 忽略单次错误
        }
      }
    }
    const timer = setInterval(tick, 2000)
    tick()
    return () => { active = false; clearInterval(timer) }
  }, [worlds])

  const getPhaseLabel = (phase?: string) => {
    const labels: Record<string, string> = {
      QUEUED: '排队中',
      OUTLINE: '生成世界框架',
      LOCATIONS: '生成地点',
      NPCS: '生成NPC',
      QUESTS: '生成任务',
      LOOT_TABLES: '生成掉落表',
      ENCOUNTER_TABLES: '生成遭遇表',
      INDEXING: '构建索引',
      READY: '完成',
      FAILED: '失败',
    }
    return (phase && labels[phase]) || '生成中'
  }

  const confirmDelete = (world: World) => {
    setTargetWorld(world)
    setDeleteOpen(true)
  }

  const handleDelete = async () => {
    if (!targetWorld) return
    try {
      setDeleting(true)
      const resp = await apiClient.deleteWorld(targetWorld.id)
      if (!resp.success) {
        throw new Error(resp.message || '删除失败')
      }
      setWorlds(prev => prev.filter(w => w.id !== targetWorld.id))
      setDeleteOpen(false)
      setTargetWorld(null)
    } catch (e) {
      toast({ title: '删除失败', description: (e as Error).message || '删除失败', variant: 'destructive' })
    } finally {
      setDeleting(false)
    }
  }

  const getStatusBadge = (status: World["status"]) => {
    switch (status) {
      case "published":
        return (
          <Badge className="bg-green-600">
            <CheckCircle className="mr-1 h-3 w-3" />
            已发布
          </Badge>
        )
      case "generating":
        return (
          <Badge className="bg-yellow-600">
            <Clock className="mr-1 h-3 w-3" />
            生成中
          </Badge>
        )
      case "draft":
        return (
          <Badge variant="secondary">
            <AlertCircle className="mr-1 h-3 w-3" />
            草稿
          </Badge>
        )
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-400">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-red-400">错误: {error}</div>
      </div>
    )
  }

  if (worlds.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="text-gray-400 text-lg mb-4">还没有世界</div>
        <p className="text-gray-500 text-sm">点击右上角"生成新世界"开始创建</p>
      </div>
    )
  }

  return (
    <>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {worlds.map((world) => (
        <Card
          key={world.id}
          className="surface-card surface-card-hover"
        >
          <CardHeader>
            <div className="flex items-start justify-between">
              <CardTitle className="text-white">{world.title}</CardTitle>
              {getStatusBadge(world.status)}
            </div>
            <CardDescription className="text-gray-400">
              种子: {world.seed}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-sm text-gray-400">
                创建时间: {formatDate(world.created_at)}
              </div>

              {world.status === 'generating' && (
                <div className="space-y-2">
                  <Progress value={Math.round((statusMap[world.id]?.progress || 0) * 100)} className="h-2" />
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span>{getPhaseLabel(statusMap[world.id]?.phase)}</span>
                    <span>{Math.round((statusMap[world.id]?.progress || 0) * 100)}%</span>
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                <Link href={`/worlds/${world.id}`} className="flex-1">
                  <Button variant="outline" className="w-full">
                    <Eye className="mr-2 h-4 w-4" />
                    查看详情
                  </Button>
                </Link>
                <Button
                  variant="outline"
                  size="icon"
                  className="text-red-400 hover:text-red-300"
                  onClick={() => confirmDelete(world)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>

    {/* 删除确认对话框 */}
    <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
      <DialogContent className="bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle className="text-white">确认删除</DialogTitle>
          <DialogDescription className="text-gray-400">
            此操作不可撤销。确定要删除世界“{targetWorld?.title}”吗？
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => setDeleteOpen(false)} disabled={deleting}>
            取消
          </Button>
          <Button className="bg-red-600 hover:bg-red-700" onClick={handleDelete} disabled={deleting}>
            {deleting ? '删除中…' : '确认删除'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </>
  )
}
