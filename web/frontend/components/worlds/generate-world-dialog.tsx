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
    pacing_preset: "balanced", // 节奏预设
    writing_style_preset: "modern_literary", // 文风预设
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

            {/* 节奏调控 */}
            <div className="space-y-2">
              <Label htmlFor="pacing" className="text-gray-300">
                叙事节奏 ⚡
              </Label>
              <Select
                value={formData.pacing_preset}
                onValueChange={(value) =>
                  setFormData({ ...formData, pacing_preset: value })
                }
              >
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="balanced">平衡节奏（推荐）</SelectItem>
                  <SelectItem value="action">动作快节奏</SelectItem>
                  <SelectItem value="epic">史诗节奏</SelectItem>
                  <SelectItem value="literary">文学慢节奏</SelectItem>
                  <SelectItem value="horror">恐怖悬疑</SelectItem>
                  <SelectItem value="detective">推理节奏</SelectItem>
                  <SelectItem value="slice_of_life">日常节奏</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* 文风选择 */}
            <div className="space-y-2">
              <Label htmlFor="writing_style" className="text-gray-300">
                写作文风 ✍️
              </Label>
              <Select
                value={formData.writing_style_preset}
                onValueChange={(value) =>
                  setFormData({ ...formData, writing_style_preset: value })
                }
              >
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="web_novel_cool">
                    <div className="flex flex-col">
                      <span className="font-medium">🔥 网文爽文</span>
                      <span className="text-xs text-gray-400">装逼打脸、爽点密集、四字成语多</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="web_novel_warm">
                    <div className="flex flex-col">
                      <span className="font-medium">☀️ 网文温情</span>
                      <span className="text-xs text-gray-400">温馨日常、对话丰富、第一人称</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="web_novel_dark">
                    <div className="flex flex-col">
                      <span className="font-medium">🌑 网文黑暗</span>
                      <span className="text-xs text-gray-400">阴暗压抑、写实残酷、镜头感强</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="classical_elegant">
                    <div className="flex flex-col">
                      <span className="font-medium">📜 古典雅致</span>
                      <span className="text-xs text-gray-400">文言白话、典雅庄重、使用典故</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="archaic_vernacular">
                    <div className="flex flex-col">
                      <span className="font-medium">🏛️ 古风白话</span>
                      <span className="text-xs text-gray-400">古风韵味、易读易懂、四字词多</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="modern_literary">
                    <div className="flex flex-col">
                      <span className="font-medium">📖 现代文学（默认）</span>
                      <span className="text-xs text-gray-400">现代白话、文学性强、适合大众</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="poetic_beauty">
                    <div className="flex flex-col">
                      <span className="font-medium">🌸 诗意优美</span>
                      <span className="text-xs text-gray-400">诗化语言、意境悠远、美感十足</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="cinematic_thriller">
                    <div className="flex flex-col">
                      <span className="font-medium">🎬 镜头感惊悚</span>
                      <span className="text-xs text-gray-400">画面感强、极简风格、镜头语言</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="vernacular_humorous">
                    <div className="flex flex-col">
                      <span className="font-medium">😄 口语化幽默</span>
                      <span className="text-xs text-gray-400">口语表达、幽默诙谐、接地气</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500">
                💡 文风控制用词、句式、修辞手法等，决定叙述风格
              </p>
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
              <div className="surface-card border-l-2 border-red-500/60 rounded p-3 text-red-400 text-sm">
                {status.error}
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
