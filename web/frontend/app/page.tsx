"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Sparkles, Play, Map, ArrowRight, Globe, Save, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { apiClient } from "@/lib/api-client"

export default function Home() {
  const router = useRouter()
  const [hasAutoSave, setHasAutoSave] = useState(false)
  const [autoTurn, setAutoTurn] = useState<number | null>(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    const checkAuto = async () => {
      try {
        const res = await apiClient.getLatestAutoSave()
        if (res.success && res.game_state) {
          setHasAutoSave(true)
          setAutoTurn(res.game_state.turn_number || res.turn_number || 0)
        } else {
          setHasAutoSave(false)
        }
      } catch (e) {
        setHasAutoSave(false)
      } finally {
        setChecking(false)
      }
    }
    checkAuto()
  }, [])

  return (
    <main className="min-h-screen app-gradient flex items-center justify-center pt-16 px-4 md:px-6 pb-8">
      <div className="max-w-4xl w-full space-y-12">
        {/* 顶部继续上次提示 */}
        {!checking && hasAutoSave && (
          <Card className="surface-card">
            <CardContent className="py-3 px-4 flex items-center justify-between">
              <div className="flex items-center gap-3 text-gray-200">
                <Clock className="w-4 h-4 text-purple-300" />
                <span>
                  继续上次游戏 · 第 {autoTurn ?? 0} 回合
                </span>
              </div>
              <Button
                size="sm"
                className="bg-purple-600 hover:bg-purple-700"
                onClick={() => router.push("/game/play")}
              >
                一键进入
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        )}
        {/* Logo与标题 */}
        <div className="text-center space-y-6">
          <div className="w-24 h-24 bg-gradient-to-br from-purple-500 to-pink-600 rounded-3xl flex items-center justify-center mx-auto shadow-2xl">
            <Globe className="w-12 h-12 text-white" />
          </div>
          <div>
            <h1 className="text-6xl font-bold tracking-tight mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI 世界生成器
            </h1>
            <p className="text-xl text-gray-300">
              预生成完整世界 · 冒险体验
            </p>
          </div>
        </div>

        {/* 主要功能卡片 */}
        <div className="grid md:grid-cols-3 gap-6">
          <Card
            className="surface-card surface-card-hover transition-all cursor-pointer group"
            onClick={() => router.push("/worlds")}
          >
            <CardContent className="pt-8 pb-8">
              <div className="space-y-4">
                <div className="w-16 h-16 bg-purple-500/20 rounded-2xl flex items-center justify-center group-hover:bg-purple-500/30 transition-colors">
                  <Map className="w-8 h-8 text-purple-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">世界管理</h3>
                  <p className="text-gray-400">
                    生成和管理预构建的游戏世界，包含地点、NPC、任务等
                  </p>
                </div>
                <div className="flex items-center text-purple-400 group-hover:text-purple-300">
                  <span className="font-medium">浏览世界</span>
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card
            className="surface-card surface-card-hover transition-all cursor-pointer group"
            onClick={() => router.push("/game/play")}
          >
            <CardContent className="pt-8 pb-8">
              <div className="space-y-4">
                <div className="w-16 h-16 bg-pink-500/20 rounded-2xl flex items-center justify-center group-hover:bg-pink-500/30 transition-colors">
                  <Play className="w-8 h-8 text-pink-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">开始冒险</h3>
                  <p className="text-gray-400">
                    探索动态世界，由叙事引擎驱动的沉浸式故事
                  </p>
                </div>
                <div className="flex items-center text-pink-400 group-hover:text-pink-300">
                  <span className="font-medium">进入游戏</span>
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card
            className="surface-card surface-card-hover transition-all cursor-pointer group"
            onClick={() => router.push("/saves")}
          >
            <CardContent className="pt-8 pb-8">
              <div className="space-y-4">
                <div className="w-16 h-16 bg-blue-500/20 rounded-2xl flex items-center justify-center group-hover:bg-blue-500/30 transition-colors">
                  <Save className="w-8 h-8 text-blue-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">存档管理</h3>
                  <p className="text-gray-400">
                    查看和管理游戏存档，加载之前的冒险进度
                  </p>
                </div>
                <div className="flex items-center text-blue-400 group-hover:text-blue-300">
                  <span className="font-medium">查看存档</span>
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 核心特性 */}
        <Card className="surface-card">
          <CardContent className="pt-6 pb-6">
            <div className="grid md:grid-cols-3 gap-6 text-sm">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-400" />
                  <span className="font-medium text-white">AI世界生成</span>
                </div>
                <p className="text-gray-400 text-xs">
                  自动生成地点、NPC、任务、战利品、遭遇表等完整世界内容
                </p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-pink-400" />
                  <span className="font-medium text-white">动态叙事引擎</span>
                </div>
                <p className="text-gray-400 text-xs">
                  叙事引擎动态响应玩家行动，创造独特的故事体验
                </p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-blue-400" />
                  <span className="font-medium text-white">进度管理</span>
                </div>
                <p className="text-gray-400 text-xs">
                  自动保存系统，支持多槽位存档，随时继续冒险
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 快速开始指南 */}
        <div className="text-center space-y-4">
          <h3 className="text-lg font-medium text-gray-300">快速开始</h3>
          <div className="flex flex-wrap justify-center gap-3 text-sm">
            <div className="px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700/50 text-gray-300">
              1️⃣ 生成或选择世界
            </div>
            <div className="px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700/50 text-gray-300">
              2️⃣ 点击"开始冒险"
            </div>
            <div className="px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700/50 text-gray-300">
              3️⃣ 通过提示与叙事引擎互动
          </div>
          </div>
          <Button
            size="lg"
            className="mt-6 text-lg px-8 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 shadow-xl"
            onClick={() => router.push(hasAutoSave ? "/game/play" : "/game/play?reset=true")}
          >
            {hasAutoSave ? "继续上次冒险" : "一键开始冒险"}
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>

        {/* 版本信息 */}
        <div className="text-center text-xs text-gray-500 space-y-1">
          <div>WorldPack v1.2 · 完整世界生成系统 · 2025-11-06</div>
          <div>后端: LangChain + OpenRouter · 前端: Next.js 14 + shadcn/ui</div>
        </div>
      </div>
    </main>
  )
}
