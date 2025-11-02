import { useState, useEffect } from "react"

interface WorldGenerationRequest {
  novelId: string
  theme: string
  tone: string
  novelType: "scifi" | "xianxia"
  numRegions?: number
  locationsPerRegion?: number
  poisPerLocation?: number
}

export function useWorld() {
  const [worlds, setWorlds] = useState<any[]>([])
  const [currentWorld, setCurrentWorld] = useState<any | null>(null)
  const [regions, setRegions] = useState<any[]>([])
  const [locations, setLocations] = useState<any[]>([])
  const [factions, setFactions] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null)

  const apiBase = "http://localhost:8000/api/world"

  // 生成世界
  const generateWorld = async (request: WorldGenerationRequest) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${apiBase}/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        throw new Error(`生成失败: ${response.statusText}`)
      }

      const result = await response.json()

      // 更新状态
      setCurrentWorld(result.world)
      setRegions(result.regions)
      setWorlds([...worlds, result.world])

      // 加载派系
      await loadFactions(result.world.id)

      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // 选择世界
  const selectWorld = async (worldId: string) => {
    setLoading(true)
    setError(null)

    try {
      // 加载世界
      const worldResponse = await fetch(`${apiBase}/scaffold/${worldId}`)
      const world = await worldResponse.json()
      setCurrentWorld(world)

      // 加载区域
      const regionsResponse = await fetch(`${apiBase}/scaffold/${worldId}/regions`)
      const regions = await regionsResponse.json()
      setRegions(regions)

      // 加载派系
      await loadFactions(worldId)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // 选择区域
  const selectRegion = async (regionId: string) => {
    setSelectedRegionId(regionId)
    setLoading(true)
    setError(null)

    try {
      // 加载地点
      const response = await fetch(`${apiBase}/region/${regionId}/locations`)
      const locations = await response.json()
      setLocations(locations)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // 加载派系
  const loadFactions = async (worldId: string) => {
    try {
      const response = await fetch(`${apiBase}/scaffold/${worldId}/factions`)
      const factions = await response.json()
      setFactions(factions)
    } catch (err: any) {
      console.error("加载派系失败:", err)
    }
  }

  // 生成地点
  const generateLocations = async (regionId: string, count: number = 8) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${apiBase}/location/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          region_id: regionId,
          count
        })
      })

      if (!response.ok) {
        throw new Error(`生成失败: ${response.statusText}`)
      }

      const newLocations = await response.json()
      setLocations([...locations, ...newLocations])

      return newLocations
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // 细化地点
  const refineLocation = async (
    locationId: string,
    targetDetailLevel: number = 2,
    passes: string[] = ["structure", "sensory", "affordance", "cinematic"]
  ) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${apiBase}/location/${locationId}/refine`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          location_id: locationId,
          turn: 0,
          target_detail_level: targetDetailLevel,
          passes
        })
      })

      if (!response.ok) {
        throw new Error(`细化失败: ${response.statusText}`)
      }

      const result = await response.json()
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    worlds,
    currentWorld,
    regions,
    locations,
    factions,
    loading,
    error,
    selectedRegionId,
    generateWorld,
    selectWorld,
    selectRegion,
    generateLocations,
    refineLocation
  }
}
