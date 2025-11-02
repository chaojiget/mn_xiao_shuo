import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Send, Square } from "lucide-react"

interface MessageInputProps {
  input: string
  setInput: (value: string) => void
  onSend: () => void
  onStop: () => void
  isLoading: boolean
  disabled?: boolean
  placeholder?: string
}

export function MessageInput({
  input,
  setInput,
  onSend,
  onStop,
  isLoading,
  disabled = false,
  placeholder = "输入你的行动或对话..."
}: MessageInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (!isLoading && input.trim()) {
        onSend()
      }
    }
  }

  return (
    <div className="p-4 border-t border-white/10">
      <div className="flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="flex-1 min-h-[60px] max-h-[120px] bg-white/10 border-white/20 text-white placeholder:text-gray-400 focus:border-purple-500 resize-none disabled:opacity-50"
        />
        {isLoading ? (
          <Button
            onClick={onStop}
            variant="destructive"
            size="icon"
            className="px-6"
            title="停止生成"
          >
            <Square className="w-5 h-5" />
          </Button>
        ) : (
          <Button
            onClick={onSend}
            disabled={disabled || !input.trim()}
            className="px-6 bg-purple-600 hover:bg-purple-700 disabled:opacity-50"
            title="发送消息 (Enter)"
          >
            <Send className="w-5 h-5" />
          </Button>
        )}
      </div>
      <div className="text-xs text-gray-400 mt-2 text-right">
        按 Enter 发送，Shift+Enter 换行
      </div>
    </div>
  )
}