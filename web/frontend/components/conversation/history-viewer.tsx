"use client"

import { useState } from "react"
import { History, Download, Search, Filter, User, Bot, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"

interface Message {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  timestamp: string
  messageType?: string
  metadata?: Record<string, any>
}

interface Branch {
  id: string
  name: string
  messageCount: number
  isActive: boolean
}

interface HistoryViewerProps {
  novelId: string
  onExport?: () => void
}

export function HistoryViewer({ novelId, onExport }: HistoryViewerProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedBranch, setSelectedBranch] = useState("main")

  // Mock data - 实际应从API获取
  const branches: Branch[] = [
    { id: "main", name: "主分支", messageCount: 25, isActive: true },
    { id: "branch_1", name: "支线：探索实验室", messageCount: 12, isActive: false }
  ]

  const messages: Message[] = [
    {
      id: "1",
      role: "user",
      content: "我想创建一个科幻小说",
      timestamp: "2025-01-31 10:00:00",
      messageType: "text"
    },
    {
      id: "2",
      role: "assistant",
      content: "好的！我会帮你创建一个科幻小说。首先，让我们设定世界观...",
      timestamp: "2025-01-31 10:00:05",
      messageType: "text"
    },
    {
      id: "3",
      role: "user",
      content: "主角选择调查废弃空间站",
      timestamp: "2025-01-31 10:15:00",
      messageType: "choice",
      metadata: { choiceId: "investigate_station" }
    },
    {
      id: "4",
      role: "assistant",
      content: "你小心翼翼地接近那座漂浮在深空中的废弃空间站...",
      timestamp: "2025-01-31 10:15:10",
      messageType: "chapter",
      metadata: { chapterNum: 1 }
    }
  ]

  const filteredMessages = messages.filter(msg =>
    msg.content.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getRoleIcon = (role: string) => {
    switch (role) {
      case "user":
        return <User className="w-4 h-4" />
      case "assistant":
        return <Bot className="w-4 h-4" />
      case "system":
        return <AlertCircle className="w-4 h-4" />
      default:
        return null
    }
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case "user":
        return "text-blue-600 dark:text-blue-400"
      case "assistant":
        return "text-green-600 dark:text-green-400"
      case "system":
        return "text-orange-600 dark:text-orange-400"
      default:
        return ""
    }
  }

  const getMessageTypeLabel = (type?: string) => {
    switch (type) {
      case "choice":
        return "选择"
      case "chapter":
        return "章节"
      case "setting_edit":
        return "设定修改"
      default:
        return "对话"
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <History className="w-5 h-5" />
              对话历史
            </CardTitle>
            <CardDescription>
              查看完整的创作过程和对话记录
            </CardDescription>
          </div>
          <Button onClick={onExport} variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            导出Markdown
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 分支选择 */}
        <div className="flex gap-2">
          {branches.map(branch => (
            <Button
              key={branch.id}
              variant={selectedBranch === branch.id ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedBranch(branch.id)}
            >
              {branch.name}
              {branch.isActive && (
                <span className="ml-2 w-2 h-2 bg-green-500 rounded-full" />
              )}
            </Button>
          ))}
        </div>

        {/* 搜索框 */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="搜索对话内容..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" size="icon">
            <Filter className="w-4 h-4" />
          </Button>
        </div>

        {/* 消息列表 */}
        <ScrollArea className="h-[500px] pr-4">
          <div className="space-y-4">
            {filteredMessages.map((message) => (
              <div
                key={message.id}
                className="flex gap-3 p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
              >
                <div className={`flex-shrink-0 ${getRoleColor(message.role)}`}>
                  {getRoleIcon(message.role)}
                </div>

                <div className="flex-1 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`font-medium ${getRoleColor(message.role)}`}>
                        {message.role === "user" ? "用户" : message.role === "assistant" ? "助手" : "系统"}
                      </span>
                      <span className="text-xs px-2 py-1 bg-secondary rounded">
                        {getMessageTypeLabel(message.messageType)}
                      </span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {message.timestamp}
                    </span>
                  </div>

                  <div className="text-sm text-foreground whitespace-pre-wrap">
                    {message.content}
                  </div>

                  {message.metadata && Object.keys(message.metadata).length > 0 && (
                    <details className="text-xs text-muted-foreground">
                      <summary className="cursor-pointer hover:text-foreground">
                        元数据
                      </summary>
                      <pre className="mt-2 p-2 bg-secondary rounded">
                        {JSON.stringify(message.metadata, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        {filteredMessages.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            {searchTerm ? "没有找到匹配的消息" : "暂无对话记录"}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
