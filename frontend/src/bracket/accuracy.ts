import type { ApiSlotPrediction } from './types'

export type SlotAccuracy = {
  winnerCorrect: boolean
  matchupCorrect: boolean
  scoreExact: boolean
  pkCorrect: boolean
}

export function isWinnerCorrect(pred: ApiSlotPrediction, result: ApiSlotPrediction): boolean {
  return pred.winner === result.winner
}

export function isMatchupCorrect(pred: ApiSlotPrediction, result: ApiSlotPrediction): boolean {
  const predSet = new Set(pred.teams)
  return result.teams.length === 2 && result.teams.every((t) => predSet.has(t))
}

export function isScoreExact(pred: ApiSlotPrediction, result: ApiSlotPrediction): boolean {
  if (!pred.scores || !result.scores) return false
  return pred.teams.every((t) => pred.scores![t] === result.scores![t])
}

export function isPKCorrect(pred: ApiSlotPrediction, result: ApiSlotPrediction): boolean {
  if (!pred.pk_scores || !result.pk_scores) return false
  return pred.teams.every((t) => pred.pk_scores![t] === result.pk_scores![t])
}

export function getSlotAccuracy(pred: ApiSlotPrediction, result: ApiSlotPrediction): SlotAccuracy {
  return {
    winnerCorrect: isWinnerCorrect(pred, result),
    matchupCorrect: isMatchupCorrect(pred, result),
    scoreExact: isScoreExact(pred, result),
    pkCorrect: isPKCorrect(pred, result),
  }
}
