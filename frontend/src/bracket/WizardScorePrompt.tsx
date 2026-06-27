import { TeamFlag } from '../components/TeamFlag'
import { TeamRecordStack } from './TeamRecordStack'
import type { TeamRecord } from './useTeamRecords'

type Props = {
  slotId: string
  teams: [string, string] | null
  records: Record<string, TeamRecord> | null
  scores: [number, number] | null
  pkScores: [number, number] | null
  winner: string | null
  onScoresChange: (scores: [number, number]) => void
  onPkChange: (pkScores: [number, number]) => void
  onConfirm: () => void
}

function slotLabel(slotId: string): string {
  if (slotId === 'SF-1') return 'Semi-final 1'
  if (slotId === 'SF-2') return 'Semi-final 2'
  if (slotId === 'FINAL') return 'Final'
  return slotId
}

function StepButton({
  direction,
  onClick,
  disabled,
}: {
  direction: 'up' | 'down'
  onClick: () => void
  disabled: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="w-10 h-10 flex items-center justify-center rounded-lg bg-blue-600
                 hover:bg-blue-700 active:bg-blue-800 disabled:bg-gray-300
                 disabled:cursor-not-allowed transition-colors"
      aria-label={direction === 'up' ? 'Increase' : 'Decrease'}
    >
      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
        {direction === 'up' ? (
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
        ) : (
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        )}
      </svg>
    </button>
  )
}

function ScoreInput({
  value,
  onChange,
  side,
}: {
  value: number | null
  onChange: (v: number) => void
  side: 'left' | 'right'
}) {
  const current = value ?? 0
  const decBtn = (
    <StepButton direction="down" onClick={() => onChange(current - 1)} disabled={current <= 0} />
  )
  const incBtn = (
    <StepButton direction="up" onClick={() => onChange(current + 1)} disabled={current >= 9} />
  )

  return (
    <div className="flex items-center gap-2">
      {side === 'left' ? decBtn : incBtn}
      <div
        className="w-14 h-14 flex items-center justify-center text-2xl font-bold
                   border-2 border-edge rounded-xl bg-surface select-none"
      >
        {value ?? '—'}
      </div>
      {side === 'left' ? incBtn : decBtn}
    </div>
  )
}

export function WizardScorePrompt({
  slotId,
  teams,
  records,
  scores,
  pkScores,
  winner,
  onScoresChange,
  onPkChange,
  onConfirm,
}: Props) {
  if (!teams) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16 text-body-faint">
        <span className="text-4xl">⏳</span>
        <p className="text-lg">{slotLabel(slotId)}</p>
        <p className="text-sm">Waiting for upstream picks…</p>
      </div>
    )
  }

  const isDrawn = scores !== null && scores[0] === scores[1]
  const canConfirm = winner !== null

  return (
    <div className="flex flex-col items-center gap-8 py-8">
      <h2 className="text-base font-medium text-body-muted tracking-wide uppercase">
        {slotLabel(slotId)}
      </h2>
      <p className="text-xl font-semibold text-body-secondary text-center">
        {slotId === 'FINAL'
          ? 'Who is the 2026 World Cup Champion?'
          : 'Enter the score (90 min + extra time)'}
      </p>

      {/* Teams */}
      <div className="flex flex-col items-center gap-3">
        <div className="flex items-center gap-2 sm:gap-4">
          {records?.[teams[0]] && <div className="hidden sm:block"><TeamRecordStack {...records[teams[0]]} /></div>}
          <div className="flex flex-col items-center gap-2 sm:gap-3 px-4 sm:px-8 py-4 sm:py-5 rounded-2xl border-2 border-edge bg-surface w-32 sm:w-44">
            <TeamFlag code={teams[0]} className="w-10 h-10 sm:w-16 sm:h-16" />
            <span className="text-sm sm:text-lg font-bold text-body text-center leading-tight">{teams[0]}</span>
          </div>
          <span className="text-sm font-bold text-body-faint tracking-wider">VS</span>
          <div className="flex flex-col items-center gap-2 sm:gap-3 px-4 sm:px-8 py-4 sm:py-5 rounded-2xl border-2 border-edge bg-surface w-32 sm:w-44">
            <TeamFlag code={teams[1]} className="w-10 h-10 sm:w-16 sm:h-16" />
            <span className="text-sm sm:text-lg font-bold text-body text-center leading-tight">{teams[1]}</span>
          </div>
          {records?.[teams[1]] && <div className="hidden sm:block"><TeamRecordStack {...records[teams[1]]} /></div>}
        </div>
        {records && (records[teams[0]] || records[teams[1]]) && (
          <div className="flex items-center gap-2 sm:hidden">
            <div className="w-32 flex justify-center">
              {records[teams[0]] && <TeamRecordStack {...records[teams[0]]} />}
            </div>
            <span className="text-sm font-bold tracking-wider invisible">VS</span>
            <div className="w-32 flex justify-center">
              {records[teams[1]] && <TeamRecordStack {...records[teams[1]]} />}
            </div>
          </div>
        )}
      </div>

      {/* Score row */}
      <div className="flex items-center gap-4">
        <ScoreInput
          value={scores?.[0] ?? null}
          onChange={(v) => onScoresChange([v, scores?.[1] ?? 0])}
          side="left"
        />
        <span className="text-xl font-bold text-body-faint">–</span>
        <ScoreInput
          value={scores?.[1] ?? null}
          onChange={(v) => onScoresChange([scores?.[0] ?? 0, v])}
          side="right"
        />
      </div>

      {/* PK section — only visible when scores are equal */}
      {isDrawn && (
        <div className="flex flex-col items-center gap-4 mt-2 p-4 rounded-xl bg-amber-50 border border-amber-200 w-full max-w-md">
          <p className="text-sm font-semibold text-amber-700">Penalty shootout</p>
          <div className="flex items-center gap-4">
            <ScoreInput
              value={pkScores?.[0] ?? null}
              onChange={(v) => onPkChange([v, pkScores?.[1] ?? 0])}
              side="left"
            />
            <span className="text-xl font-bold text-body-faint">–</span>
            <ScoreInput
              value={pkScores?.[1] ?? null}
              onChange={(v) => onPkChange([pkScores?.[0] ?? 0, v])}
              side="right"
            />
          </div>
          {pkScores && pkScores[0] === pkScores[1] && (
            <p className="text-xs text-amber-600">PK scores must differ</p>
          )}
        </div>
      )}

      {/* Winner indicator */}
      {winner && (
        <p className="text-sm text-green-700 font-medium">
          ✓ <span className="font-bold">{winner}</span> {slotId === 'FINAL' ? 'wins!' : 'advances'}
        </p>
      )}

      <button
        type="button"
        onClick={onConfirm}
        disabled={!canConfirm}
        className="px-8 py-3 rounded-xl font-semibold text-white bg-blue-600
                   hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed
                   transition-colors self-center"
      >
        Next
      </button>
    </div>
  )
}
