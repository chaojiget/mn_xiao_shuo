"use client"

import { WorldsList } from "@/components/worlds/worlds-list"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { useState } from "react"
import { GenerateWorldDialog } from "@/components/worlds/generate-world-dialog"

export default function WorldsPage() {
  const [showGenerateDialog, setShowGenerateDialog] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">世界包管理</h1>
            <p className="text-gray-300 mt-2">
              预生成的完整世界：地点、NPC、任务、掉落表、遭遇表
            </p>
          </div>
          <Button
            onClick={() => setShowGenerateDialog(true)}
            size="lg"
            className="bg-purple-600 hover:bg-purple-700"
          >
            <Plus className="mr-2 h-5 w-5" />
            生成新世界
          </Button>
        </div>

        {/* Worlds Grid */}
        <WorldsList />

        {/* Generate Dialog */}
        <GenerateWorldDialog
          open={showGenerateDialog}
          onOpenChange={setShowGenerateDialog}
        />
      </div>
    </div>
  )
}
