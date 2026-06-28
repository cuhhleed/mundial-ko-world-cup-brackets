import { useReducer } from 'react'
import { ALL_SLOTS, DEPENDENTS, FEEDERS, ROUNDS } from './topology'
import type { BracketAction, BracketState, SlotState } from './types'

const initialState: BracketState = { slots: {}, initialSlots: {} }

// ── Cascade helpers ───────────────────────────────────────────────────────────

function getTeamFromSlot(slot: SlotState, outcome: 'winner' | 'loser'): string | null {
  let winner: string | null
  let teams: [string, string] | null

  if (slot.locked && slot.lockedResult) {
    winner = slot.lockedResult.winner
    const t = slot.lockedResult.teams
    teams = t.length >= 2 ? [t[0], t[1]] : null
  } else {
    winner = slot.winner
    teams = slot.teams
  }

  if (!winner || !teams) return null
  if (outcome === 'winner') return winner
  return teams[0] === winner ? teams[1] : teams[0]
}

function computeTeams(
  slotId: string,
  slots: Record<string, SlotState>,
): [string, string] | null {
  const feeders = FEEDERS[slotId]
  if (!feeders) return null

  const [[f1Id, o1], [f2Id, o2]] = feeders
  const f1 = slots[f1Id]
  const f2 = slots[f2Id]
  if (!f1 || !f2) return null

  const team1 = getTeamFromSlot(f1, o1)
  const team2 = getTeamFromSlot(f2, o2)
  if (!team1 || !team2) return null
  return [team1, team2]
}

function cascadeFrom(
  slotId: string,
  slots: Record<string, SlotState>,
): Record<string, SlotState> {
  const deps = DEPENDENTS[slotId] ?? []
  let updated = slots

  for (const depId of deps) {
    const dep = updated[depId]
    if (!dep || dep.locked) continue

    const newTeams = computeTeams(depId, updated)
    const same =
      newTeams === dep.teams ||
      (newTeams !== null &&
        dep.teams !== null &&
        newTeams[0] === dep.teams[0] &&
        newTeams[1] === dep.teams[1])

    if (!same) {
      updated = {
        ...updated,
        [depId]: { ...dep, teams: newTeams, winner: null, scores: null, pkScores: null },
      }
      updated = cascadeFrom(depId, updated)
    }
  }

  return updated
}

// ── Reducer ───────────────────────────────────────────────────────────────────

function reducer(state: BracketState, action: BracketAction): BracketState {
  switch (action.type) {
    case 'INIT_TEMPLATE': {
      const slots: Record<string, SlotState> = {}

      for (const slotId of ALL_SLOTS) {
        const t = action.template.slots[slotId]
        if (!t) continue
        const teams =
          t.teams && t.teams.length >= 2
            ? ([t.teams[0], t.teams[1]] as [string, string])
            : null
        slots[slotId] = {
          slotId,
          teams,
          winner: t.status === 'locked' ? (t.result?.winner ?? null) : null,
          scores: null,
          pkScores: null,
          locked: t.status === 'locked',
          lockedResult: t.result ?? null,
        }
      }

      let cascaded = { ...slots }
      for (const slotId of ALL_SLOTS) {
        if (cascaded[slotId]?.locked) {
          cascaded = cascadeFrom(slotId, cascaded)
        }
      }

      const initialSlots: Record<string, SlotState> = JSON.parse(JSON.stringify(cascaded))
      return { slots: cascaded, initialSlots }
    }

    case 'SELECT_WINNER': {
      const { slotId, winner } = action
      const slot = state.slots[slotId]
      if (!slot || slot.locked) return state

      let slots = { ...state.slots, [slotId]: { ...slot, winner } }
      slots = cascadeFrom(slotId, slots)
      return { ...state, slots }
    }

    case 'SET_SCORES': {
      const { slotId, scores } = action
      const slot = state.slots[slotId]
      if (!slot || slot.locked || !slot.teams) return state

      const [s1, s2] = scores
      const [team1] = slot.teams
      let winner: string | null = null
      let pkScores: [number, number] | null = null

      if (s1 !== s2) {
        winner = s1 > s2 ? team1 : slot.teams[1]
        // pkScores remains null — scores already decided the winner
      } else {
        // Draw: preserve existing PK picks, winner stays null until PK resolved
        pkScores = slot.pkScores
      }

      let slots = { ...state.slots, [slotId]: { ...slot, scores, winner, pkScores } }
      slots = cascadeFrom(slotId, slots)
      return { ...state, slots }
    }

    case 'SET_PK': {
      const { slotId, pkScores } = action
      const slot = state.slots[slotId]
      if (!slot || slot.locked || !slot.teams) return state

      const [pk1, pk2] = pkScores
      const winner = pk1 !== pk2 ? (pk1 > pk2 ? slot.teams[0] : slot.teams[1]) : null

      let slots = { ...state.slots, [slotId]: { ...slot, pkScores, winner } }
      slots = cascadeFrom(slotId, slots)
      return { ...state, slots }
    }

    case 'CLEAR_SLOT': {
      const { slotId } = action
      const slot = state.slots[slotId]
      if (!slot || slot.locked) return state

      let slots = {
        ...state.slots,
        [slotId]: { ...slot, winner: null, scores: null, pkScores: null },
      }
      slots = cascadeFrom(slotId, slots)
      return { ...state, slots }
    }

    case 'CLEAR_FROM_ROUND': {
      const { roundId } = action
      const roundIdx = ROUNDS.findIndex((r) => r.id === roundId)
      if (roundIdx === -1) return state

      let slots = { ...state.slots }

      // Target round: clear picks but keep teams (still valid from upstream)
      for (const slotId of ROUNDS[roundIdx].slots) {
        const slot = slots[slotId]
        if (slot && !slot.locked) {
          slots = { ...slots, [slotId]: { ...slot, winner: null, scores: null, pkScores: null } }
        }
      }

      // Subsequent rounds: clear everything including teams
      for (let i = roundIdx + 1; i < ROUNDS.length; i++) {
        for (const slotId of ROUNDS[i].slots) {
          const slot = slots[slotId]
          if (slot && !slot.locked) {
            slots = {
              ...slots,
              [slotId]: { ...slot, teams: null, winner: null, scores: null, pkScores: null },
            }
          }
        }
      }

      return { ...state, slots }
    }

    case 'START_OVER': {
      const slots: Record<string, SlotState> = {}
      for (const [slotId, slot] of Object.entries(state.slots)) {
        if (slot.locked) {
          slots[slotId] = slot
        } else {
          slots[slotId] = {
            ...state.initialSlots[slotId],
            winner: null,
            scores: null,
            pkScores: null,
          }
        }
      }
      return { ...state, slots }
    }

    default:
      return state
  }
}

export function useBracketReducer() {
  return useReducer(reducer, initialState)
}
