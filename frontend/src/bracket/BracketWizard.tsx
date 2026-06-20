import { useEffect } from 'react'
import { ROUNDS, SCORE_BEARING_SLOTS, WIZARD_SLOT_ORDER } from './topology'
import type { BracketAction, BracketState } from './types'
import { WizardProgressBar } from './WizardProgressBar'
import { WizardPrompt } from './WizardPrompt'
import { WizardScorePrompt } from './WizardScorePrompt'

type Props = {
  bracketState: BracketState
  dispatch: (action: BracketAction) => void
  currentStep: number
  onStepChange: (step: number) => void
  onStartOver: () => void
}

export function BracketWizard({
  bracketState,
  dispatch,
  currentStep,
  onStepChange,
  onStartOver,
}: Props) {
  const slotId = WIZARD_SLOT_ORDER[currentStep]
  const slot = bracketState.slots[slotId]
  const isScoreBearing = SCORE_BEARING_SLOTS.has(slotId)

  function handleRoundClick(roundId: string) {
    // Find the first step index for this round
    let firstStep = 0
    for (const round of ROUNDS) {
      if (round.id === roundId) break
      firstStep += round.slots.length
    }
    dispatch({ type: 'CLEAR_FROM_ROUND', roundId })
    onStepChange(firstStep)
  }

  function handleSelectWinner(winner: string) {
    // Skip locked slots automatically
    if (slot?.locked) {
      onStepChange(currentStep + 1)
      return
    }
    dispatch({ type: 'SELECT_WINNER', slotId, winner })
    onStepChange(currentStep + 1)
  }

  function handleScoreConfirm() {
    onStepChange(currentStep + 1)
  }

  function handleBack() {
    if (currentStep === 0) return
    const prevSlotId = WIZARD_SLOT_ORDER[currentStep - 1]
    const prevSlot = bracketState.slots[prevSlotId]
    if (prevSlot && !prevSlot.locked) {
      dispatch({ type: 'CLEAR_SLOT', slotId: prevSlotId })
    }
    onStepChange(currentStep - 1)
  }

  // Auto-skip locked slots without calling setState during render
  useEffect(() => {
    if (slot?.locked) {
      onStepChange(currentStep + 1)
    }
  }, [slot, currentStep, onStepChange])

  if (slot?.locked) return null

  return (
    <div className="flex flex-col gap-6">
      <WizardProgressBar currentStep={currentStep} onRoundClick={handleRoundClick} />

      <div className="min-h-72 flex flex-col items-center justify-center">
        {isScoreBearing ? (
          <WizardScorePrompt
            slotId={slotId}
            teams={slot?.teams ?? null}
            scores={slot?.scores ?? null}
            pkScores={slot?.pkScores ?? null}
            winner={slot?.winner ?? null}
            onScoresChange={(scores) => dispatch({ type: 'SET_SCORES', slotId, scores })}
            onPkChange={(pkScores) => dispatch({ type: 'SET_PK', slotId, pkScores })}
            onConfirm={handleScoreConfirm}
          />
        ) : (
          <WizardPrompt
            slotId={slotId}
            teams={slot?.teams ?? null}
            onSelect={handleSelectWinner}
          />
        )}
      </div>

      <div className="flex justify-between items-center pt-2 border-t border-gray-100">
        <button
          type="button"
          onClick={handleBack}
          disabled={currentStep === 0}
          className="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100
                     disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          ← Back
        </button>

        <button
          type="button"
          onClick={onStartOver}
          className="px-4 py-2 rounded-lg text-sm text-red-500 hover:bg-red-50 transition-colors"
        >
          Start over
        </button>
      </div>
    </div>
  )
}
