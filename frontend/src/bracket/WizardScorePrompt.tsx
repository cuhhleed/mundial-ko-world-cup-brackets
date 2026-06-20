type Props = {
  slotId: string
  teams: [string, string] | null
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

function ScoreInput({
  value,
  onChange,
}: {
  value: number | null
  onChange: (v: number) => void
}) {
  return (
    <input
      type="number"
      min={0}
      max={9}
      value={value ?? ''}
      onChange={(e) => {
        const n = parseInt(e.target.value, 10)
        if (!isNaN(n) && n >= 0 && n <= 9) onChange(n)
      }}
      className="w-14 h-14 text-center text-2xl font-bold border-2 border-gray-300 rounded-xl
                 focus:outline-none focus:border-blue-500 bg-white"
      placeholder="—"
    />
  )
}

export function WizardScorePrompt({
  slotId,
  teams,
  scores,
  pkScores,
  winner,
  onScoresChange,
  onPkChange,
  onConfirm,
}: Props) {
  if (!teams) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16 text-gray-400">
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
      <h2 className="text-base font-medium text-gray-500 tracking-wide uppercase">
        {slotLabel(slotId)}
      </h2>
      <p className="text-xl font-semibold text-gray-700">Enter the score (90 min)</p>

      {/* Score row */}
      <div className="flex items-center gap-6">
        <div className="flex flex-col items-center gap-2 w-32">
          <span className="text-sm font-medium text-gray-600 text-center">{teams[0]}</span>
          <ScoreInput
            value={scores?.[0] ?? null}
            onChange={(v) => onScoresChange([v, scores?.[1] ?? 0])}
          />
        </div>

        <span className="text-3xl font-bold text-gray-400 pb-6">–</span>

        <div className="flex flex-col items-center gap-2 w-32">
          <span className="text-sm font-medium text-gray-600 text-center">{teams[1]}</span>
          <ScoreInput
            value={scores?.[1] ?? null}
            onChange={(v) => onScoresChange([scores?.[0] ?? 0, v])}
          />
        </div>
      </div>

      {/* PK section — only visible when scores are equal */}
      {isDrawn && (
        <div className="flex flex-col items-center gap-4 mt-2 p-4 rounded-xl bg-amber-50 border border-amber-200 w-full max-w-xs">
          <p className="text-sm font-semibold text-amber-700">Penalty shootout</p>
          <div className="flex items-center gap-6">
            <ScoreInput
              value={pkScores?.[0] ?? null}
              onChange={(v) => onPkChange([v, pkScores?.[1] ?? 0])}
            />
            <span className="text-xl font-bold text-gray-400">–</span>
            <ScoreInput
              value={pkScores?.[1] ?? null}
              onChange={(v) => onPkChange([pkScores?.[0] ?? 0, v])}
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
          ✓ <span className="font-bold">{winner}</span> advances
        </p>
      )}

      <button
        type="button"
        onClick={onConfirm}
        disabled={!canConfirm}
        className="px-8 py-3 rounded-xl font-semibold text-white bg-blue-600
                   hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed
                   transition-colors"
      >
        Next
      </button>
    </div>
  )
}
