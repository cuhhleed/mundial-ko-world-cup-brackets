import { SCORE_BEARING_SLOTS } from './topology'
import type { SlotState } from './types'

export type SlotPredictionPayload = {
  teams: string[]
  winner: string
  scores?: Record<string, number>
  pk_winner?: string
  pk_scores?: Record<string, number>
}

export function buildPayload(
  slots: Record<string, SlotState>,
): Record<string, SlotPredictionPayload> {
  const payload: Record<string, SlotPredictionPayload> = {}

  for (const [slotId, slot] of Object.entries(slots)) {
    if (slot.locked) continue
    if (!slot.winner || !slot.teams) continue

    const pred: SlotPredictionPayload = {
      teams: [...slot.teams],
      winner: slot.winner,
    }

    if (slot.scores !== null) {
      pred.scores = {
        [slot.teams[0]]: slot.scores[0],
        [slot.teams[1]]: slot.scores[1],
      }
    }

    if (slot.pkScores !== null) {
      const pkWinner =
        slot.pkScores[0] > slot.pkScores[1] ? slot.teams[0] : slot.teams[1]
      pred.pk_winner = pkWinner
      pred.pk_scores = {
        [slot.teams[0]]: slot.pkScores[0],
        [slot.teams[1]]: slot.pkScores[1],
      }
    }

    payload[slotId] = pred
  }

  return payload
}

export type CompletionStatus = {
  isComplete: boolean
  completionCount: number
}

export function getCompletionStatus(
  slots: Record<string, SlotState>,
): CompletionStatus {
  let completionCount = 0
  let total = 0

  for (const [slotId, slot] of Object.entries(slots)) {
    if (slot.locked) continue
    total++

    if (!slot.winner) continue

    if (SCORE_BEARING_SLOTS.has(slotId)) {
      if (!slot.scores) continue
      if (slot.scores[0] === slot.scores[1]) {
        if (!slot.pkScores || slot.pkScores[0] === slot.pkScores[1]) continue
      }
    }

    completionCount++
  }

  return { isComplete: completionCount === total, completionCount }
}
