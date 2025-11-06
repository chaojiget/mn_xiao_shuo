"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Book } from "lucide-react"

interface LoreViewerProps {
  lore: Record<string, string>
}

export function LoreViewer({ lore }: LoreViewerProps) {
  const entries = Object.entries(lore)

  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Book className="h-12 w-12 text-gray-600 mb-4" />
        <div className="text-gray-400">暂无Lore条目</div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4">
      {entries.map(([key, value]) => (
        <Card key={key} className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white text-lg flex items-center gap-2">
              <Book className="h-5 w-5 text-purple-500" />
              {key}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-300 whitespace-pre-wrap">{value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
