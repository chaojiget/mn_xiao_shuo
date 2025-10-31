/**
 * 自动生成设定 Hook
 */

import { useState, useCallback } from 'react'
import { apiClient } from '@/lib/api-client'
import type { NovelSettings, NPC } from '@/lib/types'
import { useNovelStore } from '@/stores/novel-store'
import { useToast } from './use-toast'

export function useAutoGenerate() {
  const [isGenerating, setIsGenerating] = useState(false)
  const { toast } = useToast()

  const currentNovel = useNovelStore((state) => state.currentNovel)
  const updateNovelSettings = useNovelStore((state) => state.updateNovelSettings)
  const addMessage = useNovelStore((state) => state.addMessage)

  /**
   * 自动生成小说设定
   */
  const generateSetting = useCallback(
    async (title: string, novelType: 'scifi' | 'xianxia', userPrompt?: string) => {
      if (!title.trim()) {
        toast({
          title: '标题不能为空',
          variant: 'destructive',
        })
        return null
      }

      setIsGenerating(true)

      try {
        const response = await apiClient.generateSetting({
          title,
          novel_type: novelType,
          user_prompt: userPrompt,
        })

        if (response.success && response.setting) {
          const generated = response.setting

          // 更新设定
          const newSettings: NovelSettings = {
            title,
            type: novelType,
            background: generated.world_setting,
            protagonist: generated.protagonist.background,
            protagonistName: generated.protagonist.name,
            protagonistRole: generated.protagonist.role,
            protagonistAbilities: generated.protagonist.abilities || [],
            npcs: generated.npcs || [],
          }

          updateNovelSettings(newSettings)

          // 显示成功消息
          addMessage({
            role: 'system',
            content: `✅ 自动生成成功！\n\n📖 世界观已创建\n👤 主角：${generated.protagonist.name}（${generated.protagonist.role}）\n🎭 NPC：${generated.npcs.map((n: NPC) => n.name).join('、')}`,
            timestamp: new Date(),
          })

          toast({
            title: '✅ 生成成功',
            description: `已为《${title}》创建完整设定`,
          })

          setIsGenerating(false)
          return newSettings
        } else {
          throw new Error(response.error || '生成失败')
        }
      } catch (error: any) {
        console.error('生成设定失败:', error)

        toast({
          title: '生成失败',
          description: error.message || '请稍后重试',
          variant: 'destructive',
        })

        setIsGenerating(false)
        return null
      }
    },
    [updateNovelSettings, addMessage, toast]
  )

  /**
   * 优化已有设定
   */
  const optimizeSetting = useCallback(
    async (optimizationRequest: string) => {
      if (!currentNovel) {
        toast({
          title: '没有当前小说',
          variant: 'destructive',
        })
        return null
      }

      setIsGenerating(true)

      try {
        const response = await apiClient.optimizeSetting({
          current_setting: currentNovel,
          optimization_request: optimizationRequest,
        })

        if (response.success && response.optimized_setting) {
          updateNovelSettings(response.optimized_setting)

          toast({
            title: '✅ 优化成功',
            description: '设定已更新',
          })

          setIsGenerating(false)
          return response.optimized_setting
        } else {
          throw new Error(response.error || '优化失败')
        }
      } catch (error: any) {
        console.error('优化设定失败:', error)

        toast({
          title: '优化失败',
          description: error.message || '请稍后重试',
          variant: 'destructive',
        })

        setIsGenerating(false)
        return null
      }
    },
    [currentNovel, updateNovelSettings, toast]
  )

  return {
    isGenerating,
    generateSetting,
    optimizeSetting,
  }
}
