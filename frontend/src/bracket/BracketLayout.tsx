import { useState } from 'react'
import { BracketSlotCard, type SlotCardData } from './BracketSlotCard'
import { CARD_H, RoundColumn, UNIT } from './RoundColumn'
import { FEEDERS, ROUNDS } from './topology'
import type { ApiSlotPrediction, BracketState } from './types'

type ViewerExtrasMap = Record<string, { result: ApiSlotPrediction; points: number | null }>

type Props = {
  bracketState: BracketState
  viewerExtras?: ViewerExtrasMap
}

// Convert internal SlotState to display-ready SlotCardData.
// For locked slots, scores come from lockedResult (dict keyed by team name) → tuple.
function toSlotCardData(
  state: BracketState['slots'][string],
): SlotCardData {
  if (state.locked && state.lockedResult) {
    const lr = state.lockedResult
    const t = lr.teams
    const teams: [string, string] | null =
      t.length >= 2 ? [t[0], t[1]] : state.teams
    let scores: [number, number] | null = null
    if (lr.scores && teams) {
      scores = [lr.scores[teams[0]] ?? 0, lr.scores[teams[1]] ?? 0]
    }
    let pkScores: [number, number] | null = null
    if (lr.pk_scores && teams) {
      pkScores = [lr.pk_scores[teams[0]] ?? 0, lr.pk_scores[teams[1]] ?? 0]
    }
    return {
      slotId: state.slotId,
      teams,
      winner: lr.winner,
      scores,
      pkScores,
      locked: true,
      status: state.status,
      kickoffTime: state.kickoffTime,
    }
  }
  return {
    slotId: state.slotId,
    teams: state.teams,
    winner: state.winner,
    scores: state.scores,
    pkScores: state.pkScores,
    locked: state.locked,
    status: state.status,
    kickoffTime: state.kickoffTime,
  }
}

const TOTAL_H = 16 * UNIT  // 1024px
const FINALS_COL_W = 160

// Vertical center positions for the Finals column
const FINAL_CENTER_Y = 8 * UNIT   // midpoint between SF-1 and SF-2 connector
const TP_CENTER_Y = 13 * UNIT     // third place, shown below the main cascade

// Round configs for main cascade (R32 through SF)
const CASCADE_ROUNDS = ROUNDS.filter((r) => ['R32', 'R16', 'QF', 'SF'].includes(r.id))
const MOBILE_TABS = [...CASCADE_ROUNDS, { id: 'FINALS', label: 'Finals', slots: ['FINAL', 'TP'] }]

// Mobile two-column layout: gap scales with slot count so sparse rounds get more room
function mGap(slotCount: number): number {
  if (slotCount <= 2) return 80
  if (slotCount <= 4) return 64
  return 56
}

const emptySlot = (slotId: string): SlotCardData => ({
  slotId, teams: null, winner: null, scores: null, pkScores: null, locked: false,
})

export function BracketLayout({ bracketState, viewerExtras }: Props) {
  const [mobileTab, setMobileTab] = useState('R32')

  const slotData: Record<string, SlotCardData> = {}
  for (const [id, s] of Object.entries(bracketState.slots)) {
    slotData[id] = toSlotCardData(s)
  }

  function getSlotsForRound(roundId: string): SlotCardData[] {
    const round = ROUNDS.find((r) => r.id === roundId)
    return round ? round.slots.map((sid) => slotData[sid] ?? { slotId: sid, teams: null, winner: null, scores: null, pkScores: null, locked: false }) : []
  }

  const finalsSlot = slotData['FINAL'] ?? { slotId: 'FINAL', teams: null, winner: null, scores: null, pkScores: null, locked: false }
  const tpSlot = slotData['TP'] ?? { slotId: 'TP', teams: null, winner: null, scores: null, pkScores: null, locked: false }

  // ── Desktop layout ──────────────────────────────────────────────────────────
  const desktopCols = CASCADE_ROUNDS.map((round, i) => (
    <RoundColumn
      key={round.id}
      roundIndex={i}
      label={round.label}
      slots={getSlotsForRound(round.id)}
      showConnectors={true}
      viewerExtras={viewerExtras}
    />
  ))

  const finalsCol = (
    <div
      key="finals"
      className="flex flex-col"
      style={{ minWidth: FINALS_COL_W }}
    >
      <div className="text-xs font-semibold text-body-faint uppercase tracking-wider text-center pb-2">
        Finals
      </div>

      <div className="relative" style={{ height: TOTAL_H, width: FINALS_COL_W }}>
        {/* FINAL */}
        <div
          className="absolute"
          style={{ top: FINAL_CENTER_Y - CARD_H / 2, left: 0, width: FINALS_COL_W, height: CARD_H }}
        >
          <BracketSlotCard slot={finalsSlot} viewer={viewerExtras?.['FINAL']} />
        </div>

        {/* TP label + card */}
        <div
          className="absolute flex flex-col items-center gap-1"
          style={{ top: TP_CENTER_Y - CARD_H / 2 - 20, left: 0, width: FINALS_COL_W }}
        >
          <span className="text-[10px] font-semibold text-body-faint uppercase tracking-wider">
            3rd Place
          </span>
          <BracketSlotCard slot={tpSlot} viewer={viewerExtras?.['TP']} />
        </div>
      </div>
    </div>
  )

  return (
    <>
      {/* ── Mobile: two aligned columns with connectors ─────────────────────── */}
      <div className="md:hidden">
        <div className="flex gap-1 overflow-x-auto pb-3">
          {MOBILE_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setMobileTab(tab.id)}
              className={[
                'px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors',
                mobileTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-surface-alt text-body-muted hover:bg-surface-hover',
              ].join(' ')}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {(() => {
          const tabIdx = MOBILE_TABS.findIndex((t) => t.id === mobileTab)
          const leftTab = MOBILE_TABS[tabIdx]
          const rightTab = tabIdx + 1 < MOBILE_TABS.length ? MOBILE_TABS[tabIdx + 1] : null

          const leftIds = leftTab.slots
          const rightIds = rightTab?.slots ?? []
          const gap = mGap(leftIds.length)

          // Left column: uniform spacing
          const leftY: Record<string, number> = {}
          leftIds.forEach((id, i) => { leftY[id] = i * gap })

          // Right column: position from feeder midpoints; TP is detached below FINAL
          const rightY: Record<string, number> = {}
          const rightIdsNoTp = rightIds.filter((id) => id !== 'TP')
          for (const id of rightIdsNoTp) {
            const f = FEEDERS[id]
            if (!f) continue
            const y1 = leftY[f[0][0]]
            const y2 = leftY[f[1][0]]
            if (y1 !== undefined && y2 !== undefined) {
              rightY[id] = (y1 + y2) / 2
            }
          }

          // Push apart any overlapping right-column cards (excluding TP)
          const sortedRightIds = Object.keys(rightY).sort((a, b) => rightY[a] - rightY[b])
          for (let i = 1; i < sortedRightIds.length; i++) {
            const prev = sortedRightIds[i - 1]
            const curr = sortedRightIds[i]
            const minGap = CARD_H + 8
            if (rightY[curr] - rightY[prev] < minGap) {
              const mid = (rightY[curr] + rightY[prev]) / 2
              rightY[prev] = mid - minGap / 2
              rightY[curr] = mid + minGap / 2
            }
          }

          // TP sits well below FINAL with clear visual separation
          if (rightIds.includes('TP')) {
            const finalY = rightY['FINAL']
            if (finalY !== undefined) {
              rightY['TP'] = finalY + CARD_H + 48
            } else {
              // FINALS as left column: TP after FINAL
              const lastLeftY = leftIds.length > 0 ? leftY[leftIds[leftIds.length - 1]] : 0
              rightY['TP'] = (lastLeftY ?? 0) + CARD_H + 48
            }
          }

          // Also separate TP in the left column when FINALS tab is selected
          if (leftIds.includes('TP') && leftIds.includes('FINAL')) {
            leftY['TP'] = leftY['FINAL'] + CARD_H + 48
          }

          // Total height from content
          const maxLeft = Object.values(leftY).length > 0
            ? Math.max(...Object.values(leftY)) + CARD_H
            : 0
          const rightVals = Object.values(rightY)
          const maxRight = rightVals.length > 0 ? Math.max(...rightVals) + CARD_H : 0
          const totalH = Math.max(maxLeft, maxRight)

          const hasRight = rightIds.length > 0

          // Connector data — TP gets no connectors
          const connectors = rightIdsNoTp.map((id) => {
            const f = FEEDERS[id]
            if (!f) return null
            const topY = leftY[f[0][0]]
            const botY = leftY[f[1][0]]
            const rY = rightY[id]
            if (topY === undefined || botY === undefined || rY === undefined) return null
            return {
              topCY: topY + CARD_H / 2,
              botCY: botY + CARD_H / 2,
              rightCY: rY + CARD_H / 2,
            }
          }).filter((c): c is { topCY: number; botCY: number; rightCY: number } => c !== null)

          return (
            <div className="relative" style={{ height: totalH }}>
              {/* Left column */}
              {leftIds.map((id) => (
                <div
                  key={id}
                  className={`absolute ${hasRight ? 'w-[46%]' : 'w-[60%]'}`}
                  style={{ top: leftY[id], left: 0 }}
                >
                  {id === 'FINAL' && <p className="text-[10px] font-semibold text-body-faint uppercase mb-0.5">Final</p>}
                  {id === 'TP' && <p className="text-[10px] font-semibold text-body-faint uppercase mb-0.5">3rd Place</p>}
                  <BracketSlotCard slot={slotData[id] ?? emptySlot(id)} viewer={viewerExtras?.[id]} />
                </div>
              ))}

              {/* Right column */}
              {rightIds.map((id) => (
                <div
                  key={id}
                  className="absolute w-[46%]"
                  style={{ top: rightY[id], right: 0 }}
                >
                  {id === 'FINAL' && <p className="text-[10px] font-semibold text-body-faint uppercase mb-0.5">Final</p>}
                  {id === 'TP' && <p className="text-[10px] font-semibold text-body-faint uppercase mb-0.5">3rd Place</p>}
                  <BracketSlotCard slot={slotData[id] ?? emptySlot(id)} viewer={viewerExtras?.[id]} />
                </div>
              ))}

              {/* Connector lines */}
              {connectors.length > 0 && (
                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                  {connectors.map((c, i) => (
                    <g key={i} stroke="var(--th-connector)" strokeWidth="1.5" fill="none">
                      <line x1="46%" y1={c.topCY} x2="50%" y2={c.topCY} />
                      <line x1="46%" y1={c.botCY} x2="50%" y2={c.botCY} />
                      <line x1="50%" y1={c.topCY} x2="50%" y2={c.botCY} />
                      <line x1="50%" y1={c.rightCY} x2="54%" y2={c.rightCY} />
                    </g>
                  ))}
                </svg>
              )}
            </div>
          )
        })()}
      </div>

      {/* ── Desktop: all columns with horizontal scroll ─────────────────────── */}
      <div className="hidden md:block overflow-x-auto">
        <div className="flex items-start gap-0" style={{ height: TOTAL_H + 32 }}>
          {desktopCols}
          {finalsCol}
        </div>
      </div>
    </>
  )
}
