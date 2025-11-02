"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { BookOpen, Sparkles, MessageSquare, Gamepad2, Map, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

export default function Home() {
  const router = useRouter()

  // 3秒后自动跳转到工作台
  useEffect(() => {
    const timer = setTimeout(() => {
      router.push("/workspace")
    }, 3000)

    return () => clearTimeout(timer)
  }, [router])

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full space-y-8">
        {/* Logo与标题 */}
        <div className="text-center space-y-4">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
            <BookOpen className="w-10 h-10 text-white" />
          </div>
          <div>
            <h1 className="text-5xl font-bold tracking-tight mb-2 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              AI 小说生成器
            </h1>
            <p className="text-xl text-muted-foreground">
              全局导演架构 · 智能叙事引擎 · 探索式世界观
            </p>
          </div>
        </div>

        {/* 功能特性网格 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="hover:shadow-lg transition-all cursor-pointer group">
            <CardContent className="pt-6 text-center">
              <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:bg-blue-500/20 transition-colors">
                <Sparkles className="w-6 h-6 text-blue-500" />
              </div>
              <div className="font-medium">小说创作</div>
              <div className="text-xs text-muted-foreground mt-1">AI辅助生成</div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-all cursor-pointer group">
            <CardContent className="pt-6 text-center">
              <div className="w-12 h-12 bg-green-500/10 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:bg-green-500/20 transition-colors">
                <MessageSquare className="w-6 h-6 text-green-500" />
              </div>
              <div className="font-medium">对话模式</div>
              <div className="text-xs text-muted-foreground mt-1">AI聊天创作</div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-all cursor-pointer group">
            <CardContent className="pt-6 text-center">
              <div className="w-12 h-12 bg-purple-500/10 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:bg-purple-500/20 transition-colors">
                <Gamepad2 className="w-6 h-6 text-purple-500" />
              </div>
              <div className="font-medium">游戏模式</div>
              <div className="text-xs text-muted-foreground mt-1">单人跑团</div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-all cursor-pointer group">
            <CardContent className="pt-6 text-center">
              <div className="w-12 h-12 bg-orange-500/10 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:bg-orange-500/20 transition-colors">
                <Map className="w-6 h-6 text-orange-500" />
              </div>
              <div className="font-medium">世界管理</div>
              <div className="text-xs text-muted-foreground mt-1">脚手架系统</div>
            </CardContent>
          </Card>
        </div>

        {/* 核心特性列表 */}
        <Card className="bg-card/50 backdrop-blur">
          <CardContent className="pt-6">
            <div className="grid md:grid-cols-3 gap-4 text-sm">
              <div>
                <div className="font-medium mb-1">✨ 可编辑设定</div>
                <div className="text-xs text-muted-foreground">动态管理世界观、主角、剧情路线</div>
              </div>
              <div>
                <div className="font-medium mb-1">🎭 NPC按需生成</div>
                <div className="text-xs text-muted-foreground">seed→instantiate→engage→adapt</div>
              </div>
              <div>
                <div className="font-medium mb-1">🔍 一致性审计</div>
                <div className="text-xs text-muted-foreground">硬规则、因果、资源守恒检查</div>
              </div>
              <div>
                <div className="font-medium mb-1">📊 事件线评分</div>
                <div className="text-xs text-muted-foreground">可玩性/叙事/混合三种模式</div>
              </div>
              <div>
                <div className="font-medium mb-1">🔗 线索经济管理</div>
                <div className="text-xs text-muted-foreground">伏笔SLA、证据链验证</div>
              </div>
              <div>
                <div className="font-medium mb-1">🗺️ 世界脚手架</div>
                <div className="text-xs text-muted-foreground">4-Pass细化、可供性chips</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 进入按钮 */}
        <div className="text-center space-y-3">
          <Button
            size="lg"
            className="text-lg px-8 shadow-lg hover:shadow-xl transition-all"
            onClick={() => router.push("/workspace")}
          >
            进入工作台
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
          <p className="text-sm text-muted-foreground">
            3秒后自动跳转...
          </p>
        </div>

        {/* 版本信息 */}
        <div className="text-center text-xs text-muted-foreground space-y-1">
          <div>v0.6.0 · 世界系统集成完成 · 2025-11-02</div>
          <div>后端: DeepSeek V3 · 前端: Next.js 14 + shadcn/ui</div>
        </div>
      </div>
    </main>
  )
}
