import { useState } from 'react'
import { Link, Outlet } from 'react-router'
import { useAuth } from '@/auth/AuthContext'

const DISPLAY_NAME_RE = /^[A-Za-z0-9 ]{3,30}$/

function DisplayNameEdit({ name }: { name: string }) {
  const { updateDisplayName } = useAuth()
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(name)
  const [validationError, setValidationError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  function startEdit() {
    setValue(name)
    setValidationError(null)
    setEditing(true)
  }

  function cancel() {
    setEditing(false)
    setValidationError(null)
  }

  async function save() {
    const trimmed = value.trim()
    if (!DISPLAY_NAME_RE.test(trimmed)) {
      setValidationError('3-30 characters, letters, numbers, and spaces only')
      return
    }
    setIsSaving(true)
    try {
      await updateDisplayName(trimmed)
      setEditing(false)
    } catch {
      setValidationError('Failed to save')
    } finally {
      setIsSaving(false)
    }
  }

  if (!editing) {
    return (
      <button
        type="button"
        onClick={startEdit}
        className="text-gray-900 font-medium hover:text-blue-600"
        title="Click to edit display name"
      >
        {name}
      </button>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <div>
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-600 w-36"
          maxLength={30}
          autoFocus
          onKeyDown={(e) => {
            if (e.key === 'Enter') save()
            if (e.key === 'Escape') cancel()
          }}
        />
        {validationError && (
          <p className="text-red-600 text-xs mt-1">{validationError}</p>
        )}
      </div>
      <button
        type="button"
        onClick={save}
        disabled={isSaving}
        className="text-blue-600 text-sm hover:underline disabled:opacity-50"
      >
        Save
      </button>
      <button
        type="button"
        onClick={cancel}
        className="text-gray-500 text-sm hover:underline"
      >
        Cancel
      </button>
    </div>
  )
}

function NavAuth() {
  const { user, isLoading, isAuthenticated, logout } = useAuth()

  if (isLoading) return null

  if (!isAuthenticated || !user) {
    return (
      <Link to="/login" className="text-blue-600 font-medium hover:text-blue-700">
        Log In
      </Link>
    )
  }

  return (
    <div className="flex items-center gap-4">
      <DisplayNameEdit name={user.displayName} />
      <button
        type="button"
        onClick={logout}
        className="text-gray-500 text-sm hover:text-gray-700"
      >
        Log Out
      </button>
    </div>
  )
}

export function RootLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-2xl font-bold text-blue-600">
                Mundial KO
              </Link>
            </div>
            <div className="flex items-center space-x-8">
              <Link to="/" className="text-gray-700 hover:text-gray-900">
                Home
              </Link>
              <Link to="/bracket" className="text-gray-700 hover:text-gray-900">
                Bracket
              </Link>
              <Link to="/leaderboard" className="text-gray-700 hover:text-gray-900">
                Leaderboard
              </Link>
              <Link to="/live" className="text-gray-700 hover:text-gray-900">
                Live
              </Link>
              <NavAuth />
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
