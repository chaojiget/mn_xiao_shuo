import { Message } from "@/types"
import { Bot, User } from "lucide-react"

interface MessageListProps {
  messages: Message[]
  messagesEndRef: React.RefObject<HTMLDivElement>
  showEmptyState?: boolean
  emptyStateMessage?: string
}

export function MessageList({
  messages,
  messagesEndRef,
  showEmptyState = true,
  emptyStateMessage = "开始你的冒险吧..."
}: MessageListProps) {
  if (messages.length === 0 && showEmptyState) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 border-2 border-gray-600 rounded-full flex items-center justify-center">
            <Bot className="w-8 h-8 text-gray-400" />
          </div>
          <p>{emptyStateMessage}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {messages.map((message, index) => (
        <div
          key={index}
          className={`flex gap-3 ${
            message.role === "user" ? "justify-end" : "justify-start"
          }`}
        >
          {message.role !== "user" && (
            <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center flex-shrink-0">
              {message.role === "system" ? "📢" : <Bot className="w-5 h-5 text-white" />}
            </div>
          )}
          <div
            className={`max-w-[70%] rounded-lg p-3 ${
              message.role === "user"
                ? "bg-purple-600 text-white"
                : message.role === "system"
                ? "bg-yellow-600/20 text-yellow-200 border border-yellow-600/30"
                : "bg-white/10 text-white"
            }`}
          >
            <div className="whitespace-pre-wrap break-words">{message.content}</div>
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 bg-white/50 ml-1 animate-pulse" />
            )}
          </div>
          {message.role === "user" && (
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
              <User className="w-5 h-5 text-white" />
            </div>
          )}
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  )
}