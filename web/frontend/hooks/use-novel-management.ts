/**
 * 小说管理 Hook - 处理保存、加载、删除等操作
 */

import { useState, useCallback, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import type { Novel, NovelSettings } from '@/lib/types'
import { useNovelStore } from '@/stores/novel-store'
import { useToast } from './use-toast'

export function useNovelManagement() {
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const { toast } = useToast()

  const novels = useNovelStore((state) => state.novels)
  const setNovels = useNovelStore((state) => state.setNovels)
  const addNovel = useNovelStore((state) => state.addNovel)
  const currentNovel = useNovelStore((state) => state.currentNovel)
  const setCurrentNovel = useNovelStore((state) => state.setCurrentNovel)

  /**
   * 加载小说列表
   */
  const loadNovels = useCallback(async () => {
    setIsLoading(true)

    try {
      const response = await apiClient.getNovels()
      setNovels(response.novels || [])
      setIsLoading(false)
    } catch (error: any) {
      console.error('加载小说列表失败:', error)
      toast({
        title: '加载失败',
        description: error.message,
        variant: 'destructive',
      })
      setIsLoading(false)
    }
  }, [setNovels, toast])

  /**
   * 创建新小说
   */
  const createNovel = useCallback(
    async (title: string, novelType: 'scifi' | 'xianxia', settings?: NovelSettings) => {
      setIsSaving(true)

      try {
        const response = await apiClient.createNovel({
          title,
          novel_type: novelType,
          preference: 'hybrid',
          settings,
        })

        const newNovel: Novel = {
          id: response.novel_id,
          title: response.title,
          type: response.type as 'scifi' | 'xianxia',
          chapters: 0,
          created_at: new Date().toISOString(),
          settings,
        }

        addNovel(newNovel)

        toast({
          title: '✅ 创建成功',
          description: `小说《${title}》已创建`,
        })

        setIsSaving(false)
        return newNovel
      } catch (error: any) {
        console.error('创建小说失败:', error)
        toast({
          title: '创建失败',
          description: error.message,
          variant: 'destructive',
        })
        setIsSaving(false)
        return null
      }
    },
    [addNovel, toast]
  )

  /**
   * 保存当前小说设定
   */
  const saveCurrentNovel = useCallback(async () => {
    if (!currentNovel?.id) {
      // 如果没有 ID，说明是新创建的，需要先创建
      if (currentNovel?.title && currentNovel?.type) {
        return await createNovel(currentNovel.title, currentNovel.type, currentNovel)
      }
      toast({
        title: '无法保存',
        description: '当前没有可保存的小说',
        variant: 'destructive',
      })
      return null
    }

    setIsSaving(true)

    try {
      await apiClient.updateNovel(currentNovel.id, currentNovel)

      toast({
        title: '✅ 保存成功',
        description: '小说设定已更新',
      })

      setIsSaving(false)
      return true
    } catch (error: any) {
      console.error('保存小说失败:', error)
      toast({
        title: '保存失败',
        description: error.message,
        variant: 'destructive',
      })
      setIsSaving(false)
      return false
    }
  }, [currentNovel, createNovel, toast])

  /**
   * 加载指定小说
   */
  const loadNovel = useCallback(
    async (novelId: string) => {
      setIsLoading(true)

      try {
        const novel = await apiClient.getNovel(novelId)

        if (novel.settings) {
          setCurrentNovel(novel.settings)
        }

        toast({
          title: '✅ 加载成功',
          description: `已加载《${novel.title}》`,
        })

        setIsLoading(false)
        return novel
      } catch (error: any) {
        console.error('加载小说失败:', error)
        toast({
          title: '加载失败',
          description: error.message,
          variant: 'destructive',
        })
        setIsLoading(false)
        return null
      }
    },
    [setCurrentNovel, toast]
  )

  /**
   * 删除小说
   */
  const deleteNovel = useCallback(
    async (novelId: string) => {
      try {
        await apiClient.deleteNovel(novelId)

        // 从列表中移除
        setNovels(novels.filter((n) => n.id !== novelId))

        toast({
          title: '✅ 删除成功',
        })

        return true
      } catch (error: any) {
        console.error('删除小说失败:', error)
        toast({
          title: '删除失败',
          description: error.message,
          variant: 'destructive',
        })
        return false
      }
    },
    [novels, setNovels, toast]
  )

  /**
   * 导出小说
   */
  const exportNovel = useCallback(
    async (novelId: string) => {
      try {
        const response = await apiClient.exportNovel(novelId)

        // 创建下载
        const blob = new Blob([response.markdown], { type: 'text/markdown' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `novel_${novelId}.md`
        a.click()
        URL.revokeObjectURL(url)

        toast({
          title: '✅ 导出成功',
        })

        return true
      } catch (error: any) {
        console.error('导出小说失败:', error)
        toast({
          title: '导出失败',
          description: error.message,
          variant: 'destructive',
        })
        return false
      }
    },
    [toast]
  )

  // 自动加载小说列表
  useEffect(() => {
    loadNovels()
  }, [])

  return {
    novels,
    currentNovel,
    isLoading,
    isSaving,
    loadNovels,
    createNovel,
    saveCurrentNovel,
    loadNovel,
    deleteNovel,
    exportNovel,
  }
}
