import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "@/auth/AuthContext";

export function Login() {
  const { isAuthenticated, isLoading, authenticateWithGoogle } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from =
    (location.state as { from?: { pathname: string } } | null)?.from
      ?.pathname ?? "/bracket";
  const [loginError, setLoginError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, from]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-64">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  async function handleSuccess(credentialResponse: { credential?: string }) {
    if (!credentialResponse.credential) return;
    setLoginError(null);
    try {
      await authenticateWithGoogle(credentialResponse.credential);
      navigate(from, { replace: true });
    } catch (err) {
      if (err instanceof Error && err.message === "NO_ACCOUNT") {
        setLoginError("No account found. Submit a bracket to sign up.");
      }
      // Other errors (network, API): Google button stays visible
    }
  }

  return (
    <div className="flex justify-center items-start pt-16">
      <div className="bg-surface rounded-lg shadow p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold text-body mb-2">Log In</h1>
        <p className="text-sm text-body-muted mb-6">
          Sign into your account with Google to view your bracket and your
          leaderboard position!
        </p>
        <div className="flex justify-center">
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={() => {
              /* GIS handles its own error UI */
            }}
          />
        </div>
        {loginError && (
          <p className="text-red-600 text-sm mt-4 text-center">{loginError}</p>
        )}
      </div>
    </div>
  );
}
