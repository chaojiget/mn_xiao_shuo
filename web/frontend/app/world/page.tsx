"use client"

import { WorldManager } from "@/components/world/world-manager"

export default function WorldPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="container mx-auto max-w-7xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white">世界管理</h1>
          <p className="text-gray-300 mt-2">
            创建和管理小说世界脚手架：区域、地点、派系、物品等
          </p>
        </div>

        <WorldManager />
      </div>
    </div>
  )
}
