export const R32_SLOTS = Array.from({ length: 16 }, (_, i) => `R32-${i + 1}`)
export const R16_SLOTS = Array.from({ length: 8 }, (_, i) => `R16-${i + 1}`)
export const QF_SLOTS = Array.from({ length: 4 }, (_, i) => `QF-${i + 1}`)
export const SF_SLOTS = ['SF-1', 'SF-2']

// Topological order: leaves first, root last (matches backend)
export const ALL_SLOTS: string[] = [...R32_SLOTS, ...R16_SLOTS, ...QF_SLOTS, ...SF_SLOTS, 'TP', 'FINAL']

export type SlotOutcome = 'winner' | 'loser'

export const FEEDERS: Record<string, [[string, SlotOutcome], [string, SlotOutcome]]> = {
  'R16-1': [['R32-1', 'winner'], ['R32-4', 'winner']],
  'R16-2': [['R32-3', 'winner'], ['R32-6', 'winner']],
  'R16-3': [['R32-2', 'winner'], ['R32-5', 'winner']],
  'R16-4': [['R32-7', 'winner'], ['R32-8', 'winner']],
  'R16-5': [['R32-12', 'winner'], ['R32-11', 'winner']],
  'R16-6': [['R32-10', 'winner'], ['R32-9', 'winner']],
  'R16-7': [['R32-15', 'winner'], ['R32-14', 'winner']],
  'R16-8': [['R32-13', 'winner'], ['R32-16', 'winner']],
  'QF-1': [['R16-1', 'winner'], ['R16-2', 'winner']],
  'QF-2': [['R16-5', 'winner'], ['R16-6', 'winner']],
  'QF-3': [['R16-3', 'winner'], ['R16-4', 'winner']],
  'QF-4': [['R16-7', 'winner'], ['R16-8', 'winner']],
  'SF-1': [['QF-1', 'winner'], ['QF-2', 'winner']],
  'SF-2': [['QF-3', 'winner'], ['QF-4', 'winner']],
  'FINAL': [['SF-1', 'winner'], ['SF-2', 'winner']],
  'TP': [['SF-1', 'loser'], ['SF-2', 'loser']],
}

// Inverse of FEEDERS: slot → list of downstream slots that depend on it
export const DEPENDENTS: Record<string, string[]> = {}
for (const [downstream, [[f1], [f2]]] of Object.entries(FEEDERS)) {
  ;(DEPENDENTS[f1] ??= []).push(downstream)
  ;(DEPENDENTS[f2] ??= []).push(downstream)
}

export const SCORE_BEARING_SLOTS = new Set(['SF-1', 'SF-2', 'FINAL'])

// ── Bracket display order ────────────────────────────────────────────────────
// Cascade columns render top-to-bottom in *bracket* order (not slot-ID order)
// so the index-based connector geometry lines up cleanly and mirrors the
// official bracket. Derived from FEEDERS, so it stays correct automatically if
// the topology changes.

// All R32 leaves beneath a slot, in tree (top-to-bottom) order.
function leafOrder(slot: string): string[] {
  const feeders = FEEDERS[slot]
  if (!feeders) return [slot]
  return [...leafOrder(feeders[0][0]), ...leafOrder(feeders[1][0])]
}

// Top half = SF-1's subtree, bottom half = SF-2's subtree.
const R32_BRACKET_ORDER = [...leafOrder('SF-1'), ...leafOrder('SF-2')]
const r32Position: Record<string, number> = {}
R32_BRACKET_ORDER.forEach((slot, i) => {
  r32Position[slot] = i
})

// Sort a round's slots by the average bracket position of their R32 leaves.
export function bracketOrder(slots: string[]): string[] {
  const key = (slot: string): number => {
    const leaves = leafOrder(slot)
    return leaves.reduce((sum, l) => sum + r32Position[l], 0) / leaves.length
  }
  return [...slots].sort((a, b) => key(a) - key(b))
}

export type RoundDef = {
  id: string
  label: string
  slots: string[]
}

export const ROUNDS: RoundDef[] = [
  { id: 'R32', label: 'R32', slots: R32_SLOTS },
  { id: 'R16', label: 'R16', slots: R16_SLOTS },
  { id: 'QF', label: 'QF', slots: QF_SLOTS },
  { id: 'SF', label: 'SF', slots: SF_SLOTS },
  { id: 'TP', label: 'TP', slots: ['TP'] },
  { id: 'FINAL', label: 'F', slots: ['FINAL'] },
]

// Flat ordered array of all 32 slot IDs in wizard sequence
export const WIZARD_SLOT_ORDER: string[] = [
  ...R32_SLOTS,
  ...R16_SLOTS,
  ...QF_SLOTS,
  'SF-1',
  'SF-2',
  'TP',
  'FINAL',
]
