"use client"

import { useState } from "react"
import { Users, Sparkles, Eye, EyeOff, Heart, Trash2, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

interface NPCSeed {
  id: string
  archetype: string
  roleInStory: string
  status: "dormant" | "ready" | "instantiated"
  spawnConditions: string[]
  priority: number
}

interface NPCInstance {
  id: string
  name: string
  role: string
  archetype: string
  description: string
  lifecycleStage: "instantiated" | "engaged" | "adapted" | "retired"
  interactionCount: number
  relationship: number  // -100 to 100
  currentLocation?: string
  faction?: string
}

interface NPCManagerProps {
  novelId: string
}

export function NPCManager({ novelId }: NPCManagerProps) {
  const [view, setView] = useState<"seeds" | "active" | "all">("active")

  // Mock data - 实际应从API获取
  const seeds: NPCSeed[] = [
    {
      id: "seed_1",
      archetype: "mentor",
      roleInStory: "神秘科学家",
      status: "ready",
      spawnConditions: ["主角到达实验室", "触发特定事件"],
      priority: 8
    },
    {
      id: "seed_2",
      archetype: "opponent",
      roleInStory: "敌对势力特工",
      status: "dormant",
      spawnConditions: ["完成第5章", "获得关键线索"],
      priority: 6
    }
  ]

  const activeNPCs: NPCInstance[] = [
    {
      id: "npc_1",
      name: "陈博士",
      role: "高级研究员",
      archetype: "mentor",
      description: "一位经验丰富的老科学家，知晓实验的真相",
      lifecycleStage: "engaged",
      interactionCount: 3,
      relationship: 45,
      currentLocation: "研究站Alpha",
      faction: "科学院"
    },
    {
      id: "npc_2",
      name: "艾莉娅",
      role: "飞行员",
      archetype: "companion",
      description: "技术精湛的太空飞行员，主角的可靠伙伴",
      lifecycleStage: "adapted",
      interactionCount: 7,
      relationship: 72,
      currentLocation: "主舰",
      faction: "联合殖民地"
    }
  ]

  const getArchetypeColor = (archetype: string) => {
    switch (archetype) {
      case "mentor":
        return "bg-blue-500"
      case "companion":
        return "bg-green-500"
      case "opponent":
        return "bg-red-500"
      case "neutral":
        return "bg-gray-500"
      default:
        return "bg-gray-500"
    }
  }

  const getStageColor = (stage: string) => {
    switch (stage) {
      case "instantiated":
        return "secondary"
      case "engaged":
        return "default"
      case "adapted":
        return "default"
      case "retired":
        return "outline"
      default:
        return "secondary"
    }
  }

  const getRelationshipColor = (value: number) => {
    if (value >= 70) return "text-green-600 dark:text-green-400"
    if (value >= 30) return "text-blue-600 dark:text-blue-400"
    if (value >= -30) return "text-gray-600 dark:text-gray-400"
    if (value >= -70) return "text-orange-600 dark:text-orange-400"
    return "text-red-600 dark:text-red-400"
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              NPC 管理
            </CardTitle>
            <CardDescription>
              管理NPC种子和活跃角色
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant={view === "seeds" ? "default" : "outline"}
              size="sm"
              onClick={() => setView("seeds")}
            >
              <EyeOff className="w-4 h-4 mr-2" />
              种子池 ({seeds.length})
            </Button>
            <Button
              variant={view === "active" ? "default" : "outline"}
              size="sm"
              onClick={() => setView("active")}
            >
              <Eye className="w-4 h-4 mr-2" />
              活跃NPC ({activeNPCs.length})
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* 种子池视图 */}
        {view === "seeds" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                NPC种子会在满足触发条件时自动生成。红色边框表示已就绪。
              </p>
              <Button size="sm" variant="outline">
                <Plus className="w-4 h-4 mr-2" />
                添加种子
              </Button>
            </div>

            {seeds.map((seed) => (
              <Card
                key={seed.id}
                className={seed.status === "ready" ? "border-red-500 border-2" : ""}
              >
                <CardContent className="pt-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${getArchetypeColor(seed.archetype)}`} />
                      <span className="font-medium">{seed.roleInStory}</span>
                      <Badge variant="outline">{seed.archetype}</Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={seed.status === "ready" ? "destructive" : "secondary"}>
                        {seed.status === "dormant" ? "休眠" : seed.status === "ready" ? "就绪" : "已生成"}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        优先级: {seed.priority}/10
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="text-sm font-medium">触发条件:</div>
                    <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1">
                      {seed.spawnConditions.map((condition, idx) => (
                        <li key={idx}>{condition}</li>
                      ))}
                    </ul>
                  </div>

                  {seed.status === "ready" && (
                    <Button size="sm" className="w-full">
                      <Sparkles className="w-4 h-4 mr-2" />
                      立即生成
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}

            {seeds.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                暂无NPC种子
              </div>
            )}
          </div>
        )}

        {/* 活跃NPC视图 */}
        {view === "active" && (
          <div className="space-y-4">
            {activeNPCs.map((npc) => (
              <Card key={npc.id}>
                <CardContent className="pt-6 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${getArchetypeColor(npc.archetype)}`} />
                        <span className="font-bold text-lg">{npc.name}</span>
                        <Badge variant="outline">{npc.role}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {npc.description}
                      </p>
                    </div>
                    <Badge variant={getStageColor(npc.lifecycleStage)}>
                      {npc.lifecycleStage === "instantiated" ? "已创建" :
                       npc.lifecycleStage === "engaged" ? "已互动" :
                       npc.lifecycleStage === "adapted" ? "已适应" : "已退出"}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="text-sm font-medium flex items-center gap-2">
                        <Heart className="w-4 h-4" />
                        关系值
                      </div>
                      <div className="space-y-1">
                        <Progress value={(npc.relationship + 100) / 2} className="h-2" />
                        <div className={`text-sm font-medium ${getRelationshipColor(npc.relationship)}`}>
                          {npc.relationship > 0 ? "+" : ""}{npc.relationship} / 100
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="text-sm font-medium">互动次数</div>
                      <div className="text-2xl font-bold">
                        {npc.interactionCount} 次
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {npc.currentLocation && (
                      <div>
                        <span className="text-muted-foreground">当前位置:</span>
                        <span className="ml-2 font-medium">{npc.currentLocation}</span>
                      </div>
                    )}
                    {npc.faction && (
                      <div>
                        <span className="text-muted-foreground">所属势力:</span>
                        <span className="ml-2 font-medium">{npc.faction}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" className="flex-1">
                      查看详情
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1">
                      编辑
                    </Button>
                    {npc.lifecycleStage !== "retired" && (
                      <Button size="sm" variant="destructive">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}

            {activeNPCs.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                暂无活跃NPC
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
