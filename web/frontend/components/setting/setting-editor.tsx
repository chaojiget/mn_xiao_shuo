"use client"

import { useState } from "react"
import { Settings, Globe, User, MapPin, Users, BookMarked, Save, Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"

interface SettingEditorProps {
  novelType: "scifi" | "xianxia"
  onSave?: (setting: any) => void
}

export function SettingEditor({ novelType, onSave }: SettingEditorProps) {
  const [worldSetting, setWorldSetting] = useState({
    title: "",
    settingText: "",
    timeline: ""
  })

  const [protagonist, setProtagonist] = useState({
    name: "",
    role: "",
    description: "",
    attributes: {} as Record<string, number>,
    resources: {} as Record<string, number>
  })

  const [locations, setLocations] = useState<Array<{
    id: string
    name: string
    description: string
  }>>([])

  const [factions, setFactions] = useState<Array<{
    id: string
    name: string
    description: string
  }>>([])

  const typeConfig = novelType === "scifi" ? {
    attributeNames: ["智力", "技术", "战斗", "社交", "探索"],
    resourceNames: ["能量", "资金", "情报", "装备"],
    exampleTitle: "深空迷航",
    exampleSetting: "2157年，人类殖民计划遭遇未知危机...",
    exampleRole: "工程师"
  } : {
    attributeNames: ["灵力", "体魄", "悟性", "意志", "魅力"],
    resourceNames: ["灵石", "丹药", "功法点", "声望"],
    exampleTitle: "逆天改命录",
    exampleSetting: "一个凡人少年在修仙界逆天崛起...",
    exampleRole: "外门弟子"
  }

  const addLocation = () => {
    setLocations([...locations, {
      id: `loc_${Date.now()}`,
      name: "",
      description: ""
    }])
  }

  const removeLocation = (id: string) => {
    setLocations(locations.filter(loc => loc.id !== id))
  }

  const addFaction = () => {
    setFactions([...factions, {
      id: `fac_${Date.now()}`,
      name: "",
      description: ""
    }])
  }

  const removeFaction = (id: string) => {
    setFactions(factions.filter(fac => fac.id !== id))
  }

  const handleSave = () => {
    const setting = {
      worldSetting,
      protagonist,
      locations,
      factions
    }
    onSave?.(setting)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              设定编辑器
            </CardTitle>
            <CardDescription>
              {novelType === "scifi" ? "科幻小说" : "玄幻/仙侠"}设定 - 主角将通过探索逐步发现世界真相
            </CardDescription>
          </div>
          <Button onClick={handleSave} className="flex items-center gap-2">
            <Save className="w-4 h-4" />
            保存设定
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="world" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="world" className="flex items-center gap-2">
              <Globe className="w-4 h-4" />
              世界观
            </TabsTrigger>
            <TabsTrigger value="protagonist" className="flex items-center gap-2">
              <User className="w-4 h-4" />
              主角
            </TabsTrigger>
            <TabsTrigger value="locations" className="flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              地点
            </TabsTrigger>
            <TabsTrigger value="factions" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              势力
            </TabsTrigger>
          </TabsList>

          {/* 世界观 */}
          <TabsContent value="world" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">小说标题</Label>
              <Input
                id="title"
                placeholder={typeConfig.exampleTitle}
                value={worldSetting.title}
                onChange={(e) => setWorldSetting({...worldSetting, title: e.target.value})}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="setting">世界背景 (300-500字)</Label>
              <Textarea
                id="setting"
                placeholder={typeConfig.exampleSetting}
                className="min-h-[200px]"
                value={worldSetting.settingText}
                onChange={(e) => setWorldSetting({...worldSetting, settingText: e.target.value})}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="timeline">时间线</Label>
              <Input
                id="timeline"
                placeholder={novelType === "scifi" ? "2157年，第三次殖民浪潮" : "灵纪三千年，大劫将至"}
                value={worldSetting.timeline}
                onChange={(e) => setWorldSetting({...worldSetting, timeline: e.target.value})}
              />
            </div>
          </TabsContent>

          {/* 主角 */}
          <TabsContent value="protagonist" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="protagonist-name">姓名</Label>
                <Input
                  id="protagonist-name"
                  placeholder="主角名字"
                  value={protagonist.name}
                  onChange={(e) => setProtagonist({...protagonist, name: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="protagonist-role">职业/境界</Label>
                <Input
                  id="protagonist-role"
                  placeholder={typeConfig.exampleRole}
                  value={protagonist.role}
                  onChange={(e) => setProtagonist({...protagonist, role: e.target.value})}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="protagonist-desc">角色描述</Label>
              <Textarea
                id="protagonist-desc"
                placeholder="主角的背景、性格、目标..."
                className="min-h-[120px]"
                value={protagonist.description}
                onChange={(e) => setProtagonist({...protagonist, description: e.target.value})}
              />
            </div>

            <div className="space-y-2">
              <Label>属性 (0-10)</Label>
              <div className="grid grid-cols-2 gap-3">
                {typeConfig.attributeNames.map(attr => (
                  <div key={attr} className="flex items-center gap-2">
                    <Label className="w-16 text-sm">{attr}</Label>
                    <Input
                      type="number"
                      min="0"
                      max="10"
                      value={protagonist.attributes[attr] || 5}
                      onChange={(e) => setProtagonist({
                        ...protagonist,
                        attributes: {...protagonist.attributes, [attr]: Number(e.target.value)}
                      })}
                      className="flex-1"
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label>初始资源</Label>
              <div className="grid grid-cols-2 gap-3">
                {typeConfig.resourceNames.map(resource => (
                  <div key={resource} className="flex items-center gap-2">
                    <Label className="w-16 text-sm">{resource}</Label>
                    <Input
                      type="number"
                      min="0"
                      value={protagonist.resources[resource] || 10}
                      onChange={(e) => setProtagonist({
                        ...protagonist,
                        resources: {...protagonist.resources, [resource]: Number(e.target.value)}
                      })}
                      className="flex-1"
                    />
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* 地点 */}
          <TabsContent value="locations" className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                定义世界中的重要地点。主角最初不知道这些地点，需要通过探索发现。
              </p>
              <Button onClick={addLocation} size="sm" variant="outline">
                <Plus className="w-4 h-4 mr-2" />
                添加地点
              </Button>
            </div>

            <div className="space-y-4">
              {locations.map((location, index) => (
                <Card key={location.id}>
                  <CardContent className="pt-6 space-y-3">
                    <div className="flex items-center justify-between">
                      <Label>地点 {index + 1}</Label>
                      <Button
                        onClick={() => removeLocation(location.id)}
                        size="sm"
                        variant="ghost"
                        className="text-destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>

                    <Input
                      placeholder="地点名称"
                      value={location.name}
                      onChange={(e) => {
                        const updated = [...locations]
                        updated[index].name = e.target.value
                        setLocations(updated)
                      }}
                    />

                    <Textarea
                      placeholder="地点描述、秘密、重要性..."
                      value={location.description}
                      onChange={(e) => {
                        const updated = [...locations]
                        updated[index].description = e.target.value
                        setLocations(updated)
                      }}
                      className="min-h-[80px]"
                    />
                  </CardContent>
                </Card>
              ))}

              {locations.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  暂无地点，点击"添加地点"开始
                </div>
              )}
            </div>
          </TabsContent>

          {/* 势力 */}
          <TabsContent value="factions" className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                定义世界中的势力/组织。主角将在冒险中逐步了解这些势力。
              </p>
              <Button onClick={addFaction} size="sm" variant="outline">
                <Plus className="w-4 h-4 mr-2" />
                添加势力
              </Button>
            </div>

            <div className="space-y-4">
              {factions.map((faction, index) => (
                <Card key={faction.id}>
                  <CardContent className="pt-6 space-y-3">
                    <div className="flex items-center justify-between">
                      <Label>势力 {index + 1}</Label>
                      <Button
                        onClick={() => removeFaction(faction.id)}
                        size="sm"
                        variant="ghost"
                        className="text-destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>

                    <Input
                      placeholder="势力名称"
                      value={faction.name}
                      onChange={(e) => {
                        const updated = [...factions]
                        updated[index].name = e.target.value
                        setFactions(updated)
                      }}
                    />

                    <Textarea
                      placeholder="势力描述、目标、立场、势力范围..."
                      value={faction.description}
                      onChange={(e) => {
                        const updated = [...factions]
                        updated[index].description = e.target.value
                        setFactions(updated)
                      }}
                      className="min-h-[80px]"
                    />
                  </CardContent>
                </Card>
              ))}

              {factions.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  暂无势力，点击"添加势力"开始
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
