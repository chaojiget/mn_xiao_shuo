"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Loader2, Plus, MapPin, Building, Users, Swords } from "lucide-react"
import { WorldTree } from "./world-tree"
import { LocationCard } from "./location-card"
import { useWorld } from "@/hooks/use-world"

export function WorldManager() {
  const {
    worlds,
    currentWorld,
    regions,
    locations,
    factions,
    loading,
    error,
    generateWorld,
    generateLocations,
    selectWorld,
    selectRegion,
    selectedRegionId
  } = useWorld()

  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedLocationId, setSelectedLocationId] = useState<string | null>(null)

  // 生成世界表单
  const [worldForm, setWorldForm] = useState({
    novelId: "",
    theme: "",
    tone: "",
    novelType: "xianxia" as "scifi" | "xianxia",
    numRegions: 5,
    locationsPerRegion: 8,
    poisPerLocation: 5
  })

  const handleGenerateWorld = async () => {
    if (!worldForm.novelId || !worldForm.theme || !worldForm.tone) {
      alert("请填写所有必填字段")
      return
    }

    setIsGenerating(true)
    try {
      await generateWorld(worldForm)
      alert("世界生成成功！")
    } catch (err) {
      alert(`生成失败: ${err}`)
    } finally {
      setIsGenerating(false)
    }
  }

  const selectedLocation = locations.find(loc => loc.id === selectedLocationId)

  return (
    <div className="grid grid-cols-12 gap-6">
      {/* 左侧：世界树 */}
      <div className="col-span-3">
        <Card>
          <CardHeader>
            <CardTitle>世界结构</CardTitle>
            <CardDescription>
              {currentWorld ? currentWorld.name : "未选择世界"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!currentWorld ? (
              <div className="space-y-4">
                <Select onValueChange={(value) => selectWorld(value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择世界" />
                  </SelectTrigger>
                  <SelectContent>
                    {worlds.map((world) => (
                      <SelectItem key={world.id} value={world.id}>
                        {world.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    // 触发生成世界表单
                  }}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  创建新世界
                </Button>
              </div>
            ) : (
              <WorldTree
                world={currentWorld}
                regions={regions}
                onSelectRegion={selectRegion}
                selectedRegionId={selectedRegionId}
                onSelectLocation={setSelectedLocationId}
                selectedLocationId={selectedLocationId}
              />
            )}
          </CardContent>
        </Card>

        {/* 世界信息卡片 */}
        {currentWorld && (
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>世界信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div>
                <div className="font-medium">主题</div>
                <div className="text-muted-foreground">{currentWorld.theme}</div>
              </div>
              <div>
                <div className="font-medium">基调</div>
                <div className="text-muted-foreground">{currentWorld.tone}</div>
              </div>
              <div>
                <div className="font-medium">状态</div>
                <Badge variant={currentWorld.status === "published" ? "default" : "secondary"}>
                  {currentWorld.status}
                </Badge>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 中间：内容区 */}
      <div className="col-span-6">
        {!currentWorld ? (
          <Card>
            <CardHeader>
              <CardTitle>生成世界</CardTitle>
              <CardDescription>创建一个新的世界脚手架</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label>小说ID *</Label>
                  <Input
                    value={worldForm.novelId}
                    onChange={(e) => setWorldForm({ ...worldForm, novelId: e.target.value })}
                    placeholder="例如: novel-001"
                  />
                </div>

                <div>
                  <Label>主题 *</Label>
                  <Input
                    value={worldForm.theme}
                    onChange={(e) => setWorldForm({ ...worldForm, theme: e.target.value })}
                    placeholder="例如: dark survival, epic cultivation"
                  />
                </div>

                <div>
                  <Label>基调 *</Label>
                  <Input
                    value={worldForm.tone}
                    onChange={(e) => setWorldForm({ ...worldForm, tone: e.target.value })}
                    placeholder="例如: 冷冽压抑, 波澜壮阔"
                  />
                </div>

                <div>
                  <Label>小说类型</Label>
                  <Select
                    value={worldForm.novelType}
                    onValueChange={(value: "scifi" | "xianxia") =>
                      setWorldForm({ ...worldForm, novelType: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="scifi">科幻</SelectItem>
                      <SelectItem value="xianxia">玄幻/仙侠</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>区域数量</Label>
                    <Input
                      type="number"
                      min={3}
                      max={12}
                      value={worldForm.numRegions}
                      onChange={(e) =>
                        setWorldForm({ ...worldForm, numRegions: parseInt(e.target.value) })
                      }
                    />
                  </div>
                  <div>
                    <Label>每区域地点数</Label>
                    <Input
                      type="number"
                      min={5}
                      max={15}
                      value={worldForm.locationsPerRegion}
                      onChange={(e) =>
                        setWorldForm({ ...worldForm, locationsPerRegion: parseInt(e.target.value) })
                      }
                    />
                  </div>
                  <div>
                    <Label>每地点POI数</Label>
                    <Input
                      type="number"
                      min={3}
                      max={10}
                      value={worldForm.poisPerLocation}
                      onChange={(e) =>
                        setWorldForm({ ...worldForm, poisPerLocation: parseInt(e.target.value) })
                      }
                    />
                  </div>
                </div>

                <Button
                  className="w-full"
                  onClick={handleGenerateWorld}
                  disabled={isGenerating}
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      生成中...
                    </>
                  ) : (
                    "生成世界"
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : selectedLocation ? (
          <LocationCard location={selectedLocation} />
        ) : selectedRegionId ? (
          <Card>
            <CardHeader>
              <CardTitle>区域地点</CardTitle>
              <CardDescription>
                {regions.find((r) => r.id === selectedRegionId)?.name}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-2">
                  {locations.length === 0 ? (
                    <div className="text-center text-muted-foreground py-8">
                      该区域暂无地点
                      <div className="mt-4">
                        <Button
                          size="sm"
                          onClick={() => {
                            if (selectedRegionId) {
                              generateLocations(selectedRegionId, 8)
                            }
                          }}
                        >
                          <Plus className="mr-2 h-4 w-4" />
                          生成地点
                        </Button>
                      </div>
                    </div>
                  ) : (
                    locations.map((loc) => (
                      <Card
                        key={loc.id}
                        className="cursor-pointer hover:bg-accent"
                        onClick={() => setSelectedLocationId(loc.id)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="font-medium">{loc.name}</div>
                              <div className="text-sm text-muted-foreground">{loc.type}</div>
                            </div>
                            <Badge variant="outline">细化等级 {loc.detail_level}</Badge>
                          </div>
                          {loc.macro_description && (
                            <p className="text-sm text-muted-foreground mt-2">
                              {loc.macro_description}
                            </p>
                          )}
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="flex items-center justify-center h-[600px]">
              <div className="text-center text-muted-foreground">
                <MapPin className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>请从左侧选择区域或地点</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 右侧：派系、物品等 */}
      <div className="col-span-3">
        <Tabs defaultValue="factions">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="factions">
              <Users className="h-4 w-4" />
            </TabsTrigger>
            <TabsTrigger value="items">
              <Swords className="h-4 w-4" />
            </TabsTrigger>
            <TabsTrigger value="creatures">
              <Building className="h-4 w-4" />
            </TabsTrigger>
          </TabsList>

          <TabsContent value="factions">
            <Card>
              <CardHeader>
                <CardTitle>派系</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[500px]">
                  {factions.length === 0 ? (
                    <div className="text-center text-muted-foreground py-8">暂无派系</div>
                  ) : (
                    <div className="space-y-3">
                      {factions.map((faction) => (
                        <Card key={faction.id}>
                          <CardContent className="p-3">
                            <div className="font-medium">{faction.name}</div>
                            <div className="text-xs text-muted-foreground mt-1">
                              {faction.purpose}
                            </div>
                            <div className="mt-2 flex items-center gap-2">
                              <Badge variant="outline" className="text-xs">
                                势力 {faction.power_level}
                              </Badge>
                              <Badge
                                variant={
                                  faction.status === "active" ? "default" : "secondary"
                                }
                                className="text-xs"
                              >
                                {faction.status}
                              </Badge>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="items">
            <Card>
              <CardHeader>
                <CardTitle>物品</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center text-muted-foreground py-8">功能开发中...</div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="creatures">
            <Card>
              <CardHeader>
                <CardTitle>生物</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center text-muted-foreground py-8">功能开发中...</div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
