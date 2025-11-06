"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Save,
  Trash2,
  Play,
  Clock,
  MapPin,
  Heart,
  TrendingUp,
  ArrowLeft,
  Loader2,
  Download,
  AlertTriangle
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api-client"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface SaveMetadata {
  turn_number: number
  playtime: number
  location: string
  level: number
  hp: number
  max_hp: number
}

interface GameSave {
  save_id: number
  slot_id: number
  save_name: string
  metadata: SaveMetadata
  screenshot_url?: string
  created_at: string
  updated_at: string
}

export default function SavesPage() {
  const router = useRouter()
  const [saves, setSaves] = useState<GameSave[]>([])
  const [loading, setLoading] = useState(true)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [saveToDelete, setSaveToDelete] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)
  const userId = "default_user"

  useEffect(() => {
    loadSaves()
  }, [])

  const loadSaves = async () => {
    try {
      setLoading(true)
      console.log("[SavesPage] 开始加载存档, userId:", userId)
      const response = await apiClient.getSaves(userId)
      console.log("[SavesPage] API 返回:", response)
      console.log("[SavesPage] 存档数量:", response.saves?.length || 0)
      setSaves(response.saves)
      console.log("[SavesPage] 状态已更新")
    } catch (error) {
      console.error("[SavesPage] 加载存档失败:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleLoadSave = async (saveId: number) => {
    try {
      // 加载存档并跳转到游戏页面
      const response = await apiClient.loadSave(saveId)

      if (response.success && response.game_state) {
        // 将存档数据存储到 localStorage
        localStorage.setItem('loadedGameState', JSON.stringify(response.game_state))

        // 跳转到游戏页面
        router.push('/game/play')
      }
    } catch (error) {
      console.error("加载存档失败:", error)
      alert("加载存档失败，请重试")
    }
  }

  const handleDeleteSave = async () => {
    if (!saveToDelete) return

    try {
      setDeleting(true)
      const response = await apiClient.deleteSave(saveToDelete)

      if (response.success) {
        // 从列表中移除
        setSaves(saves.filter(s => s.save_id !== saveToDelete))
        setDeleteDialogOpen(false)
        setSaveToDelete(null)
      }
    } catch (error) {
      console.error("删除存档失败:", error)
      alert("删除存档失败，请重试")
    } finally {
      setDeleting(false)
    }
  }

  const confirmDelete = (saveId: number) => {
    setSaveToDelete(saveId)
    setDeleteDialogOpen(true)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatPlaytime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (hours > 0) {
      return `${hours}小时${minutes}分钟`
    }
    return `${minutes}分钟`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 text-purple-400 animate-spin mx-auto" />
          <p className="text-gray-300">加载存档中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* 头部 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push('/')}
              className="text-gray-300 hover:text-white"
            >
              <ArrowLeft className="w-6 h-6" />
            </Button>
            <div>
              <h1 className="text-4xl font-bold text-white">游戏存档</h1>
              <p className="text-gray-400 mt-1">管理你的冒险进度</p>
            </div>
          </div>

          <div className="text-sm text-gray-400">
            {saves.length} / 10 存档槽位
          </div>
        </div>

        {/* 存档列表 */}
        {saves.length === 0 ? (
          <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur">
            <CardContent className="py-16 text-center">
              <Save className="w-16 h-16 text-gray-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-300 mb-2">还没有存档</h3>
              <p className="text-gray-500 mb-6">开始游戏后，系统会自动保存你的进度</p>
              <Button
                onClick={() => router.push('/game/play')}
                className="bg-purple-600 hover:bg-purple-700"
              >
                <Play className="w-4 h-4 mr-2" />
                开始新游戏
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {saves.map((save) => (
              <Card
                key={save.save_id}
                className="bg-slate-800/50 border-slate-700/50 hover:border-purple-500/50 transition-all backdrop-blur group"
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-xl text-white mb-1">
                        {save.save_name}
                      </CardTitle>
                      <CardDescription className="text-gray-400">
                        槽位 {save.slot_id}
                      </CardDescription>
                    </div>
                    <Badge
                      variant="outline"
                      className="bg-purple-500/20 text-purple-300 border-purple-500/30"
                    >
                      Lv.{save.metadata.level || 1}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* 截图区域 */}
                  {save.screenshot_url ? (
                    <div className="aspect-video bg-slate-700/50 rounded-lg overflow-hidden">
                      <img
                        src={save.screenshot_url}
                        alt="存档截图"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ) : (
                    <div className="aspect-video bg-gradient-to-br from-slate-700/50 to-slate-800/50 rounded-lg flex items-center justify-center">
                      <MapPin className="w-12 h-12 text-gray-600" />
                    </div>
                  )}

                  {/* 元数据 */}
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-gray-300">
                      <MapPin className="w-4 h-4 text-purple-400" />
                      <span>{save.metadata.location || "未知位置"}</span>
                    </div>

                    <div className="flex items-center gap-2 text-gray-300">
                      <Heart className="w-4 h-4 text-red-400" />
                      <span>{save.metadata.hp || 100} / {save.metadata.max_hp || 100} HP</span>
                    </div>

                    <div className="flex items-center gap-2 text-gray-300">
                      <TrendingUp className="w-4 h-4 text-green-400" />
                      <span>第 {save.metadata.turn_number || 0} 回合</span>
                    </div>

                    <div className="flex items-center gap-2 text-gray-300">
                      <Clock className="w-4 h-4 text-blue-400" />
                      <span>{formatPlaytime(save.metadata.playtime || 0)}</span>
                    </div>
                  </div>

                  {/* 时间信息 */}
                  <div className="pt-3 border-t border-slate-700/50 text-xs text-gray-500">
                    <div>创建: {formatDate(save.created_at)}</div>
                    <div>更新: {formatDate(save.updated_at)}</div>
                  </div>

                  {/* 操作按钮 */}
                  <div className="flex gap-2 pt-2">
                    <Button
                      onClick={() => handleLoadSave(save.save_id)}
                      className="flex-1 bg-purple-600 hover:bg-purple-700"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      加载
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => confirmDelete(save.save_id)}
                      className="border-red-500/30 hover:bg-red-500/20 hover:border-red-500/50"
                    >
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* 提示区域 */}
        {saves.length > 0 && saves.length >= 10 && (
          <Card className="bg-amber-500/10 border-amber-500/30 backdrop-blur">
            <CardContent className="py-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5" />
                <div>
                  <h4 className="text-amber-300 font-medium">存档槽位已满</h4>
                  <p className="text-amber-200/70 text-sm mt-1">
                    你已经使用了所有10个存档槽位。如需保存新游戏，请先删除一些旧存档。
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 删除确认对话框 */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">确认删除存档</DialogTitle>
            <DialogDescription className="text-gray-400">
              此操作无法撤销。存档数据将永久删除。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={deleting}
              className="bg-slate-700 hover:bg-slate-600 text-white border-slate-600"
            >
              取消
            </Button>
            <Button
              onClick={handleDeleteSave}
              disabled={deleting}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {deleting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  删除中...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  确认删除
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
