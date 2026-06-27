import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import { WIZARD_SLOT_ORDER } from './topology'
import type { ApiBracketTemplate } from './types'
import { useBracketReducer } from './useBracketReducer'
import { BracketPreview } from './BracketPreview'
import { BracketWizard } from './BracketWizard'

export function BracketCreator() {
  const [bracketState, dispatch] = useBracketReducer()
  const [currentStep, setCurrentStep] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<ApiBracketTemplate>('/api/brackets/template')
      .then((template) => {
        dispatch({ type: 'INIT_TEMPLATE', template })
      })
      .catch(() => setError('Failed to load bracket template. Please refresh.'))
      .finally(() => setIsLoading(false))
  }, [dispatch])

  function handleStartOver() {
    dispatch({ type: 'START_OVER' })
    setCurrentStep(0)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-3 text-body-faint">
          <div className="w-8 h-8 border-2 border-edge border-t-blue-500 rounded-full animate-spin" />
          <p className="text-sm">Loading bracket…</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-red-500 text-sm">{error}</p>
      </div>
    )
  }

  const wizardComplete = currentStep >= WIZARD_SLOT_ORDER.length

  if (wizardComplete) {
    return (
      <BracketPreview
        bracketState={bracketState}
        onStartOver={handleStartOver}
      />
    )
  }

  return (
    <BracketWizard
      bracketState={bracketState}
      dispatch={dispatch}
      currentStep={currentStep}
      onStepChange={setCurrentStep}
      onStartOver={handleStartOver}
    />
  )
}
