"use client"

import { useState } from "react"
import { BookText, Loader2, Play, Save } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import { Toaster } from "@/components/ui/toaster"
import { apiClient } from "@/lib/api-client"

export function NovelGenerator() {
  const [novelType, setNovelType] = useState<"scifi" | "xianxia">("scifi")
  const [generating, setGenerating] = useState(false)
  const [currentChapter, setCurrentChapter] = useState(0)
  const [content, setContent] = useState("")
  const [userChoice, setUserChoice] = useState("")
  const [novelSettings, setNovelSettings] = useState({
    title: "",
    type: "scifi",
    protagonist: "",
    background: ""
  })
  const { toast } = useToast()

  const handleStart = async () => {
    setGenerating(true)
    setCurrentChapter(1)
    setContent("")

    try {
      console.log("开始生成第一章...")

      // 调用聊天 API 生成第一章
      const response = await apiClient.streamChat({
        message: `请为我创作一部${novelType === "scifi" ? "科幻" : "玄幻"}小说的第一章。请包含：
1. 引人入胜的开场
2. 主角的初始设定
3. 世界观的基本介绍
4. 一个吸引读者的悬念

请直接输出第一章内容，不要额外的说明。`,
        novel_settings: {
          title: novelType === "scifi" ? "能源纪元" : "逆天改命录",
          type: novelType,
          protagonist: "",
          background: ""
        },
        history: []
      })

      console.log("API 响应状态:", response.status, response.ok)

      if (!response.ok) {
        const errorText = await response.text()
        console.error("API 错误响应:", errorText)
        throw new Error(`生成失败: ${response.status} - ${errorText}`)
      }

      console.log("开始读取流式响应...")

      // 读取流式响应
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let generatedContent = ""

      if (reader) {
        console.log("Reader 已创建，开始读取数据流...")
        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            console.log("流式读取完成")
            break
          }

          const chunk = decoder.decode(value)
          console.log("收到数据块:", chunk.substring(0, 100) + "...")

          const lines = chunk.split("\n\n")

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6))
                console.log("解析的数据:", data)
                if (data.type === "text") {
                  generatedContent += data.content
                  setContent(generatedContent)
                }
              } catch (e) {
                console.error("解析 SSE 失败:", e, "原始行:", line)
              }
            }
          }
        }
      } else {
        console.error("无法创建 reader")
      }

      console.log("生成完成，总长度:", generatedContent.length)
      toast({
        title: "生成成功",
        description: "第一章已生成完毕"
      })
    } catch (error) {
      console.error("生成失败:", error)
      toast({
        title: "生成失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      })
      setContent("生成失败，请稍后重试")
    } finally {
      setGenerating(false)
    }
  }

  const handleContinue = async () => {
    if (!userChoice.trim()) {
      toast({
        title: "请输入你的选择",
        description: "请在输入框中描述你希望故事如何发展",
        variant: "destructive"
      })
      return
    }

    setGenerating(true)
    const nextChapter = currentChapter + 1
    setContent("")

    try {
      // 调用聊天 API 生成下一章
      const response = await apiClient.streamChat({
        message: `基于用户的选择："${userChoice}"，请继续生成第 ${nextChapter} 章的内容。

请注意：
1. 延续前文的故事线
2. 合理地融入用户的选择
3. 保持世界观一致性
4. 继续推进剧情发展
5. 保持悬念和吸引力

请直接输出第 ${nextChapter} 章内容，不要额外的说明。`,
        novel_settings: {
          title: novelType === "scifi" ? "能源纪元" : "逆天改命录",
          type: novelType,
          protagonist: "",
          background: ""
        },
        history: []
      })

      if (!response.ok) {
        throw new Error("生成失败")
      }

      // 读取流式响应
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let generatedContent = ""

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split("\n\n")

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === "text") {
                  generatedContent += data.content
                  setContent(generatedContent)
                }
              } catch (e) {
                console.error("解析 SSE 失败:", e)
              }
            }
          }
        }
      }

      setCurrentChapter(nextChapter)
      setUserChoice("")
      toast({
        title: "生成成功",
        description: `第 ${nextChapter} 章已生成完毕`
      })
    } catch (error) {
      console.error("生成失败:", error)
      toast({
        title: "生成失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      })
      setContent("生成失败，请稍后重试")
    } finally {
      setGenerating(false)
    }
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
            <RadioGroup value={novelType} onValueChange={(value) => setNovelType(value as "scifi" | "xianxia")}>
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
      <Toaster />
    </div>
  )
}
