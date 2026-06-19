import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { GoogleLogin } from '@react-oauth/google'
import { useAuth } from '@/auth/AuthContext'

type Props = {
  isOpen: boolean
  onClose: () => void
  onAuthenticated: () => void
}

type ModalStep = 'confirm' | 'google'

export function SignUpModal({ isOpen, onClose, onAuthenticated }: Props) {
  const { authenticateWithGoogle } = useAuth()
  const [step, setStep] = useState<ModalStep>('confirm')
  const [authError, setAuthError] = useState<string | null>(null)

  useEffect(() => {
    if (!isOpen) {
      setStep('confirm')
      setAuthError(null)
    }
  }, [isOpen])

  async function handleGoogleSuccess(credentialResponse: { credential?: string }) {
    if (!credentialResponse.credential) return
    setAuthError(null)
    try {
      await authenticateWithGoogle(credentialResponse.credential)
      onAuthenticated()
    } catch {
      setAuthError('Something went wrong. Please try again.')
    }
  }

  if (!isOpen) return null

  const modal = (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative bg-white rounded-lg shadow-xl p-8 w-full max-w-md mx-4">

        {step === 'confirm' && (
          <>
            <h2 className="text-xl font-bold text-gray-900 mb-4">Submit Bracket</h2>
            <p className="text-gray-700 mb-6">
              Your bracket is final and cannot be edited after submission.
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStep('google')}
                className="flex-1 bg-blue-600 text-white rounded-md py-2 font-medium hover:bg-blue-700"
              >
                Continue
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 border border-gray-300 text-gray-700 rounded-md py-2 font-medium hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </>
        )}

        {step === 'google' && (
          <>
            <h2 className="text-xl font-bold text-gray-900 mb-4">Sign In to Submit</h2>
            <p className="text-gray-600 mb-6">
              Sign in with Google to save your bracket.
            </p>
            <div className="flex justify-center">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={() => setAuthError('Google sign-in failed. Please try again.')}
              />
            </div>
            {authError && (
              <p className="text-red-600 text-sm mt-3 text-center">{authError}</p>
            )}
          </>
        )}

      </div>
    </div>
  )

  return createPortal(modal, document.body)
}
