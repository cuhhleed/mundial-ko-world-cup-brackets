import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, setAuthToken, setOnUnauthorized } from '@/api/client'
import { saveToken, loadToken, clearToken, isTokenExpired } from '@/auth/tokens'

type User = {
  id: string
  email: string
  displayName: string
}

type UserRecord = {
  user_id: string
  email: string
  display_name: string
  bracket_id?: string | null
  created_at: string
}

type AuthContextValue = {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  authenticateWithGoogle: (idToken: string) => Promise<void>
  signupWithBracket: (idToken: string, predictions: Record<string, unknown>) => Promise<void>
  logout: () => void
  updateDisplayName: (name: string) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  function doLogout() {
    clearToken()
    setAuthToken(null)
    setUser(null)
  }

  // On a 401 (expired ~1h token), clear state so the UI re-prompts Google.
  // No refresh token in ADR-004b — the GoogleLogin button / One Tap handles re-auth.
  useEffect(() => {
    setOnUnauthorized(async () => {
      doLogout()
      return null
    })
  }, [])

  // Hydrate on mount: restore session from sessionStorage if the token is still valid.
  useEffect(() => {
    async function hydrate() {
      const stored = loadToken()
      if (!stored || isTokenExpired(stored)) {
        if (stored) clearToken()
        setIsLoading(false)
        return
      }

      setAuthToken(stored)
      try {
        const record = await api.get<UserRecord>('/api/users/me')
        setUser({
          id: record.user_id,
          email: record.email,
          displayName: record.display_name,
        })
      } catch {
        doLogout()
      } finally {
        setIsLoading(false)
      }
    }

    hydrate()
  }, [])

  // Login-only: verifies the Google JWT, checks the user exists, then fetches their record.
  // Throws 'NO_ACCOUNT' if the user has not signed up yet.
  const authenticateWithGoogle = useCallback(async (idToken: string) => {
    const { exists } = await api.post<{ exists: boolean }>('/api/auth/check', { token: idToken })
    if (!exists) {
      throw new Error('NO_ACCOUNT')
    }
    saveToken(idToken)
    setAuthToken(idToken)
    const record = await api.get<UserRecord>('/api/users/me')
    setUser({
      id: record.user_id,
      email: record.email,
      displayName: record.display_name,
    })
  }, [])

  // Signup: creates user + bracket atomically via POST /api/auth/signup.
  const signupWithBracket = useCallback(
    async (idToken: string, predictions: Record<string, unknown>) => {
      const response = await api.post<{ user: UserRecord; bracket: unknown }>(
        '/api/auth/signup',
        { token: idToken, predictions },
      )
      saveToken(idToken)
      setAuthToken(idToken)
      setUser({
        id: response.user.user_id,
        email: response.user.email,
        displayName: response.user.display_name,
      })
    },
    [],
  )

  const logout = doLogout

  const updateDisplayName = useCallback(async (name: string) => {
    const record = await api.patch<UserRecord>('/api/users/me', { display_name: name })
    setUser((prev) => (prev ? { ...prev, displayName: record.display_name } : prev))
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        authenticateWithGoogle,
        signupWithBracket,
        logout,
        updateDisplayName,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
