import { useState, useCallback } from "react"
import { NovelSettings, NPC } from "@/types"
import { apiClient } from "@/lib/api-client"

export const useNovelSettings = () => {
  const [settings, setSettings] = useState<NovelSettings>({
    title: "",
    type: "scifi",
    protagonist: "",
    background: "",
    npcs: []
  })
  const [isGenerating, setIsGenerating] = useState(false)

  const updateSetting = useCallback((updates: Partial<NovelSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }))
  }, [])

  const generateSetting = useCallback(async (title: string, type: "scifi" | "xianxia") => {
    if (!title.trim()) {
      throw new Error("请先输入小说标题")
    }

    setIsGenerating(true)

    try {
      const result = await apiClient.generateSetting({
        title,
        novel_type: type
      })

      if (result.success && result.setting) {
        const generated = result.setting

        // 更新设定
        setSettings({
          title,
          type,
          background: generated.world_setting || generated.background,
          protagonist: generated.protagonist.background || generated.protagonist,
          protagonistName: generated.protagonist.name,
          protagonistRole: generated.protagonist.role,
          protagonistAbilities: generated.protagonist.abilities,
          npcs: generated.npcs || []
        })

        return result.setting
      } else {
        throw new Error(result.error || "生成失败")
      }
    } catch (error) {
      console.error("生成设定失败:", error)
      throw error
    } finally {
      setIsGenerating(false)
    }
  }, [])

  const resetSettings = useCallback(() => {
    setSettings({
      title: "",
      type: "scifi",
      protagonist: "",
      background: "",
      npcs: []
    })
  }, [])

  const validateSettings = useCallback((): string | null => {
    if (!settings.title.trim()) return "请输入小说标题"
    if (!settings.background.trim()) return "请完善世界观设定"
    if (!settings.protagonist.trim()) return "请完善主角设定"
    return null
  }, [settings])

  const addNPC = useCallback((npc: NPC) => {
    setSettings(prev => ({
      ...prev,
      npcs: [...(prev.npcs || []), npc]
    }))
  }, [])

  const removeNPC = useCallback((npcId: string) => {
    setSettings(prev => ({
      ...prev,
      npcs: prev.npcs?.filter(npc => npc.id !== npcId) || []
    }))
  }, [])

  const updateNPC = useCallback((npcId: string, updates: Partial<NPC>) => {
    setSettings(prev => ({
      ...prev,
      npcs: prev.npcs?.map(npc =>
        npc.id === npcId ? { ...npc, ...updates } : npc
      ) || []
    }))
  }, [])

  return {
    settings,
    isGenerating,
    updateSetting,
    generateSetting,
    resetSettings,
    validateSettings,
    addNPC,
    removeNPC,
    updateNPC
  }
}