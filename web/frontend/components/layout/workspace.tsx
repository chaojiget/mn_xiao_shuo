"use client"

import { useState } from "react"
import { BookOpen, MessageSquare, Gamepad2, Map, Settings, Menu, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface WorkspaceProps {
  children?: React.ReactNode
}

export type WorkspaceTab = "create" | "chat" | "game" | "world" | "settings"

interface NavItem {
  id: WorkspaceTab
  label: string
  icon: React.ElementType
  description: string
}

const navItems: NavItem[] = [
  {
    id: "create",
    label: "创作",
    icon: BookOpen,
    description: "小说生成与管理"
  },
  {
    id: "chat",
    label: "聊天",
    icon: MessageSquare,
    description: "AI对话辅助创作"
  },
  {
    id: "game",
    label: "游戏",
    icon: Gamepad2,
    description: "单人跑团模式"
  },
  {
    id: "world",
    label: "世界",
    icon: Map,
    description: "世界脚手架管理"
  },
  {
    id: "settings",
    label: "设置",
    icon: Settings,
    description: "系统配置"
  }
]

interface WorkspaceInternalProps extends WorkspaceProps {
  activeTab: WorkspaceTab
  setActiveTab: (tab: WorkspaceTab) => void
}

export function Workspace({ children, activeTab, setActiveTab }: WorkspaceInternalProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* 侧边栏 */}
      <aside
        className={cn(
          "flex flex-col border-r bg-card transition-all duration-300",
          sidebarOpen ? "w-64" : "w-16"
        )}
      >
        {/* Logo区域 */}
        <div className="h-16 flex items-center justify-between px-4 border-b">
          {sidebarOpen ? (
            <>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <BookOpen className="w-4 h-4 text-primary-foreground" />
                </div>
                <div className="flex flex-col">
                  <span className="font-semibold text-sm">AI小说生成器</span>
                  <span className="text-xs text-muted-foreground">v0.6.0</span>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 mx-auto"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* 导航菜单 */}
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = activeTab === item.id

            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-left",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-accent hover:text-accent-foreground"
                )}
                title={!sidebarOpen ? item.label : undefined}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                {sidebarOpen && (
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{item.label}</div>
                    <div className="text-xs opacity-70 truncate">
                      {item.description}
                    </div>
                  </div>
                )}
              </button>
            )
          })}
        </nav>

        {/* 底部信息 */}
        {sidebarOpen && (
          <div className="p-4 border-t text-xs text-muted-foreground">
            <div className="space-y-1">
              <div>后端: DeepSeek V3</div>
              <div>模式: 混合叙事</div>
            </div>
          </div>
        )}
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* 顶部栏 */}
        <header className="h-16 border-b px-6 flex items-center justify-between bg-card">
          <div>
            <h1 className="text-xl font-semibold">
              {navItems.find((item) => item.id === activeTab)?.label}
            </h1>
            <p className="text-sm text-muted-foreground">
              {navItems.find((item) => item.id === activeTab)?.description}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              帮助
            </Button>
          </div>
        </header>

        {/* 内容区域 */}
        <div className="flex-1 overflow-auto p-6 bg-background">
          {children || (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-muted-foreground">
                <div className="text-4xl mb-4">
                  {navItems.find((item) => item.id === activeTab)?.icon &&
                    (() => {
                      const Icon = navItems.find((item) => item.id === activeTab)!.icon
                      return <Icon className="h-16 w-16 mx-auto opacity-20" />
                    })()}
                </div>
                <p>选择左侧菜单开始使用</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

// 导出Context供子组件使用
import { createContext, useContext } from "react"

interface WorkspaceContextType {
  activeTab: WorkspaceTab
  setActiveTab: (tab: WorkspaceTab) => void
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined)

export function useWorkspace() {
  const context = useContext(WorkspaceContext)
  if (!context) {
    throw new Error("useWorkspace must be used within WorkspaceProvider")
  }
  return context
}

export function WorkspaceProvider({
  children,
  value
}: {
  children: React.ReactNode
  value: WorkspaceContextType
}) {
  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
}
