"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { MapPin, Users, Scroll, Package, Swords } from "lucide-react"

interface WorldOverviewProps {
  world: {
    meta: any
    locations: any[]
    npcs: any[]
    quests: any[]
    loot_tables: any[]
    encounter_tables: any[]
    lore: Record<string, string>
  }
}

export function WorldOverview({ world }: WorldOverviewProps) {
  const stats = [
    {
      icon: MapPin,
      label: "地点",
      value: world.locations.length,
      color: "text-blue-500",
    },
    {
      icon: Users,
      label: "NPC",
      value: world.npcs.length,
      color: "text-green-500",
    },
    {
      icon: Scroll,
      label: "任务",
      value: world.quests.length,
      color: "text-purple-500",
    },
    {
      icon: Package,
      label: "掉落表",
      value: world.loot_tables.length,
      color: "text-yellow-500",
    },
    {
      icon: Swords,
      label: "遭遇表",
      value: world.encounter_tables.length,
      color: "text-red-500",
    },
  ]

  const mainQuests = world.quests.filter((q) => q.line === "main")
  const sideQuests = world.quests.filter((q) => q.line === "side")

  const biomes = Array.from(
    new Set(world.locations.map((loc) => loc.biome))
  ).join(", ")

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {stats.map((stat) => (
          <Card
            key={stat.label}
            className="bg-slate-800/50 border-slate-700"
          >
            <CardContent className="p-6 flex items-center gap-4">
              <stat.icon className={`h-8 w-8 ${stat.color}`} />
              <div>
                <div className="text-2xl font-bold text-white">{stat.value}</div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">世界信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <span className="text-gray-400">基调:</span>
              <span className="ml-2 text-white capitalize">{world.meta.tone}</span>
            </div>
            <div>
              <span className="text-gray-400">难度:</span>
              <span className="ml-2 text-white capitalize">{world.meta.difficulty}</span>
            </div>
            <div>
              <span className="text-gray-400">种子:</span>
              <span className="ml-2 text-white">{world.meta.seed}</span>
            </div>
            <div>
              <span className="text-gray-400">生态类型:</span>
              <span className="ml-2 text-white">{biomes}</span>
            </div>
            <div>
              <span className="text-gray-400">索引版本:</span>
              <span className="ml-2 text-white">v{world.meta.index_version || 1}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">任务分布</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <span className="text-gray-400">主线任务:</span>
              <span className="ml-2 text-white">{mainQuests.length}</span>
            </div>
            <div>
              <span className="text-gray-400">支线任务:</span>
              <span className="ml-2 text-white">{sideQuests.length}</span>
            </div>
            <div>
              <span className="text-gray-400">总目标数:</span>
              <span className="ml-2 text-white">
                {world.quests.reduce((sum, q) => sum + (q.objectives?.length || 0), 0)}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lore Preview */}
      {Object.keys(world.lore).length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">世界Lore预览</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(world.lore).slice(0, 3).map(([key, value]) => (
              <div key={key}>
                <div className="text-sm font-medium text-purple-400 mb-1">
                  {key}
                </div>
                <div className="text-sm text-gray-300 line-clamp-3">{value}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
