"use client"

import { useState } from "react"
import { useParams } from "next/navigation"
import { BookOpen, Settings, History, Users, Compass } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { SettingEditor } from "@/components/setting/setting-editor"
import { HistoryViewer } from "@/components/conversation/history-viewer"
import { NPCManager } from "@/components/npc/npc-manager"

export default function NovelPage() {
  const params = useParams()
  const novelId = params.id as string
  const [novelType, setNovelType] = useState<"scifi" | "xianxia">("scifi")

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto py-8 px-4">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
              <BookOpen className="w-6 h-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">小说工作台</h1>
              <p className="text-muted-foreground">全方位管理你的AI小说创作</p>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="setting" className="space-y-6">
          <TabsList className="grid w-full max-w-2xl grid-cols-4">
            <TabsTrigger value="setting" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              设定编辑
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2">
              <History className="w-4 h-4" />
              对话历史
            </TabsTrigger>
            <TabsTrigger value="npcs" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              NPC管理
            </TabsTrigger>
            <TabsTrigger value="explore" className="flex items-center gap-2">
              <Compass className="w-4 h-4" />
              探索进度
            </TabsTrigger>
          </TabsList>

          <TabsContent value="setting">
            <SettingEditor
              novelType={novelType}
              onSave={(setting) => {
                console.log("保存设定:", setting)
                // TODO: 调用API保存设定
              }}
            />
          </TabsContent>

          <TabsContent value="history">
            <HistoryViewer
              novelId={novelId}
              onExport={() => {
                console.log("导出历史")
                // TODO: 调用API导出Markdown
              }}
            />
          </TabsContent>

          <TabsContent value="npcs">
            <NPCManager novelId={novelId} />
          </TabsContent>

          <TabsContent value="explore">
            <Card className="p-8 text-center text-muted-foreground">
              <Compass className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">探索进度</h3>
              <p>即将推出 - 追踪主角的世界探索进度</p>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  )
}
