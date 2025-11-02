"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Eye, Ear, Wind, Hand, Thermometer, Zap, Loader2 } from "lucide-react"
import { useState } from "react"

interface LocationCardProps {
  location: any
}

export function LocationCard({ location }: LocationCardProps) {
  const [isRefining, setIsRefining] = useState(false)
  const [refinedData, setRefinedData] = useState<any>(null)

  const handleRefine = async () => {
    setIsRefining(true)
    try {
      const response = await fetch(`http://localhost:8000/api/world/location/${location.id}/refine`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          location_id: location.id,
          turn: 0,
          target_detail_level: 2,
          passes: ["structure", "sensory", "affordance", "cinematic"]
        })
      })

      const result = await response.json()
      setRefinedData(result)
      alert("细化完成！")
    } catch (err) {
      alert(`细化失败: ${err}`)
    } finally {
      setIsRefining(false)
    }
  }

  const sensoryIcons = {
    visual: Eye,
    auditory: Ear,
    olfactory: Wind,
    tactile: Hand,
    temperature: Thermometer
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle>{location.name}</CardTitle>
              <CardDescription className="mt-1">
                {location.type} · 访问次数: {location.visit_count}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">细化等级 {location.detail_level}/3</Badge>
              <Badge variant={location.canon_locked ? "destructive" : "secondary"}>
                {location.canon_locked ? "已锁定" : "草稿"}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {location.macro_description && (
            <p className="text-sm text-muted-foreground mb-4">{location.macro_description}</p>
          )}

          <Button onClick={handleRefine} disabled={isRefining}>
            {isRefining ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                细化中...
              </>
            ) : (
              <>
                <Zap className="mr-2 h-4 w-4" />
                细化场景
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      <Tabs defaultValue="geometry">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="geometry">几何</TabsTrigger>
          <TabsTrigger value="sensory">感官</TabsTrigger>
          <TabsTrigger value="affordances">可供性</TabsTrigger>
          <TabsTrigger value="pois">POI</TabsTrigger>
        </TabsList>

        <TabsContent value="geometry">
          <Card>
            <CardHeader>
              <CardTitle>几何特征</CardTitle>
            </CardHeader>
            <CardContent>
              {location.geometry && location.geometry.length > 0 ? (
                <ul className="space-y-2">
                  {location.geometry.map((item: string, index: number) => (
                    <li key={index} className="text-sm flex items-start gap-2">
                      <span className="text-muted-foreground">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-sm text-muted-foreground">暂无几何特征</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sensory">
          <Card>
            <CardHeader>
              <CardTitle>感官节点</CardTitle>
            </CardHeader>
            <CardContent>
              {location.sensory && location.sensory.length > 0 ? (
                <ul className="space-y-2">
                  {location.sensory.map((item: string, index: number) => (
                    <li key={index} className="text-sm flex items-start gap-2">
                      <span className="text-muted-foreground">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              ) : refinedData?.layers?.find((l: any) => l.layer_type === "sensory") ? (
                <div className="space-y-3">
                  {refinedData.layers
                    .find((l: any) => l.layer_type === "sensory")
                    .content.sensory_nodes.map((node: any, index: number) => {
                      const Icon = sensoryIcons[node.sense as keyof typeof sensoryIcons] || Eye
                      return (
                        <div key={index} className="flex items-start gap-3">
                          <Icon className="h-4 w-4 mt-0.5 text-muted-foreground" />
                          <div>
                            <div className="text-xs font-medium text-muted-foreground uppercase">
                              {node.sense}
                            </div>
                            <div className="text-sm">{node.content}</div>
                          </div>
                        </div>
                      )
                    })}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">暂无感官节点，请先细化场景</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="affordances">
          <Card>
            <CardHeader>
              <CardTitle>可供性（可做之事）</CardTitle>
            </CardHeader>
            <CardContent>
              {location.affordances && location.affordances.length > 0 ? (
                <div className="space-y-3">
                  {location.affordances.map((item: string, index: number) => (
                    <Badge key={index} variant="outline">
                      {item}
                    </Badge>
                  ))}
                </div>
              ) : refinedData?.affordances && refinedData.affordances.length > 0 ? (
                <div className="space-y-3">
                  {refinedData.affordances.map((aff: any, index: number) => (
                    <Card key={index} className="p-3">
                      <div className="font-medium text-sm">
                        {aff.verb} {aff.object}
                      </div>
                      {aff.requirement && (
                        <div className="text-xs text-muted-foreground mt-1">
                          前提: {JSON.stringify(aff.requirement)}
                        </div>
                      )}
                      {aff.risk && (
                        <div className="text-xs text-yellow-600 mt-1">⚠️ {aff.risk}</div>
                      )}
                      {aff.expected_outcome && (
                        <div className="text-xs text-green-600 mt-1">→ {aff.expected_outcome}</div>
                      )}
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">暂无可供性，请先细化场景</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pois">
          <Card>
            <CardHeader>
              <CardTitle>兴趣点（POI）</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">POI列表功能开发中...</div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {refinedData?.narrative_text && (
        <Card>
          <CardHeader>
            <CardTitle>生成的叙事文本</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {refinedData.narrative_text}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
