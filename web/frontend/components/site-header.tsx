"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Globe, Layers, Save, Play } from "lucide-react"

function NavLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname()
  const active = pathname === href || (href !== "/" && pathname.startsWith(href))
  return (
    <Link href={href} className="hidden sm:inline-block">
      <span
        className={`px-3 py-1 rounded-md text-sm transition-colors ${
          active
            ? "bg-slate-800/80 text-white border border-slate-700"
            : "text-gray-300 hover:text-white hover:bg-slate-800/60 border border-transparent"
        }`}
      >
        {label}
      </span>
    </Link>
  )
}

export default function SiteHeader() {
  const pathname = usePathname()

  // 在游戏页面隐藏站点头部，避免与游戏内 UI 冲突
  if (pathname.startsWith("/game")) return null

  return (
    <header className="sticky top-0 z-50 bg-slate-950/70 backdrop-blur-md border-b border-slate-800/60">
      <div className="max-w-7xl mx-auto px-4 md:px-6 h-14 flex items-center justify-between">
        {/* 左侧：Logo + 导航 */}
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2 text-white">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
              <Globe className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold hidden sm:block">AI 世界生成器</span>
          </Link>

          <nav className="flex items-center gap-1">
            <NavLink href="/worlds" label="世界" />
            <NavLink href="/saves" label="存档" />
          </nav>
        </div>

        {/* 右侧：快捷操作 */}
        <div className="flex items-center gap-2">
          <Link href="/worlds" className="sm:hidden">
            <Button variant="ghost" size="icon" className="text-gray-300 hover:text-white">
              <Layers className="w-4 h-4" />
            </Button>
          </Link>
          <Link href="/saves" className="sm:hidden">
            <Button variant="ghost" size="icon" className="text-gray-300 hover:text-white">
              <Save className="w-4 h-4" />
            </Button>
          </Link>
          <Link href="/game/play">
            <Button size="sm" className="bg-purple-600 hover:bg-purple-700">
              <Play className="w-4 h-4 mr-2" />
              开始冒险
            </Button>
          </Link>
        </div>
      </div>
    </header>
  )
}

