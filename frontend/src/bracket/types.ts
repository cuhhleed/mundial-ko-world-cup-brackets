// ── API shapes (match backend JSON) ──────────────────────────────────────────

export type ApiSlotDetail = {
  prediction: ApiSlotPrediction
  result: ApiSlotPrediction | null
  points: number | null
}

export type ApiBracketResponse = {
  bracket_id: string
  user_id: string
  slots: Record<string, ApiSlotDetail>
  locked_slots: string[]
  total_points: number
  status: string
  created_at: string
}

export type ApiSlotPrediction = {
  teams: string[]
  winner: string
  scores: Record<string, number> | null
  pk_winner: string | null
  pk_scores: Record<string, number> | null
}

export type ApiSlotTemplate = {
  slot_id: string
  teams: string[] | null
  status: 'open' | 'locked'
  result: ApiSlotPrediction | null
}

export type ApiBracketTemplate = {
  slots: Record<string, ApiSlotTemplate>
}

// ── Internal reducer state ────────────────────────────────────────────────────

export type SlotState = {
  slotId: string
  teams: [string, string] | null  // null when upstream not yet picked
  winner: string | null
  scores: [number, number] | null   // indexed by teams position
  pkScores: [number, number] | null
  locked: boolean
  lockedResult: ApiSlotPrediction | null
  status?: "scheduled" | "live" | "completed"
  kickoffTime?: string
}

export type BracketState = {
  slots: Record<string, SlotState>
  initialSlots: Record<string, SlotState>  // pristine template snapshot for START_OVER
}

// ── Reducer actions ───────────────────────────────────────────────────────────

export type BracketAction =
  | { type: 'INIT_TEMPLATE'; template: ApiBracketTemplate }
  | { type: 'SELECT_WINNER'; slotId: string; winner: string }
  | { type: 'SET_SCORES'; slotId: string; scores: [number, number] }
  | { type: 'SET_PK'; slotId: string; pkScores: [number, number] }
  | { type: 'CLEAR_SLOT'; slotId: string }
  | { type: 'CLEAR_FROM_ROUND'; roundId: string }
  | { type: 'START_OVER' }
