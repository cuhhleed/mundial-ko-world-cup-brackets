import { useEffect, useRef, useState } from 'react'
import { ROUNDS, SCORE_BEARING_SLOTS, WIZARD_SLOT_ORDER } from './topology'
import type { BracketAction, BracketState } from './types'
import { useTeamRecords } from './useTeamRecords'
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
  const records = useTeamRecords()
  const slotId = WIZARD_SLOT_ORDER[currentStep]
  const slot = bracketState.slots[slotId]
  const isScoreBearing = SCORE_BEARING_SLOTS.has(slotId)
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null)
  const transitionTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

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
    if (selectedTeam) return
    if (slot?.locked) {
      onStepChange(currentStep + 1)
      return
    }
    dispatch({ type: 'SELECT_WINNER', slotId, winner })
    setSelectedTeam(winner)
    transitionTimer.current = setTimeout(() => {
      setSelectedTeam(null)
      onStepChange(currentStep + 1)
    }, 500)
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

  useEffect(() => {
    return () => {
      if (transitionTimer.current) clearTimeout(transitionTimer.current)
    }
  }, [])

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
            records={records}
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
            records={records}
            onSelect={handleSelectWinner}
            selectedTeam={selectedTeam}
          />
        )}
      </div>

      <div className="flex justify-between items-center pt-2 border-t border-edge-light">
        <button
          type="button"
          onClick={handleBack}
          disabled={currentStep === 0}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-blue-700
                     disabled:opacity-30 disabled:cursor-not-allowed transition-colors self-center"
        >
          ← Back
        </button>

        <button
          type="button"
          onClick={onStartOver}
          className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-red-700 transition-colors self-center"
        >
          Start over
        </button>
      </div>
    </div>
  )
}
