"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Scroll, CheckCircle, Circle } from "lucide-react"

interface QuestsListProps {
  quests: any[]
}

export function QuestsList({ quests }: QuestsListProps) {
  const getLineColor = (line: string) => {
    return line === "main" ? "bg-purple-600" : "bg-blue-600"
  }

  const getLineLabel = (line: string) => {
    return line === "main" ? "主线" : "支线"
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {quests.map((quest) => (
        <Card key={quest.id} className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <div className="flex items-start justify-between">
              <CardTitle className="text-white text-lg flex items-center gap-2">
                <Scroll className="h-5 w-5" />
                {quest.title}
              </CardTitle>
              <Badge className={getLineColor(quest.line)}>
                {getLineLabel(quest.line)}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {quest.summary && (
              <p className="text-sm text-gray-300">{quest.summary}</p>
            )}

            {quest.objectives && quest.objectives.length > 0 && (
              <div className="pt-2 border-t border-slate-700">
                <div className="text-xs text-gray-500 mb-2">
                  目标 ({quest.objectives.length}):
                </div>
                <ul className="space-y-2">
                  {quest.objectives.map((obj: any) => (
                    <li
                      key={obj.id}
                      className="flex items-start gap-2 text-sm text-gray-300"
                    >
                      {obj.done ? (
                        <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                      ) : (
                        <Circle className="h-4 w-4 text-gray-500 mt-0.5" />
                      )}
                      <span className="flex-1">{obj.text}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {quest.rewards && Object.keys(quest.rewards).length > 0 && (
              <div className="pt-2 border-t border-slate-700">
                <div className="text-xs text-gray-500 mb-1">奖励:</div>
                <div className="text-sm text-yellow-400">
                  {Object.entries(quest.rewards)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join(", ")}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
