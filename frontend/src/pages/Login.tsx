import { useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router'
import { GoogleLogin } from '@react-oauth/google'
import { useAuth } from '@/auth/AuthContext'

export function Login() {
  const { isAuthenticated, isLoading, authenticateWithGoogle } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? '/bracket'

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, isLoading, navigate, from])

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-64">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  async function handleSuccess(credentialResponse: { credential?: string }) {
    if (!credentialResponse.credential) return
    try {
      await authenticateWithGoogle(credentialResponse.credential)
      navigate(from, { replace: true })
    } catch {
      // authenticateWithGoogle failure (e.g. network) — GIS button stays visible
    }
  }

  return (
    <div className="flex justify-center items-start pt-16">
      <div className="bg-white rounded-lg shadow p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Log In</h1>
        <div className="flex justify-center">
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={() => {/* GIS handles its own error UI */}}
            auto_select
            useOneTap
          />
        </div>
      </div>
    </div>
  )
}
