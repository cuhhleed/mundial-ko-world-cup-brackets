import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api, ApiError } from '@/api/client'
import { BracketLayout } from './BracketLayout'
import { BracketLegend } from './BracketLegend'
import type { ApiBracketResponse, ApiSlotDetail, ApiSlotPrediction, BracketState, SlotState } from './types'

function predToSlotState(slotId: string, pred: ApiSlotPrediction, locked: boolean): SlotState {
  const teams: [string, string] | null =
    pred.teams.length >= 2 ? [pred.teams[0], pred.teams[1]] : null

  let scores: [number, number] | null = null
  if (pred.scores && teams) {
    scores = [pred.scores[teams[0]] ?? 0, pred.scores[teams[1]] ?? 0]
  }

  let pkScores: [number, number] | null = null
  if (pred.pk_scores && teams) {
    pkScores = [pred.pk_scores[teams[0]] ?? 0, pred.pk_scores[teams[1]] ?? 0]
  }

  return {
    slotId,
    teams,
    winner: pred.winner,
    scores,
    pkScores,
    locked,
    lockedResult: locked ? pred : null,
  }
}

function buildBracketState(data: ApiBracketResponse): BracketState {
  const lockedSet = new Set(data.locked_slots)
  const slots: Record<string, SlotState> = {}

  for (const [slotId, detail] of Object.entries(data.slots)) {
    slots[slotId] = predToSlotState(slotId, detail.prediction, lockedSet.has(slotId))
  }

  return { slots, initialSlots: slots }
}

type ViewerExtrasMap = Record<string, { result: ApiSlotPrediction; points: number | null }>

function buildViewerExtras(
  data: ApiBracketResponse,
): ViewerExtrasMap {
  const lockedSet = new Set(data.locked_slots)
  const extras: ViewerExtrasMap = {}
  for (const [slotId, detail] of Object.entries(data.slots)) {
    if (detail.result && !lockedSet.has(slotId)) {
      extras[slotId] = { result: detail.result, points: detail.points }
    }
  }
  return extras
}

function computeSummary(
  slots: Record<string, ApiSlotDetail>,
  lockedSlots: string[],
) {
  const lockedSet = new Set(lockedSlots)
  let completed = 0
  let correct = 0

  for (const [slotId, detail] of Object.entries(slots)) {
    if (!detail.result) continue
    completed++
    if (!lockedSet.has(slotId) && detail.prediction.winner === detail.result.winner) correct++
  }

  return { completed, correct }
}

export function BracketViewer() {
  const [data, setData] = useState<ApiBracketResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<ApiBracketResponse>('/api/brackets/me')
      .then(setData)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) {
          setError("Can't find your bracket.")
        } else {
          setError('Failed to load your bracket. Please try refreshing.')
        }
      })
  }, [])

  if (error) {
    return (
      <div className="py-12 text-center text-body-muted">
        <p>{error}</p>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-8 h-8 border-2 border-edge border-t-blue-500 rounded-full animate-spin" />
      </div>
    )
  }

  const bracketState = buildBracketState(data)
  const viewerExtras = buildViewerExtras(data)
  const { completed, correct } = computeSummary(data.slots, data.locked_slots)
  const totalPoints = data.total_points

  return (
    <div className="space-y-6">
      {/* Summary header */}
      <div className="flex flex-wrap gap-4 rounded-xl border border-edge bg-surface px-6 py-4 shadow-sm">
        <div className="flex flex-col">
          <span className="text-xs font-semibold uppercase tracking-wider text-body-faint">
            Total Points
          </span>
          <span className="text-2xl font-bold text-blue-700">
            {totalPoints ?? '--'}
          </span>
        </div>
        <div className="w-px bg-edge self-stretch" />
        <div className="flex flex-col">
          <span className="text-xs font-semibold uppercase tracking-wider text-body-faint">
            Correct Predictions
          </span>
          <span className="text-2xl font-bold text-green-700">
            {correct}
            <span className="text-sm font-normal text-body-faint"> / {completed} played</span>
          </span>
        </div>
      </div>

      <BracketLegend />

      {/* Bracket */}
      <BracketLayout bracketState={bracketState} viewerExtras={viewerExtras} />

      {/* Footer */}
      <div className="flex justify-center pt-2 pb-8">
        <Link
          to="/leaderboard"
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-blue-700 transition-colors"
        >
          View Leaderboard
        </Link>
      </div>
    </div>
  )
}
