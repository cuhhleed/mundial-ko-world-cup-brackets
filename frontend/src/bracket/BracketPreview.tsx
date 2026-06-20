import { BracketLayout } from './BracketLayout'
import type { BracketState } from './types'

type Props = {
  bracketState: BracketState
  onStartOver: () => void
  onSubmit?: () => void  // wired in S6
}

export function BracketPreview({ bracketState, onStartOver, onSubmit }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Your Bracket</h2>
          <p className="text-sm text-gray-500 mt-0.5">Review your picks before submitting.</p>
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onStartOver}
            className="px-4 py-2 rounded-lg text-sm text-red-500 border border-red-200
                       hover:bg-red-50 transition-colors"
          >
            Start over
          </button>
          <button
            type="button"
            onClick={onSubmit}
            disabled={!onSubmit}
            className="px-6 py-2 rounded-lg text-sm font-semibold text-white bg-blue-600
                       hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed
                       transition-colors"
          >
            Submit bracket
          </button>
        </div>
      </div>

      <BracketLayout bracketState={bracketState} />
    </div>
  )
}
