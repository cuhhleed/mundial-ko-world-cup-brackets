import { Link, Outlet } from 'react-router'

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
