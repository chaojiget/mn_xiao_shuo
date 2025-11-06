import { useState, useCallback, useEffect } from "react"
import {
  GameState,
  GameAction,
  PlayerState,
  WorldState,
  Quest,
  InventoryItem,
  MapNode
} from "@/types/game"

/**
 * 游戏状态管理Hook
 * 提供状态读取、行动应用、存档等功能
 */
export const useGameState = (initialState?: GameState) => {
  const [gameState, setGameState] = useState<GameState | null>(initialState || null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // ==================== 状态读取 ====================

  const getPlayerState = useCallback((): PlayerState | null => {
    return gameState?.player || null
  }, [gameState])

  const getWorldState = useCallback((): WorldState | null => {
    return gameState?.world || null
  }, [gameState])

  const getQuests = useCallback((status?: Quest["status"]): Quest[] => {
    if (!gameState) return []
    if (status) {
      return gameState.quests.filter(q => q.status === status)
    }
    return gameState.quests
  }, [gameState])

  const getLocation = useCallback((locationId?: string): MapNode | null => {
    if (!gameState) return null
    const id = locationId || gameState.player.location
    return gameState.map.nodes.find(n => n.id === id) || null
  }, [gameState])

  const getInventoryItem = useCallback((itemId: string): InventoryItem | null => {
    if (!gameState) return null
    return gameState.player.inventory.find(i => i.id === itemId) || null
  }, [gameState])

  // ==================== 行动应用 ====================

  const applyAction = useCallback((action: GameAction) => {
    if (!gameState) return

    setGameState(prevState => {
      if (!prevState) return null

      const newState = { ...prevState }

      switch (action.type) {
        case "ADD_ITEM": {
          const existing = newState.player.inventory.find(i => i.id === action.itemId)
          if (existing) {
            existing.quantity += action.quantity || 1
          } else {
            // 需要从somewhere获取物品信息，这里暂时创建简单对象
            newState.player.inventory.push({
              id: action.itemId,
              name: action.itemId, // 临时：应该从数据库获取
              description: "",
              quantity: action.quantity || 1,
              type: "misc"
            })
          }
          break
        }

        case "REMOVE_ITEM": {
          const index = newState.player.inventory.findIndex(i => i.id === action.itemId)
          if (index !== -1) {
            const item = newState.player.inventory[index]
            if (item.quantity <= (action.quantity || 1)) {
              newState.player.inventory.splice(index, 1)
            } else {
              item.quantity -= action.quantity || 1
            }
          }
          break
        }

        case "UPDATE_HP": {
          const newHp = Math.max(0, Math.min(
            newState.player.maxHp,
            newState.player.hp + action.delta
          ))
          newState.player.hp = newHp
          break
        }

        case "UPDATE_STAMINA": {
          const newStamina = Math.max(0, Math.min(
            newState.player.maxStamina,
            newState.player.stamina + action.delta
          ))
          newState.player.stamina = newStamina
          break
        }

        case "SET_LOCATION": {
          newState.player.location = action.locationId
          newState.map.currentNodeId = action.locationId
          break
        }

        case "SET_FLAG": {
          newState.world.flags[action.key] = action.value
          break
        }

        case "UPDATE_QUEST": {
          const questIndex = newState.quests.findIndex(q => q.id === action.questId)
          if (questIndex !== -1) {
            newState.quests[questIndex] = {
              ...newState.quests[questIndex],
              ...action.updates
            }
          }
          break
        }

        case "DISCOVER_LOCATION": {
          const node = newState.map.nodes.find(n => n.id === action.locationId)
          if (node && !node.discovered) {
            node.discovered = true
            if (!newState.world.discoveredLocations.includes(action.locationId)) {
              newState.world.discoveredLocations.push(action.locationId)
            }
          }
          break
        }

        case "UNLOCK_LOCATION": {
          const node = newState.map.nodes.find(n => n.id === action.locationId)
          if (node) {
            node.locked = false
          }
          break
        }

        case "ADD_TRAIT": {
          if (!newState.player.traits.includes(action.trait)) {
            newState.player.traits.push(action.trait)
          }
          break
        }

        case "REMOVE_TRAIT": {
          const index = newState.player.traits.indexOf(action.trait)
          if (index !== -1) {
            newState.player.traits.splice(index, 1)
          }
          break
        }

        case "ADD_LOG": {
          newState.log.push({
            ...action.entry,
            turn: newState.world.time,
            timestamp: Date.now()
          })
          break
        }

        case "CUSTOM": {
          // 自定义行动处理
          console.warn("Custom action not handled:", action)
          break
        }
      }

      // 更新时间戳
      if (newState.metadata) {
        newState.metadata.updatedAt = Date.now()
      }

      return newState
    })
  }, [gameState])

  const applyActions = useCallback((actions: GameAction[]) => {
    actions.forEach(action => applyAction(action))
  }, [applyAction])

  // ==================== 状态初始化 ====================

  const initGame = useCallback((config?: Partial<GameState>) => {
    const defaultState: GameState = {
      version: "1.0.0",
      turn_number: 0,
      player: {
        hp: 100,
        maxHp: 100,
        stamina: 100,
        maxStamina: 100,
        traits: ["勇敢", "好奇"],
        inventory: [],
        location: "start",
        money: 50
      },
      world: {
        time: 0,
        flags: {},
        discoveredLocations: ["start"],
        variables: {}
      },
      quests: [],
      map: {
        nodes: [
          {
            id: "start",
            name: "起点",
            shortDesc: "一片空旷的广场",
            discovered: true,
            locked: false
          }
        ],
        edges: [],
        currentNodeId: "start"
      },
      log: [],
      metadata: {
        createdAt: Date.now(),
        updatedAt: Date.now(),
        playTime: 0
      }
    }

    const mergedState = config ? { ...defaultState, ...config } : defaultState
    setGameState(mergedState)
    return mergedState
  }, [])

  // ==================== 存档/读档 ====================

  const saveGame = useCallback((slotId: string = "auto") => {
    if (!gameState) {
      setError("无游戏状态可保存")
      return false
    }

    try {
      const saveData = JSON.stringify(gameState)
      localStorage.setItem(`game_save_${slotId}`, saveData)
      localStorage.setItem(`game_save_${slotId}_timestamp`, Date.now().toString())
      return true
    } catch (err) {
      setError("保存失败：" + (err instanceof Error ? err.message : String(err)))
      return false
    }
  }, [gameState])

  const loadGame = useCallback((slotId: string = "auto") => {
    try {
      const saveData = localStorage.getItem(`game_save_${slotId}`)
      if (!saveData) {
        setError("存档不存在")
        return false
      }

      const loadedState = JSON.parse(saveData) as GameState
      setGameState(loadedState)
      return true
    } catch (err) {
      setError("读档失败：" + (err instanceof Error ? err.message : String(err)))
      return false
    }
  }, [])

  const exportGame = useCallback((): string | null => {
    if (!gameState) return null
    return JSON.stringify(gameState, null, 2)
  }, [gameState])

  const importGame = useCallback((jsonData: string) => {
    try {
      const importedState = JSON.parse(jsonData) as GameState
      setGameState(importedState)
      return true
    } catch (err) {
      setError("导入失败：数据格式错误")
      return false
    }
  }, [])

  const listSaves = useCallback((): Array<{ slotId: string; timestamp: number }> => {
    const saves: Array<{ slotId: string; timestamp: number }> = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key?.startsWith("game_save_") && !key.endsWith("_timestamp")) {
        const slotId = key.replace("game_save_", "")
        const timestampStr = localStorage.getItem(`${key}_timestamp`)
        saves.push({
          slotId,
          timestamp: timestampStr ? parseInt(timestampStr) : 0
        })
      }
    }
    return saves.sort((a, b) => b.timestamp - a.timestamp)
  }, [])

  // ==================== 自动保存 ====================

  useEffect(() => {
    if (!gameState) return

    // 每30秒自动保存
    const interval = setInterval(() => {
      saveGame("auto")
    }, 30000)

    return () => clearInterval(interval)
  }, [gameState, saveGame])

  return {
    // 状态
    gameState,
    isLoading,
    error,

    // 读取器
    getPlayerState,
    getWorldState,
    getQuests,
    getLocation,
    getInventoryItem,

    // 行动
    applyAction,
    applyActions,

    // 初始化
    initGame,
    setGameState,

    // 存档
    saveGame,
    loadGame,
    exportGame,
    importGame,
    listSaves,

    // 工具
    clearError: () => setError(null)
  }
}