"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Eye, CheckCircle, Clock, AlertCircle, Trash2 } from "lucide-react"
import Link from "next/link"

interface World {
  id: string
  title: string
  seed: number
  status: "draft" | "published" | "generating"
  created_at: string
}

export function WorldsList() {
  const [worlds, setWorlds] = useState<World[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadWorlds()
  }, [])

  const loadWorlds = async () => {
    try {
      setLoading(true)
      const response = await fetch("/api/worlds/")
      if (!response.ok) {
        throw new Error("加载世界列表失败")
      }
      const data = await response.json()
      setWorlds(data.worlds || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知错误")
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: World["status"]) => {
    switch (status) {
      case "published":
        return (
          <Badge className="bg-green-600">
            <CheckCircle className="mr-1 h-3 w-3" />
            已发布
          </Badge>
        )
      case "generating":
        return (
          <Badge className="bg-yellow-600">
            <Clock className="mr-1 h-3 w-3" />
            生成中
          </Badge>
        )
      case "draft":
        return (
          <Badge variant="secondary">
            <AlertCircle className="mr-1 h-3 w-3" />
            草稿
          </Badge>
        )
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-400">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-red-400">错误: {error}</div>
      </div>
    )
  }

  if (worlds.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="text-gray-400 text-lg mb-4">还没有世界</div>
        <p className="text-gray-500 text-sm">点击右上角"生成新世界"开始创建</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {worlds.map((world) => (
        <Card
          key={world.id}
          className="bg-slate-800/50 border-slate-700 hover:bg-slate-800/70 transition-colors"
        >
          <CardHeader>
            <div className="flex items-start justify-between">
              <CardTitle className="text-white">{world.title}</CardTitle>
              {getStatusBadge(world.status)}
            </div>
            <CardDescription className="text-gray-400">
              种子: {world.seed}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-sm text-gray-400">
                创建时间: {formatDate(world.created_at)}
              </div>

              <div className="flex gap-2">
                <Link href={`/worlds/${world.id}`} className="flex-1">
                  <Button variant="outline" className="w-full">
                    <Eye className="mr-2 h-4 w-4" />
                    查看详情
                  </Button>
                </Link>
                <Button
                  variant="outline"
                  size="icon"
                  className="text-red-400 hover:text-red-300"
                  onClick={() => {
                    // TODO: 实现删除功能
                    console.log("删除世界:", world.id)
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
