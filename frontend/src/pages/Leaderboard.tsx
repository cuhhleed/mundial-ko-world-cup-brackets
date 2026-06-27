import { useState, useEffect } from 'react'
import { api, ApiError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'

type LeaderboardEntry = {
  rank: number
  display_name: string
  total_points: number
}

type LeaderboardResponse = {
  entries: LeaderboardEntry[]
  total_participants: number
}

type MyRankResponse = {
  rank: number
  total_points: number
  total_participants: number
}

type YourRankBannerProps = {
  myRank: MyRankResponse
}

function YourRankBanner({ myRank }: YourRankBannerProps) {
  return (
    <div className="flex flex-wrap gap-4 rounded-xl border border-blue-200 bg-blue-50 px-6 py-4">
      <div className="flex flex-col">
        <span className="text-xs font-semibold uppercase tracking-wider text-blue-400">
          Your Rank
        </span>
        <span className="text-2xl font-bold text-blue-700">#{myRank.rank}</span>
      </div>
      <div className="hidden sm:block w-px bg-blue-200 self-stretch" />
      <div className="flex flex-col">
        <span className="text-xs font-semibold uppercase tracking-wider text-blue-400">
          Your Points
        </span>
        <span className="text-2xl font-bold text-blue-700">{myRank.total_points}</span>
      </div>
      <div className="hidden sm:block w-px bg-blue-200 self-stretch" />
      <div className="flex flex-col">
        <span className="text-xs font-semibold uppercase tracking-wider text-blue-400">
          Total Players
        </span>
        <span className="text-2xl font-bold text-blue-700">{myRank.total_participants}</span>
      </div>
    </div>
  )
}

type LeaderboardRowProps = {
  entry: LeaderboardEntry
  isCurrentUser: boolean
  index: number
  isTopThree: boolean
}

const MEDALS: Record<number, string> = { 1: '\u{1F947}', 2: '\u{1F948}', 3: '\u{1F949}' }

function LeaderboardRow({ entry, isCurrentUser, index, isTopThree }: LeaderboardRowProps) {
  const medal = MEDALS[entry.rank]
  const altBg = index % 2 === 0 ? 'bg-surface' : 'bg-surface-alt'

  let rowBg: string
  let leftAccent: string
  if (isCurrentUser) {
    rowBg = altBg
    leftAccent = 'border-l-4 border-l-amber-500'
  } else {
    rowBg = altBg
    leftAccent = ''
  }

  const rankSize = isTopThree ? 'text-base' : 'text-sm'
  const nameSize = isTopThree ? 'text-base' : 'text-sm'
  const pointsSize = isTopThree ? 'text-base font-bold' : 'text-sm font-semibold'
  const rowPadding = isTopThree ? 'px-4 py-4' : 'px-4 py-3'

  return (
    <div
      className={`flex items-center gap-4 ${rowPadding} border-b border-edge-light ${rowBg} ${leftAccent}`}
    >
      <span className={`w-10 shrink-0 ${rankSize} font-bold text-body-muted`}>
        {medal ? `${medal}` : entry.rank}
      </span>
      <span className={`flex-1 ${nameSize} font-medium text-body`}>
        {entry.display_name}
        {isCurrentUser && (
          <span className="ml-2 text-xs font-semibold text-amber-500">(you)</span>
        )}
      </span>
      <span className={`${pointsSize} text-body-secondary`}>{entry.total_points}</span>
    </div>
  )
}

export function Leaderboard() {
  const { isAuthenticated } = useAuth()

  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [totalParticipants, setTotalParticipants] = useState<number>(0)
  const [myRank, setMyRank] = useState<MyRankResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    const leaderboardReq = api.get<LeaderboardResponse>('/api/leaderboard?limit=50')
    const myRankReq: Promise<MyRankResponse | null> = isAuthenticated
      ? api.get<MyRankResponse>('/api/leaderboard/me').catch((err) => {
          if (err instanceof ApiError && err.status === 404) return null
          throw err
        })
      : Promise.resolve(null)

    Promise.all([leaderboardReq, myRankReq])
      .then(([leaderboardData, myRankData]) => {
        if (cancelled) return
        setEntries(leaderboardData.entries)
        setTotalParticipants(leaderboardData.total_participants)
        setMyRank(myRankData)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Failed to load leaderboard.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [refreshKey, isAuthenticated])

  const showBanner =
    isAuthenticated &&
    myRank != null &&
    !entries.some((e) => e.rank === myRank.rank)

  // First-load spinner
  if (loading && entries.length === 0) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-8 h-8 border-2 border-edge border-t-blue-500 rounded-full animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-4xl font-bold">Leaderboard</h1>
        <p className="text-body-muted">{error}</p>
        <button
          className="text-blue-600 underline"
          onClick={() => setRefreshKey((k) => k + 1)}
        >
          Try again
        </button>
      </div>
    )
  }

  if (!loading && entries.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-4xl font-bold">Leaderboard</h1>
        <p className="text-body-muted">No rankings yet.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold">Leaderboard</h1>
          <p className="mt-1 text-sm text-body-muted">
            {totalParticipants} {totalParticipants === 1 ? 'player' : 'players'}
          </p>
        </div>
        <button
          onClick={() => setRefreshKey((k) => k + 1)}
          disabled={loading}
          className="mt-1 flex items-center gap-1.5 rounded-lg border border-edge bg-surface px-3 py-1.5 text-sm text-body-muted shadow-sm hover:bg-surface-alt disabled:opacity-50 transition-colors"
          aria-label="Refresh leaderboard"
        >
          <svg
            className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`}
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh
        </button>
      </div>

      {/* "Your rank" banner — shown only when current user is outside visible top N */}
      {showBanner && myRank && <YourRankBanner myRank={myRank} />}

      {/* Table card */}
      <div className="overflow-hidden rounded-xl border border-edge bg-surface shadow-sm">
        {/* Column headers */}
        <div className="flex items-center gap-4 bg-blue-600 px-4 py-2.5 border-b border-edge">
          <span className="w-10 shrink-0 text-xs font-semibold uppercase tracking-wider text-white">
            Rank
          </span>
          <span className="flex-1 text-xs font-semibold uppercase tracking-wider text-white">
            Player
          </span>
          <span className="text-xs font-semibold uppercase tracking-wider text-white">
            Points
          </span>
        </div>

        {entries.map((entry, index) => (
          <LeaderboardRow
            key={entry.rank}
            entry={entry}
            isCurrentUser={myRank != null && entry.rank === myRank.rank}
            index={index}
            isTopThree={entry.rank <= 3}
          />
        ))}
      </div>
    </div>
  )
}
