import { BrowserRouter, Routes, Route } from 'react-router'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { AuthProvider } from '@/auth/AuthContext'
import { ThemeProvider } from '@/theme/ThemeContext'
import { RootLayout } from '@/layouts/RootLayout'
import { Home } from '@/pages/Home'
import { Bracket } from '@/pages/Bracket'
import { Leaderboard } from '@/pages/Leaderboard'
import { LiveBracket } from '@/pages/LiveBracket'
import { Login } from '@/pages/Login'
import { config } from '@/config'

export function App() {
  return (
    <ThemeProvider>
      <GoogleOAuthProvider clientId={config.googleClientId}>
        <BrowserRouter>
          <AuthProvider>
          <Routes>
            <Route element={<RootLayout />}>
              <Route path="/" element={<Home />} />
              <Route path="/bracket" element={<Bracket />} />
              <Route path="/leaderboard" element={<Leaderboard />} />
              <Route path="/live" element={<LiveBracket />} />
              <Route path="/login" element={<Login />} />
            </Route>
          </Routes>
          </AuthProvider>
        </BrowserRouter>
      </GoogleOAuthProvider>
    </ThemeProvider>
  )
}
