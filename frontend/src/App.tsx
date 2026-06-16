import { BrowserRouter, Routes, Route } from 'react-router'
import { RootLayout } from '@/layouts/RootLayout'
import { Home } from '@/pages/Home'
import { Bracket } from '@/pages/Bracket'
import { Leaderboard } from '@/pages/Leaderboard'
import { LiveBracket } from '@/pages/LiveBracket'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<RootLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/bracket" element={<Bracket />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/live" element={<LiveBracket />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
