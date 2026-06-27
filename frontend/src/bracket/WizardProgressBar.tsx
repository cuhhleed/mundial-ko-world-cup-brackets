import { ROUNDS, WIZARD_SLOT_ORDER } from './topology'

// Start index (in WIZARD_SLOT_ORDER) for each round
const ROUND_START: Record<string, number> = {}
const ROUND_END: Record<string, number> = {}

let cursor = 0
for (const round of ROUNDS) {
  ROUND_START[round.id] = cursor
  ROUND_END[round.id] = cursor + round.slots.length - 1
  cursor += round.slots.length
}

type Props = {
  currentStep: number  // index into WIZARD_SLOT_ORDER (0-31)
  onRoundClick: (roundId: string) => void
}

export function WizardProgressBar({ currentStep, onRoundClick }: Props) {
  return (
    <div className="w-full flex items-center gap-1">
      {ROUNDS.map((round) => {
        const start = ROUND_START[round.id]
        const end = ROUND_END[round.id]
        const total = round.slots.length

        // How many steps in this round are done
        const done = Math.max(0, Math.min(currentStep - start, total))
        const fillPct = Math.round((done / total) * 100)

        const isAccessible = currentStep >= start
        const isPast = currentStep > end

        return (
          <div key={round.id} className="flex-1 flex flex-col gap-1">
            <button
              type="button"
              disabled={!isAccessible}
              onClick={() => isAccessible && onRoundClick(round.id)}
              className={[
                'text-xs font-semibold text-center py-0.5 rounded transition-colors',
                isAccessible
                  ? 'text-blue-700 hover:text-blue-900 cursor-pointer'
                  : 'text-body-disabled cursor-default',
              ].join(' ')}
            >
              {round.label}
            </button>

            {/* Progress track */}
            <div className="h-2 rounded-full bg-connector overflow-hidden">
              <div
                className={[
                  'h-full rounded-full transition-all duration-300',
                  isPast ? 'bg-green-500' : 'bg-blue-500',
                ].join(' ')}
                style={{ width: `${fillPct}%` }}
              />
            </div>

            {/* Match indicators */}
            <div className="hidden md:flex gap-0.5 justify-center flex-wrap">
              {Array.from({ length: total }, (_, j) => {
                const stepIdx = start + j
                const isDone = stepIdx < currentStep
                const isActive = stepIdx === currentStep
                return (
                  <div
                    key={j}
                    className={[
                      'w-1.5 h-1.5 rounded-full transition-colors',
                      isDone
                        ? 'bg-green-500'
                        : isActive
                        ? 'bg-blue-500'
                        : 'bg-body-disabled',
                    ].join(' ')}
                  />
                )
              })}
            </div>
          </div>
        )
      })}

      {/* Overall step label */}
      <div className="pl-2 text-xs text-body-faint whitespace-nowrap">
        {Math.min(currentStep, WIZARD_SLOT_ORDER.length)}/{WIZARD_SLOT_ORDER.length}
      </div>
    </div>
  )
}
