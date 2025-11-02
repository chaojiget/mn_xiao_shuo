import { NovelSettings, NPC, Novel } from "@/types"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  Settings,
  BookOpen,
  Sparkles,
  Wand2,
  Loader2,
  User,
  Bot,
  Map
} from "lucide-react"

interface SettingsPanelProps {
  settings: NovelSettings
  novels: Novel[]
  isGenerating: boolean
  onUpdateSetting: (updates: Partial<NovelSettings>) => void
  onGenerateSetting: () => Promise<void>
  onStartCreating: () => void
  onLoadNovel?: (novelId: string) => void
}

export function SettingsPanel({
  settings,
  novels,
  isGenerating,
  onUpdateSetting,
  onGenerateSetting,
  onStartCreating,
  onLoadNovel
}: SettingsPanelProps) {
  const handleAutoGenerate = async () => {
    try {
      await onGenerateSetting()
    } catch (error) {
      console.error("生成设定失败:", error)
    }
  }

  return (
    <div className="w-full lg:w-[500px] flex flex-col gap-4">
      {/* 主标题区域 */}
      <Card className="p-6 bg-white/5 border-white/10 backdrop-blur-sm">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center justify-center gap-2">
            <Sparkles className="w-8 h-8 text-yellow-400" />
            AI 跑团小说
          </h1>
          <p className="text-gray-400 text-sm">输入标题，一键生成完整的世界观和角色设定</p>
        </div>

        {/* 标题输入 - 突出显示 */}
        <div className="mb-4">
          <Label className="text-white mb-2 block text-lg font-semibold">📖 小说标题</Label>
          <input
            value={settings.title}
            onChange={(e) => onUpdateSetting({ title: e.target.value })}
            placeholder="例如：星际迷航、修仙者传说..."
            className="w-full px-4 py-3 bg-white/10 border-2 border-white/20 rounded-lg text-white text-lg placeholder:text-gray-400 focus:border-purple-500 focus:outline-none transition-all disabled:opacity-50"
            disabled={isGenerating}
          />
        </div>

        {/* 类型选择 */}
        <div className="mb-4">
          <Label className="text-white mb-2 block font-semibold">🎨 类型</Label>
          <RadioGroup
            value={settings.type}
            onValueChange={(value: "scifi" | "xianxia") =>
              onUpdateSetting({ type: value })
            }
            disabled={isGenerating}
            className="flex gap-4"
          >
            <div className="flex-1">
              <div className="flex items-center space-x-2 p-3 rounded-lg bg-white/10 border border-white/20 hover:bg-white/20 transition-colors cursor-pointer disabled:opacity-50">
                <RadioGroupItem value="scifi" id="scifi" />
                <Label htmlFor="scifi" className="text-white cursor-pointer flex-1">🚀 科幻</Label>
              </div>
            </div>
            <div className="flex-1">
              <div className="flex items-center space-x-2 p-3 rounded-lg bg-white/10 border border-white/20 hover:bg-white/20 transition-colors cursor-pointer disabled:opacity-50">
                <RadioGroupItem value="xianxia" id="xianxia" />
                <Label htmlFor="xianxia" className="text-white cursor-pointer flex-1">⚔️ 玄幻</Label>
              </div>
            </div>
          </RadioGroup>
        </div>

        {/* 一键生成按钮 */}
        <Button
          onClick={handleAutoGenerate}
          disabled={isGenerating || !settings.title.trim()}
          className="w-full py-6 text-lg font-bold bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 transition-all disabled:opacity-50"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-6 h-6 mr-2 animate-spin" />
              AI 正在创作中...
            </>
          ) : (
            <>
              <Wand2 className="w-6 h-6 mr-2" />
              ✨ 一键生成完整设定
            </>
          )}
        </Button>
      </Card>

      {/* 生成的详细设定 */}
      {(settings.background || settings.npcs?.length) && (
        <Card className="p-4 bg-white/5 border-white/10 backdrop-blur-sm flex-1 overflow-y-auto">
          <h3 className="text-white font-bold mb-4 flex items-center gap-2">
            <Settings className="w-5 h-5" />
            生成的设定
          </h3>

          <div className="space-y-4 text-white text-sm">
            {/* 主角信息 */}
            {settings.protagonistName && (
              <div className="p-3 rounded-lg bg-blue-500/20 border border-blue-500/30">
                <div className="font-bold text-blue-300 mb-1 flex items-center gap-2">
                  <User className="w-4 h-4" />
                  主角
                </div>
                <div className="font-semibold">{settings.protagonistName}</div>
                <div className="text-gray-300 text-xs">{settings.protagonistRole}</div>
                {settings.protagonistAbilities && settings.protagonistAbilities.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {settings.protagonistAbilities.map((ability, i) => (
                      <span key={i} className="px-2 py-1 rounded bg-blue-600/30 text-xs">
                        {ability}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* 世界观 */}
            {settings.background && (
              <div>
                <div className="font-bold text-purple-300 mb-1 flex items-center gap-2">
                  <Map className="w-4 h-4" />
                  世界观
                </div>
                <div className="text-gray-300 text-xs leading-relaxed whitespace-pre-wrap">
                  {settings.background}
                </div>
              </div>
            )}

            {/* NPC 列表 */}
            {settings.npcs && settings.npcs.length > 0 && (
              <div>
                <div className="font-bold text-green-300 mb-2 flex items-center gap-2">
                  <Bot className="w-4 h-4" />
                  NPC 角色
                </div>
                <div className="space-y-2">
                  {settings.npcs.map(npc => (
                    <div key={npc.id} className="p-2 rounded bg-white/10 border border-white/10">
                      <div className="font-semibold">
                        {npc.name} <span className="text-xs text-gray-400">({npc.role})</span>
                      </div>
                      <div className="text-xs text-gray-400 mt-1">{npc.personality}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 开始创作按钮 */}
            <Button
              onClick={onStartCreating}
              className="w-full py-4 bg-green-600 hover:bg-green-700 transition-all"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              开始创作
            </Button>
          </div>
        </Card>
      )}

      {/* 已有小说列表（折叠） */}
      {novels.length > 0 && (
        <Card className="p-4 bg-white/5 border-white/10 backdrop-blur-sm">
          <details>
            <summary className="text-white font-bold cursor-pointer flex items-center gap-2">
              <BookOpen className="w-5 h-5" />
              我的小说 ({novels.length})
            </summary>
            <div className="mt-3 space-y-2 max-h-40 overflow-y-auto">
              {novels.map(novel => (
                <button
                  key={novel.id}
                  onClick={() => onLoadNovel?.(novel.id)}
                  className="w-full text-left px-3 py-2 rounded bg-white/10 hover:bg-white/20 transition-colors text-white text-sm"
                >
                  <div className="font-medium">{novel.title}</div>
                  <div className="text-xs text-gray-400">
                    {novel.type === "scifi" ? "🚀 科幻" : "⚔️ 玄幻"}
                  </div>
                </button>
              ))}
            </div>
          </details>
        </Card>
      )}
    </div>
  )
}