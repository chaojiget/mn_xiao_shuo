"use client"

import { useEffect, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api-client"

interface LoreEditorDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  worldId: string
  lore: Record<string, string>
  onSaved?: () => void
}

export function LoreEditorDialog({ open, onOpenChange, worldId, lore, onSaved }: LoreEditorDialogProps) {
  const { toast } = useToast()
  const [items, setItems] = useState<Array<{ key: string; value: string }>>([])

  useEffect(() => {
    const entries = Object.entries(lore || {})
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => ({ key: k, value: v }))
    setItems(entries)
  }, [lore])

  const addRow = () => setItems(prev => [...prev, { key: "", value: "" }])
  const removeRow = (idx: number) => setItems(prev => prev.filter((_, i) => i !== idx))
  const updateKey = (idx: number, key: string) => setItems(prev => prev.map((it, i) => i === idx ? { ...it, key } : it))
  const updateValue = (idx: number, value: string) => setItems(prev => prev.map((it, i) => i === idx ? { ...it, value } : it))

  const handleSave = async () => {
    try {
      // 计算变更：entries 为非空 key/value；delete_keys 为原有中被移除的 key
      const newMap: Record<string, string> = {}
      const invalid = items.find(it => (it.key.trim().length === 0 && it.value.trim().length > 0))
      if (invalid) {
        toast({ title: "请填写条目名称", description: "存在内容但缺少名称的条目", variant: "destructive" })
        return
      }
      for (const it of items) {
        const k = it.key.trim()
        if (k.length > 0) newMap[k] = it.value
      }

      const deleteKeys = Object.keys(lore || {}).filter(k => !(k in newMap))

      await apiClient.request(`/api/worlds/${worldId}/lore`, {
        method: 'PATCH',
        body: JSON.stringify({ entries: newMap, delete_keys: deleteKeys })
      })

      toast({ title: "已保存", description: "世界设定已更新" })
      onOpenChange(false)
      onSaved?.()
    } catch (e) {
      toast({ title: "保存失败", description: String(e), variant: "destructive" })
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-800 border-slate-700 max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-white">编辑世界设定（Lore）</DialogTitle>
          <DialogDescription className="text-gray-400">新增、修改或删除设定条目</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
          {items.map((it, idx) => (
            <div key={idx} className="grid grid-cols-1 md:grid-cols-5 gap-3 items-start">
              <div className="md:col-span-2 space-y-1">
                <Label className="text-gray-300">名称</Label>
                <Input value={it.key} onChange={(e) => updateKey(idx, e.target.value)} className="bg-slate-700 border-slate-600 text-white" placeholder="如：世界观、魔法体系" />
              </div>
              <div className="md:col-span-3 space-y-1">
                <Label className="text-gray-300">内容</Label>
                <Textarea value={it.value} onChange={(e) => updateValue(idx, e.target.value)} className="bg-slate-700 border-slate-600 text-white min-h-[96px]" placeholder="详细描述..." />
              </div>
              <div className="md:col-span-5 flex justify-end">
                <Button variant="outline" className="border-red-500/40 text-red-300 hover:bg-red-500/10" onClick={() => removeRow(idx)}>
                  删除
                </Button>
              </div>
            </div>
          ))}

          <div>
            <Button variant="outline" onClick={addRow}>新增条目</Button>
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={handleSave} className="bg-purple-600 hover:bg-purple-700">保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

