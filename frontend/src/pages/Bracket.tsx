import { useAuth } from '@/auth/AuthContext'
import { BracketCreator } from '@/bracket/BracketCreator'

export function Bracket() {
  const { isLoading, isAuthenticated } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-8 h-8 border-2 border-gray-200 border-t-blue-500 rounded-full animate-spin" />
      </div>
    )
  }

  if (isAuthenticated) {
    // Bracket viewer for signed-in users with existing bracket (S7)
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-bold">Your Bracket</h1>
        <p className="text-gray-500">Bracket viewer coming in S7.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Create Your Bracket</h1>
      <BracketCreator />
    </div>
  )
}
