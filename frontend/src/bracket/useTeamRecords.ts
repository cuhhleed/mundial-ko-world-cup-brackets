import { useEffect, useState } from 'react'
import { api } from '@/api/client'

export type TeamRecord = {
  wins: number
  draws: number
  losses: number
}

type TeamRecordsResponse = {
  records: Record<string, TeamRecord>
}

export function useTeamRecords(): Record<string, TeamRecord> | null {
  const [records, setRecords] = useState<Record<string, TeamRecord> | null>(null)

  useEffect(() => {
    let cancelled = false

    api
      .get<TeamRecordsResponse>('/api/teams/records')
      .then((data) => {
        if (!cancelled) setRecords(data.records)
      })
      .catch(() => {})

    return () => {
      cancelled = true
    }
  }, [])

  return records
}
