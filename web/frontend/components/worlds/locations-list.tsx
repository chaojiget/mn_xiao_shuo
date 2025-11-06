"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MapPin, Eye } from "lucide-react"

interface LocationsListProps {
  locations: any[]
}

export function LocationsList({ locations }: LocationsListProps) {
  const getBiomeColor = (biome: string) => {
    const colors: Record<string, string> = {
      forest: "bg-green-700",
      desert: "bg-yellow-700",
      swamp: "bg-teal-700",
      mountain: "bg-gray-700",
      plains: "bg-amber-700",
      sea: "bg-blue-700",
      city: "bg-purple-700",
    }
    return colors[biome] || "bg-slate-700"
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {locations.map((location) => (
        <Card key={location.id} className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <div className="flex items-start justify-between">
              <CardTitle className="text-white text-lg">{location.name}</CardTitle>
              <Badge className={getBiomeColor(location.biome)}>
                {location.biome}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {location.description && (
              <p className="text-sm text-gray-300 line-clamp-3">
                {location.description}
              </p>
            )}

            <div className="flex items-center gap-4 text-sm text-gray-400">
              <div className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                ({location.coord.x}, {location.coord.y})
              </div>
              <div className="flex items-center gap-1">
                <Eye className="h-4 w-4" />
                {location.pois?.length || 0} POI
              </div>
            </div>

            {location.npcs && location.npcs.length > 0 && (
              <div className="pt-2 border-t border-slate-700">
                <div className="text-xs text-gray-500 mb-1">NPC:</div>
                <div className="text-sm text-gray-300">
                  {location.npcs.length} 个角色
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
