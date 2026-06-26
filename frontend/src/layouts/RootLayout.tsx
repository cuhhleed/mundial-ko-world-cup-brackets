import { useState } from "react";
import { Link, Outlet } from "react-router";
import { useAuth } from "@/auth/AuthContext";
import { TeamFlag } from "@/components/TeamFlag";

const DISPLAY_NAME_RE = /^[A-Za-z0-9 ]{3,30}$/;

function DisplayNameEdit({ name }: { name: string }) {
  const { updateDisplayName } = useAuth();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(name);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  function startEdit() {
    setValue(name);
    setValidationError(null);
    setEditing(true);
  }

  function cancel() {
    setEditing(false);
    setValidationError(null);
  }

  async function save() {
    const trimmed = value.trim();
    if (!DISPLAY_NAME_RE.test(trimmed)) {
      setValidationError("3-30 characters, letters, numbers, and spaces only");
      return;
    }
    setIsSaving(true);
    try {
      await updateDisplayName(trimmed);
      setEditing(false);
    } catch {
      setValidationError("Failed to save");
    } finally {
      setIsSaving(false);
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
    );
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
            if (e.key === "Enter") save();
            if (e.key === "Escape") cancel();
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
  );
}

function NavAuth() {
  const { user, isLoading, isAuthenticated, logout } = useAuth();

  if (isLoading) return null;

  if (!isAuthenticated || !user) {
    return (
      <Link
        to="/login"
        className="text-blue-600 font-medium hover:text-blue-700"
      >
        Log In
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-4">
      <DisplayNameEdit name={user.displayName} />
      <button
        type="button"
        onClick={logout}
        className="text-red-500 text-sm hover:text-red-700"
      >
        Log Out
      </button>
    </div>
  );
}

const NAV_LINKS = [
  { to: "/", label: "Home" },
  { to: "/bracket", label: "Bracket" },
  { to: "/leaderboard", label: "Leaderboard" },
  { to: "/live", label: "Live" },
];

export function RootLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link
                to="/"
                className="text-2xl font-bold text-blue-600 flex gap-1"
              >
                <TeamFlag code={"TBD"} className="w-9 h-9" />
                <span>Mundial</span>
                <span className="text-red-600">KO</span>
              </Link>
            </div>

            {/* Desktop nav */}
            <div className="hidden md:flex items-center space-x-8">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className="text-gray-700 hover:text-gray-900"
                >
                  {link.label}
                </Link>
              ))}
              <NavAuth />
            </div>

            {/* Mobile hamburger */}
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="md:hidden flex items-center p-2 text-gray-600 hover:text-gray-900"
              aria-label="Open menu"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="fixed inset-0 bg-black/30"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="fixed inset-y-0 right-0 w-64 bg-white shadow-xl flex flex-col">
            <div className="flex items-center justify-between px-4 h-16 border-b">
              <span className="text-lg font-bold text-blue-600">Menu</span>
              <button
                type="button"
                onClick={() => setSidebarOpen(false)}
                className="p-2 text-gray-500 hover:text-gray-900"
                aria-label="Close menu"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            <div className="flex flex-col py-4">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setSidebarOpen(false)}
                  className="px-6 py-3 text-gray-700 hover:bg-gray-50 hover:text-gray-900 font-medium"
                >
                  {link.label}
                </Link>
              ))}
            </div>
            <div className="mt-auto border-t px-6 py-4">
              <NavAuth />
            </div>
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}
