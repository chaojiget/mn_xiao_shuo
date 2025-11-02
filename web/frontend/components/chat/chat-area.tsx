import { Message, NovelSettings } from "@/types"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Settings } from "lucide-react"
import { MessageList } from "./message-list"
import { MessageInput } from "./message-input"

interface ChatAreaProps {
  messages: Message[]
  input: string
  setInput: (value: string) => void
  onSend: () => void
  onStop: () => void
  isLoading: boolean
  messagesEndRef: React.RefObject<HTMLDivElement>
  settings: NovelSettings
  showSettings: boolean
  onToggleSettings: () => void
}

export function ChatArea({
  messages,
  input,
  setInput,
  onSend,
  onStop,
  isLoading,
  messagesEndRef,
  settings,
  showSettings,
  onToggleSettings
}: ChatAreaProps) {
  return (
    <Card className="flex-1 flex flex-col bg-white/5 border-white/10 backdrop-blur-sm overflow-hidden">
      {/* 顶部栏 */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div>
          <h2 className="text-white font-bold text-lg">{settings.title || "AI 跑团"}</h2>
          {settings.protagonistName && (
            <p className="text-gray-400 text-sm">扮演: {settings.protagonistName}</p>
          )}
        </div>
        {!showSettings && (
          <Button
            onClick={onToggleSettings}
            variant="outline"
            size="sm"
            className="text-white border-white/20"
          >
            <Settings className="w-4 h-4 mr-2" />
            设定
          </Button>
        )}
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList
          messages={messages}
          messagesEndRef={messagesEndRef}
          showEmptyState={showSettings}
          emptyStateMessage={showSettings ? "输入标题，点击'一键生成'开始创作" : "开始你的冒险吧..."}
        />
      </div>

      {/* 输入框 */}
      {!showSettings && (
        <MessageInput
          input={input}
          setInput={setInput}
          onSend={onSend}
          onStop={onStop}
          isLoading={isLoading}
          disabled={!settings.title || !settings.background}
        />
      )}
    </Card>
  )
}