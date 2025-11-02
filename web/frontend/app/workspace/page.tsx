"use client"

import { useState } from "react"
import { Workspace, WorkspaceProvider, WorkspaceTab } from "@/components/layout/workspace"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { NovelGenerator } from "@/components/novel/novel-generator"
import { NovelList } from "@/components/novel/novel-list"
import { WorldManager } from "@/components/world/world-manager"
import { Card } from "@/components/ui/card"
import { BookOpen, Sparkles } from "lucide-react"

// 创作页面
function CreateTab() {
  const [activeTab, setActiveTab] = useState("generate")

  return (
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
  )
}

// 聊天页面（从原chat页面导入）
function ChatTab() {
  return (
    <div className="h-full flex items-center justify-center">
      <Card className="p-8 text-center max-w-md">
        <h3 className="text-lg font-semibold mb-2">聊天功能</h3>
        <p className="text-sm text-muted-foreground mb-4">
          AI对话辅助创作功能正在整合中...
        </p>
        <p className="text-xs text-muted-foreground">
          临时访问: <a href="/chat" className="text-primary hover:underline">/chat</a>
        </p>
      </Card>
    </div>
  )
}

// 游戏页面（从原game页面导入）
function GameTab() {
  return (
    <div className="h-full flex items-center justify-center">
      <Card className="p-8 text-center max-w-md">
        <h3 className="text-lg font-semibold mb-2">游戏功能</h3>
        <p className="text-sm text-muted-foreground mb-4">
          单人跑团游戏功能正在整合中...
        </p>
        <p className="text-xs text-muted-foreground">
          临时访问: <a href="/game" className="text-primary hover:underline">/game</a>
        </p>
      </Card>
    </div>
  )
}

// 世界管理页面
function WorldTab() {
  return <WorldManager />
}

// 设置页面
function SettingsTab() {
  return (
    <div className="h-full flex items-center justify-center">
      <Card className="p-8 text-center max-w-md">
        <h3 className="text-lg font-semibold mb-2">系统设置</h3>
        <p className="text-sm text-muted-foreground">
          设置功能开发中...
        </p>
      </Card>
    </div>
  )
}

// 主工作台页面
export default function WorkspacePage() {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("create")

  return (
    <WorkspaceProvider value={{ activeTab, setActiveTab }}>
      <Workspace activeTab={activeTab} setActiveTab={setActiveTab}>
        {activeTab === "create" && <CreateTab />}
        {activeTab === "chat" && <ChatTab />}
        {activeTab === "game" && <GameTab />}
        {activeTab === "world" && <WorldTab />}
        {activeTab === "settings" && <SettingsTab />}
      </Workspace>
    </WorkspaceProvider>
  )
}
