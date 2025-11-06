"use client"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"

interface GenerateWorldDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface GenerationStatus {
  phase: string
  progress: number
  error?: string
}

export function GenerateWorldDialog({
  open,
  onOpenChange,
}: GenerateWorldDialogProps) {
  const router = useRouter()
  const [formData, setFormData] = useState({
    title: "",
    tone: "epic",
    difficulty: "normal",
    num_locations: 10,
    num_npcs: 15,
    num_quests: 8,
  })

  const [generating, setGenerating] = useState(false)
  const [worldId, setWorldId] = useState<string | null>(null)
  const [status, setStatus] = useState<GenerationStatus | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      setGenerating(true)

      // 触发生成
      const response = await fetch("/api/worlds/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      })

      if (!response.ok) {
        throw new Error("生成请求失败")
      }

      const data = await response.json()
      setWorldId(data.world_id)

      // 轮询状态
      pollStatus(data.world_id)
    } catch (error) {
      console.error("生成失败:", error)
      setGenerating(false)
    }
  }

  const pollStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/worlds/${id}/status`)
        if (!response.ok) {
          throw new Error("查询状态失败")
        }

        const statusData = await response.json()
        setStatus({
          phase: statusData.phase,
          progress: statusData.progress,
          error: statusData.error,
        })

        // 生成完成
        if (statusData.phase === "READY") {
          clearInterval(interval)
          setTimeout(() => {
            onOpenChange(false)
            router.push(`/worlds/${id}`)
          }, 1000)
        }

        // 生成失败
        if (statusData.phase === "FAILED") {
          clearInterval(interval)
          setGenerating(false)
        }
      } catch (error) {
        console.error("查询状态失败:", error)
        clearInterval(interval)
        setGenerating(false)
      }
    }, 2000) // 每2秒查询一次
  }

  const getPhaseLabel = (phase: string) => {
    const labels: Record<string, string> = {
      QUEUED: "排队中",
      OUTLINE: "生成世界框架",
      LOCATIONS: "生成地点",
      NPCS: "生成NPC",
      QUESTS: "生成任务",
      LOOT_TABLES: "生成掉落表",
      ENCOUNTER_TABLES: "生成遭遇表",
      INDEXING: "构建索引",
      READY: "完成",
      FAILED: "失败",
    }
    return labels[phase] || phase
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] bg-slate-800 border-slate-700">
        <DialogHeader>
          <DialogTitle className="text-white">生成新世界</DialogTitle>
          <DialogDescription className="text-gray-400">
            配置世界参数并开始生成
          </DialogDescription>
        </DialogHeader>

        {!generating ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title" className="text-gray-300">
                世界标题
              </Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                placeholder="例如：魔法学院、末日废土"
                className="bg-slate-700 border-slate-600 text-white"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="tone" className="text-gray-300">
                  基调
                </Label>
                <Select
                  value={formData.tone}
                  onValueChange={(value) =>
                    setFormData({ ...formData, tone: value })
                  }
                >
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
                <Label htmlFor="difficulty" className="text-gray-300">
                  难度
                </Label>
                <Select
                  value={formData.difficulty}
                  onValueChange={(value) =>
                    setFormData({ ...formData, difficulty: value })
                  }
                >
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

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="num_locations" className="text-gray-300">
                  地点数
                </Label>
                <Input
                  id="num_locations"
                  type="number"
                  min="5"
                  max="50"
                  value={formData.num_locations}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      num_locations: parseInt(e.target.value),
                    })
                  }
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="num_npcs" className="text-gray-300">
                  NPC数
                </Label>
                <Input
                  id="num_npcs"
                  type="number"
                  min="3"
                  max="30"
                  value={formData.num_npcs}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      num_npcs: parseInt(e.target.value),
                    })
                  }
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="num_quests" className="text-gray-300">
                  任务数
                </Label>
                <Input
                  id="num_quests"
                  type="number"
                  min="3"
                  max="20"
                  value={formData.num_quests}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      num_quests: parseInt(e.target.value),
                    })
                  }
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <Button type="submit" className="bg-purple-600 hover:bg-purple-700">
                开始生成
              </Button>
            </div>
          </form>
        ) : (
          <div className="space-y-4 py-6">
            <div className="text-center space-y-2">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-purple-500" />
              <div className="text-white font-medium">
                {status ? getPhaseLabel(status.phase) : "初始化..."}
              </div>
            </div>

            {status && (
              <>
                <Progress value={status.progress * 100} className="h-2" />
                <div className="text-center text-sm text-gray-400">
                  {Math.round(status.progress * 100)}%
                </div>
              </>
            )}

            {status?.error && (
              <div className="bg-red-900/20 border border-red-500 rounded p-3 text-red-400 text-sm">
                {status.error}
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
