import { useCallback, useState } from 'react'
import type { Medication } from '../types'

const STORAGE_KEY = 'arca:recent-medications'
const MAX_RECENTS = 6

export type RecentMedication = Pick<Medication, 'id' | 'name' | 'category'>

function readStorage(): RecentMedication[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as RecentMedication[]) : []
  } catch {
    return []
  }
}

export function useRecentMedications() {
  const [recents, setRecents] = useState<RecentMedication[]>(readStorage)

  const addRecent = useCallback((medication: RecentMedication) => {
    setRecents((prev) => {
      const entry: RecentMedication = {
        id: medication.id,
        name: medication.name,
        category: medication.category,
      }
      const next = [
        entry,
        ...prev.filter((m) => m.id !== medication.id),
      ].slice(0, MAX_RECENTS)
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      } catch {
        // armazenamento indisponível — recentes ficam apenas em memória
      }
      return next
    })
  }, [])

  return { recents, addRecent }
}
