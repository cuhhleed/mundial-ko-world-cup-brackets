import { useMemo, useState } from 'react'
import { SignUpModal } from '@/auth/SignUpModal'
import { BracketLayout } from './BracketLayout'
import { buildPayload, getCompletionStatus } from './payload'
import type { BracketState } from './types'

type Props = {
  bracketState: BracketState
  onStartOver: () => void
}

export function BracketPreview({ bracketState, onStartOver }: Props) {
  const [modalOpen, setModalOpen] = useState(false)

  const predictions = useMemo(
    () => buildPayload(bracketState.slots),
    [bracketState.slots],
  )
  const { isComplete } = useMemo(
    () => getCompletionStatus(bracketState.slots),
    [bracketState.slots],
  )

  const allLocked = useMemo(
    () => Object.values(bracketState.slots).every((s) => s.locked),
    [bracketState.slots],
  )

  return (
    <>
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-body">Your Bracket</h2>
            <p className="text-sm text-body-muted mt-0.5">
              {allLocked
                ? 'The tournament has ended, come back for World Cup 2030!'
                : 'Review your picks before submitting.'}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onStartOver}
              disabled={allLocked}
              className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-bold
                         hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed
                         transition-colors self-center"
            >
              Start over
            </button>
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              disabled={!isComplete || allLocked}
              className="px-6 py-2 rounded-lg text-sm font-bold text-white bg-blue-600
                         hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed
                         transition-colors self-center"
            >
              Submit bracket
            </button>
          </div>
        </div>

        <BracketLayout bracketState={bracketState} />
      </div>

      <SignUpModal
        isOpen={modalOpen}
        predictions={predictions}
        onClose={() => setModalOpen(false)}
        onAuthenticated={() => setModalOpen(false)}
      />
    </>
  )
}
