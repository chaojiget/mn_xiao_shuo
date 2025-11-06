/**
 * 保存游戏对话框组件
 */

'use client';

import { useState } from 'react';
import { Save, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { apiClient } from '@/lib/api-client';

interface SaveGameDialogProps {
  gameState: any;
  onSaveSuccess?: () => void;
  trigger?: React.ReactNode;
}

export function SaveGameDialog({ gameState, onSaveSuccess, trigger }: SaveGameDialogProps) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [slotId, setSlotId] = useState<number>(1);
  const [saveName, setSaveName] = useState('');

  const handleSave = async () => {
    if (!saveName.trim()) {
      alert('请输入存档名称');
      return;
    }

    try {
      setSaving(true);

      const response = await apiClient.saveGame({
        slot_id: slotId,
        save_name: saveName.trim(),
        game_state: gameState,
      });

      if (response.success) {
        setOpen(false);
        setSaveName('');
        onSaveSuccess?.();
        alert('保存成功！');
      }
    } catch (error: any) {
      console.error('保存失败:', error);
      alert(error.message || '保存失败，请重试');
    } finally {
      setSaving(false);
    }
  };

  // 生成默认存档名称
  const generateDefaultName = () => {
    const location = gameState?.player?.location || '未知地点';
    const turn = gameState?.world?.time || gameState?.turn_number || 0;
    return `${location} - 第${turn}回合`;
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm">
            <Save className="w-4 h-4 mr-2" />
            保存游戏
          </Button>
        )}
      </DialogTrigger>

      <DialogContent className="bg-slate-800 border-slate-700 text-white sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>保存游戏</DialogTitle>
          <DialogDescription className="text-gray-400">
            选择存档槽位并为存档命名
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* 槽位选择 */}
          <div className="space-y-2">
            <Label htmlFor="slot">存档槽位</Label>
            <Select
              value={slotId.toString()}
              onValueChange={(value) => setSlotId(parseInt(value))}
            >
              <SelectTrigger
                id="slot"
                className="bg-slate-700 border-slate-600 text-white"
              >
                <SelectValue placeholder="选择槽位" />
              </SelectTrigger>
              <SelectContent className="bg-slate-700 border-slate-600">
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((slot) => (
                  <SelectItem
                    key={slot}
                    value={slot.toString()}
                    className="text-white hover:bg-slate-600"
                  >
                    槽位 {slot}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* 存档名称 */}
          <div className="space-y-2">
            <Label htmlFor="name">存档名称</Label>
            <Input
              id="name"
              placeholder={generateDefaultName()}
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              className="bg-slate-700 border-slate-600 text-white placeholder:text-gray-500"
              disabled={saving}
            />
            <p className="text-xs text-gray-500">
              留空将使用默认名称
            </p>
          </div>

          {/* 当前状态信息 */}
          <div className="bg-slate-700/50 rounded-lg p-3 text-sm space-y-1">
            <div className="flex justify-between text-gray-300">
              <span>位置:</span>
              <span className="text-white font-medium">
                {gameState?.player?.location || '未知'}
              </span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>回合:</span>
              <span className="text-white font-medium">
                第 {gameState?.world?.time || gameState?.turn_number || 0} 回合
              </span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>生命值:</span>
              <span className="text-white font-medium">
                {gameState?.player?.hp || 100} / {gameState?.player?.maxHp || 100}
              </span>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
            disabled={saving}
            className="bg-slate-700 hover:bg-slate-600 text-white border-slate-600"
          >
            取消
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving}
            className="bg-purple-600 hover:bg-purple-700"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                保存中...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                保存
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
