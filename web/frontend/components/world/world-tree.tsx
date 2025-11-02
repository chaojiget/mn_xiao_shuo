"use client"

import { ChevronDown, ChevronRight, MapPin, Map } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { useState } from "react"

interface WorldTreeProps {
  world: any
  regions: any[]
  onSelectRegion: (regionId: string) => void
  selectedRegionId: string | null
  onSelectLocation: (locationId: string) => void
  selectedLocationId: string | null
}

export function WorldTree({
  world,
  regions,
  onSelectRegion,
  selectedRegionId,
  onSelectLocation,
  selectedLocationId
}: WorldTreeProps) {
  const [expandedRegions, setExpandedRegions] = useState<Set<string>>(new Set())

  const toggleRegion = (regionId: string) => {
    const newExpanded = new Set(expandedRegions)
    if (newExpanded.has(regionId)) {
      newExpanded.delete(regionId)
    } else {
      newExpanded.add(regionId)
    }
    setExpandedRegions(newExpanded)
  }

  return (
    <ScrollArea className="h-[400px]">
      <div className="space-y-1">
        {regions.map((region) => {
          const isExpanded = expandedRegions.has(region.id)
          const isSelected = selectedRegionId === region.id

          return (
            <div key={region.id}>
              <div
                className={cn(
                  "flex items-center gap-2 p-2 rounded-md cursor-pointer hover:bg-accent",
                  isSelected && "bg-accent"
                )}
                onClick={() => {
                  onSelectRegion(region.id)
                  toggleRegion(region.id)
                }}
              >
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-4 w-4 p-0"
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleRegion(region.id)
                  }}
                >
                  {isExpanded ? (
                    <ChevronDown className="h-3 w-3" />
                  ) : (
                    <ChevronRight className="h-3 w-3" />
                  )}
                </Button>
                <Map className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">{region.name}</span>
              </div>

              {/* 地点列表（展开时） */}
              {isExpanded && region.locations && (
                <div className="ml-6 mt-1 space-y-1">
                  {region.locations.map((location: any) => (
                    <div
                      key={location.id}
                      className={cn(
                        "flex items-center gap-2 p-2 rounded-md cursor-pointer hover:bg-accent",
                        selectedLocationId === location.id && "bg-accent"
                      )}
                      onClick={(e) => {
                        e.stopPropagation()
                        onSelectLocation(location.id)
                      }}
                    >
                      <MapPin className="h-3 w-3 text-muted-foreground" />
                      <span className="text-xs">{location.name}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </ScrollArea>
  )
}
