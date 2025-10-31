"use client"

import { useState } from "react"
import { BookOpen, Download, Eye, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface Novel {
  id: string
  title: string
  type: string
  chapters: number
  createdAt: string
}

export function NovelList() {
  const [novels] = useState<Novel[]>([
    {
      id: "1",
      title: "能源纪元",
      type: "scifi",
      chapters: 15,
      createdAt: "2025-10-30"
    },
    {
      id: "2",
      title: "逆天改命录",
      type: "xianxia",
      chapters: 8,
      createdAt: "2025-10-29"
    }
  ])

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {novels.length === 0 ? (
        <Card className="col-span-full">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
            <BookOpen className="h-12 w-12 mb-4 opacity-50" />
            <p>还没有创作小说</p>
            <p className="text-sm mt-2">点击"开始创作"开始你的第一部小说</p>
          </CardContent>
        </Card>
      ) : (
        novels.map((novel) => (
          <Card key={novel.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{novel.title}</CardTitle>
                  <CardDescription>
                    {novel.type === "scifi" ? "科幻" : "玄幻"} · {novel.chapters} 章
                  </CardDescription>
                </div>
                <Button variant="ghost" size="icon">
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1">
                  <Eye className="mr-2 h-4 w-4" />
                  查看
                </Button>
                <Button variant="outline" size="sm" className="flex-1">
                  <Download className="mr-2 h-4 w-4" />
                  导出
                </Button>
              </div>
              <div className="mt-3 text-xs text-muted-foreground">
                创建于 {novel.createdAt}
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  )
}
