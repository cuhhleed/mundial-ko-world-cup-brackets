import { useState } from 'react'
import { useAuth } from '@/auth/AuthContext'
import { SignUpModal } from '@/auth/SignUpModal'

export function Bracket() {
  const { isAuthenticated } = useAuth()
  const [modalOpen, setModalOpen] = useState(false)

  if (isAuthenticated) {
    return (
      <div className="space-y-6">
        <h1 className="text-4xl font-bold">Bracket</h1>
        <p className="text-gray-600">Your bracket has been submitted.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-bold">Bracket</h1>
      <p className="text-gray-600">Create and manage your World Cup bracket predictions.</p>
      <button
        type="button"
        onClick={() => setModalOpen(true)}
        className="bg-blue-600 text-white rounded-md px-6 py-2 font-medium hover:bg-blue-700"
      >
        Submit Bracket
      </button>
      <SignUpModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onAuthenticated={() => setModalOpen(false)}
      />
    </div>
  )
}
