"use client"

import { useState } from "react"
import { BookText, Loader2, Play, Save } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Textarea } from "@/components/ui/textarea"

export function NovelGenerator() {
  const [novelType, setNovelType] = useState("scifi")
  const [generating, setGenerating] = useState(false)
  const [currentChapter, setCurrentChapter] = useState(0)
  const [content, setContent] = useState("")
  const [userChoice, setUserChoice] = useState("")

  const handleStart = async () => {
    setGenerating(true)
    setCurrentChapter(1)

    // TODO: 调用后端 API
    setTimeout(() => {
      setContent("这是生成的第一章内容示例...")
      setGenerating(false)
    }, 2000)
  }

  const handleContinue = async () => {
    setGenerating(true)
    // TODO: 发送用户选择到后端
    setTimeout(() => {
      setCurrentChapter(prev => prev + 1)
      setContent("基于你的选择，生成的后续内容...")
      setUserChoice("")
      setGenerating(false)
    }, 2000)
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* 左侧：设置面板 */}
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle>创作设置</CardTitle>
          <CardDescription>选择小说类型和风格</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <Label>小说类型</Label>
            <RadioGroup value={novelType} onValueChange={setNovelType}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="scifi" id="scifi" />
                <Label htmlFor="scifi" className="font-normal cursor-pointer">
                  科幻小说 - 能源纪元
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="xianxia" id="xianxia" />
                <Label htmlFor="xianxia" className="font-normal cursor-pointer">
                  玄幻小说 - 逆天改命录
                </Label>
              </div>
            </RadioGroup>
          </div>

          {currentChapter === 0 ? (
            <Button onClick={handleStart} disabled={generating} className="w-full">
              {generating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  生成中...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  开始创作
                </>
              )}
            </Button>
          ) : (
            <div className="space-y-4">
              <div>
                <Label htmlFor="choice">你的选择</Label>
                <Textarea
                  id="choice"
                  placeholder="输入你的选择，影响后续剧情..."
                  value={userChoice}
                  onChange={(e) => setUserChoice(e.target.value)}
                  className="mt-2"
                  rows={3}
                />
              </div>
              <Button
                onClick={handleContinue}
                disabled={generating}
                className="w-full"
              >
                {generating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    继续生成
                  </>
                )}
              </Button>
            </div>
          )}

          {currentChapter > 0 && (
            <div className="pt-4 border-t">
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>已生成章节</span>
                <span className="font-semibold">{currentChapter}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 右侧：内容展示 */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>
                {currentChapter > 0 ? `第 ${currentChapter} 章` : "小说内容"}
              </CardTitle>
              <CardDescription>
                {currentChapter > 0 ? "AI 生成的章节内容" : "开始创作后将在这里显示"}
              </CardDescription>
            </div>
            {currentChapter > 0 && (
              <Button variant="outline" size="sm">
                <Save className="mr-2 h-4 w-4" />
                保存
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {currentChapter === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
              <BookText className="h-12 w-12 mb-4 opacity-50" />
              <p>选择小说类型，点击"开始创作"</p>
              <p className="text-sm mt-2">AI 将为你生成精彩的故事内容</p>
            </div>
          ) : (
            <div className="prose prose-slate dark:prose-invert max-w-none">
              <div className="whitespace-pre-wrap">{content}</div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
