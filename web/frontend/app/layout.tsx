import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Toaster } from "@/components/ui/toaster"
import dynamic from "next/dynamic"

// 站点头部（在游戏页面自动隐藏）
const SiteHeader = dynamic(() => import("@/components/site-header"), { ssr: false })

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "AI 世界生成器",
  description: "预生成完整世界 · 冒险体验",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <SiteHeader />
        {children}
        <Toaster />
      </body>
    </html>
  )
}
