import { useState } from "react";
import { Link, Outlet } from "react-router";
import { useAuth } from "@/auth/AuthContext";
import { useTheme } from "@/theme/ThemeContext";
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
        className="font-display text-lg text-body font-medium hover:text-blue-600"
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
          className="border border-edge rounded px-2 py-1 text-sm text-body bg-surface focus:outline-none focus:ring-2 focus:ring-blue-600 w-36"
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
        className="text-body-muted text-sm hover:underline"
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
        className="bg-blue-600 text-white font-bold px-4 py-1.5 rounded hover:bg-blue-700 self-center"
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
        className="bg-red-600 text-white text-sm font-bold px-4 py-1.5 rounded hover:bg-red-700 self-center"
      >
        Log Out
      </button>
    </div>
  );
}

function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      type="button"
      onClick={toggle}
      className="p-2 rounded-lg text-body-muted hover:text-body transition-colors"
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
    >
      {theme === "dark" ? (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      ) : (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      )}
    </button>
  );
}

export function RootLayout() {
  const { isAuthenticated } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navLinks = [
    { to: "/", label: "Home" },
    {
      to: "/bracket",
      label: isAuthenticated ? "My Bracket" : "Build A Bracket",
    },
    { to: "/leaderboard", label: "Leaderboard" },
    { to: "/live", label: "Live" },
  ];

  return (
    <div className="min-h-screen bg-page">
      <nav className="bg-nav shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link
                to="/"
                className="text-2xl font-bold text-blue-600 flex items-center-safe"
              >
                <TeamFlag code={"TBD"} className="w-9 h-9 m-1" />
                <span className="font-display leading-none translate-y-0.5">
                  Mundial
                </span>
                <span className="font-display leading-none translate-y-0.5 text-red-600">
                  KO
                </span>
              </Link>
            </div>

            {/* Desktop nav */}
            <div className="hidden md:flex items-center space-x-8">
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className="font-display text-lg uppercase tracking-wide text-body-secondary hover:text-blue-600"
                >
                  {link.label}
                </Link>
              ))}
              <ThemeToggle />
              <NavAuth />
            </div>

            {/* Mobile hamburger */}
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="md:hidden flex items-center p-2 text-body-muted hover:text-body"
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
          <div className="fixed inset-y-0 right-0 w-64 bg-nav shadow-xl flex flex-col">
            <div className="flex items-center justify-between px-4 h-16 shadow">
              <span className="font-display text-xl font-bold text-blue-600">
                Menu
              </span>
              <button
                type="button"
                onClick={() => setSidebarOpen(false)}
                className="p-2 text-body-muted hover:text-body"
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
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setSidebarOpen(false)}
                  className="font-display text-lg uppercase tracking-wide px-6 py-3 text-body-secondary hover:text-blue-600 font-medium"
                >
                  {link.label}
                </Link>
              ))}
            </div>
            <div className="mt-auto shadow-[0_-2px_4px_rgba(0,0,0,0.1)] px-6 py-4 flex flex-col gap-4">
              <ThemeToggle />
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
