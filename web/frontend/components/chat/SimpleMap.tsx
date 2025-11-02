"use client"

import { MapNode, MapEdge } from "@/types/game"
import { motion } from "framer-motion"
import { Lock, Check } from "lucide-react"

interface SimpleMapProps {
  nodes: MapNode[]
  edges: MapEdge[]
  currentNodeId: string
}

export function SimpleMap({ nodes, edges, currentNodeId }: SimpleMapProps) {
  // 简单的网格布局算法
  const getNodePosition = (index: number, total: number) => {
    const cols = Math.ceil(Math.sqrt(total))
    const row = Math.floor(index / cols)
    const col = index % cols

    return {
      x: col * 120 + 60,
      y: row * 100 + 50
    }
  }

  return (
    <div className="w-full h-64 bg-slate-950/50 rounded-lg border border-amber-500/20 overflow-hidden relative">
      <svg width="100%" height="100%" viewBox="0 0 400 300" className="text-amber-400">
        {/* 绘制边 */}
        {edges.map((edge, i) => {
          const fromNode = nodes.find(n => n.id === edge.fromNode)
          const toNode = nodes.find(n => n.id === edge.toNode)

          if (!fromNode || !toNode) return null

          const fromIndex = nodes.indexOf(fromNode)
          const toIndex = nodes.indexOf(toNode)
          const fromPos = getNodePosition(fromIndex, nodes.length)
          const toPos = getNodePosition(toIndex, nodes.length)

          return (
            <motion.line
              key={`edge-${i}`}
              x1={fromPos.x}
              y1={fromPos.y}
              x2={toPos.x}
              y2={toPos.y}
              stroke="currentColor"
              strokeWidth="2"
              strokeDasharray={fromNode.discovered && toNode.discovered ? "0" : "5,5"}
              opacity={fromNode.discovered || toNode.discovered ? 0.6 : 0.2}
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
            />
          )
        })}

        {/* 绘制节点 */}
        {nodes.map((node, i) => {
          const pos = getNodePosition(i, nodes.length)
          const isCurrent = node.id === currentNodeId
          const isDiscovered = node.discovered

          return (
            <g key={node.id}>
              {/* 当前位置光环 */}
              {isCurrent && (
                <motion.circle
                  cx={pos.x}
                  cy={pos.y}
                  r="25"
                  fill="none"
                  stroke="#fbbf24"
                  strokeWidth="2"
                  opacity="0.5"
                  animate={{ r: [20, 28, 20] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              )}

              {/* 节点圆圈 */}
              <motion.circle
                cx={pos.x}
                cy={pos.y}
                r="20"
                fill={isCurrent ? "#fbbf24" : isDiscovered ? "#f59e0b" : "#1e293b"}
                stroke={isCurrent ? "#fef3c7" : isDiscovered ? "#fbbf24" : "#475569"}
                strokeWidth="3"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.3, delay: i * 0.1 }}
              />

              {/* 锁定图标 */}
              {node.locked && isDiscovered && (
                <g transform={`translate(${pos.x - 6}, ${pos.y - 6})`}>
                  <Lock className="w-3 h-3" />
                </g>
              )}

              {/* 已访问标记 */}
              {!isCurrent && isDiscovered && !node.locked && (
                <g transform={`translate(${pos.x - 6}, ${pos.y - 6})`}>
                  <Check className="w-3 h-3 text-green-400" />
                </g>
              )}

              {/* 节点名称 */}
              <text
                x={pos.x}
                y={pos.y + 35}
                textAnchor="middle"
                className="text-xs fill-current"
                fill={isDiscovered ? "#fbbf24" : "#64748b"}
              >
                {isDiscovered ? node.name : "???"}
              </text>
            </g>
          )
        })}
      </svg>

      {/* 图例 */}
      <div className="absolute bottom-2 right-2 text-xs text-amber-200/70 space-y-1 bg-slate-950/80 p-2 rounded">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-amber-400" />
          <span>当前位置</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-orange-600" />
          <span>已探索</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-slate-700" />
          <span>未知</span>
        </div>
      </div>
    </div>
  )
}
