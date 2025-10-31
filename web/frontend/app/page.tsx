"use client"

import { useState } from "react"
import { BookOpen, Sparkles, Settings, MessageSquare, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { NovelGenerator } from "@/components/novel/novel-generator"
import { NovelList } from "@/components/novel/novel-list"
import Link from "next/link"

export default function Home() {
  const [activeTab, setActiveTab] = useState("generate")

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto py-8 px-4">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
                <BookOpen className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight">AI 小说生成器</h1>
                <p className="text-muted-foreground">全局导演架构 · 智能叙事引擎 · 探索式世界观</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Link href="/chat">
                <Button variant="outline" className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  聊天模式
                </Button>
              </Link>
              <Button variant="outline" size="icon">
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <div className="font-medium">可编辑设定</div>
                  <div className="text-sm text-muted-foreground">动态管理世界观</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <div className="font-medium">NPC按需生成</div>
                  <div className="text-sm text-muted-foreground">智能角色管理</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-purple-500" />
                </div>
                <div>
                  <div className="font-medium">一致性审计</div>
                  <div className="text-sm text-muted-foreground">自动检查逻辑</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="generate" className="flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              开始创作
            </TabsTrigger>
            <TabsTrigger value="library" className="flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              我的小说
            </TabsTrigger>
          </TabsList>

          <TabsContent value="generate" className="space-y-4">
            <NovelGenerator />
          </TabsContent>

          <TabsContent value="library" className="space-y-4">
            <NovelList />
          </TabsContent>
        </Tabs>
      </div>
    </main>
  )
}
