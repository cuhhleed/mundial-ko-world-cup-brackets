import { useAuth } from '@/auth/AuthContext'
import { BracketCreator } from '@/bracket/BracketCreator'
import { BracketViewer } from '@/bracket/BracketViewer'

export function Bracket() {
  const { isLoading, isAuthenticated } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-8 h-8 border-2 border-edge border-t-blue-500 rounded-full animate-spin" />
      </div>
    )
  }

  if (isAuthenticated) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-bold">Your Bracket</h1>
        <BracketViewer />
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
