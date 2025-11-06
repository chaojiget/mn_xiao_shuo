"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { User, MapPin, Heart, Lock } from "lucide-react"

interface NpcsListProps {
  npcs: any[]
  locations: any[]
}

export function NpcsList({ npcs, locations }: NpcsListProps) {
  const getLocationName = (locationId: string | null) => {
    if (!locationId) return "未知"
    const location = locations.find((loc) => loc.id === locationId)
    return location?.name || locationId
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {npcs.map((npc) => (
        <Card key={npc.id} className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <div className="flex items-start justify-between">
              <CardTitle className="text-white text-lg flex items-center gap-2">
                <User className="h-5 w-5" />
                {npc.name}
              </CardTitle>
              <Badge variant="secondary">{npc.role}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {npc.persona && (
              <p className="text-sm text-gray-300 line-clamp-3">{npc.persona}</p>
            )}

            {npc.home_location_id && (
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <MapPin className="h-4 w-4" />
                {getLocationName(npc.home_location_id)}
              </div>
            )}

            {npc.desires && npc.desires.length > 0 && (
              <div className="pt-2 border-t border-slate-700">
                <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
                  <Heart className="h-3 w-3" />
                  欲望:
                </div>
                <ul className="text-sm text-gray-300 space-y-1">
                  {npc.desires.slice(0, 2).map((desire: string, i: number) => (
                    <li key={i} className="line-clamp-1">
                      • {desire}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {npc.secrets && npc.secrets.length > 0 && (
              <div className="pt-2 border-t border-slate-700">
                <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
                  <Lock className="h-3 w-3" />
                  秘密:
                </div>
                <ul className="text-sm text-gray-300 space-y-1">
                  {npc.secrets.slice(0, 2).map((secret: string, i: number) => (
                    <li key={i} className="line-clamp-1">
                      • {secret}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
