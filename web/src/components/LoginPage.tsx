import { useState } from 'react';
import { useAppStore } from '../stores/appStore';
import { GoogleLoginButton } from './GoogleLoginButton';
import { exchangeGoogleToken, storeAuth } from '../api/auth';

/**
 * Login page with Google Sign-In.
 * Handles the full OAuth flow: Google popup -> backend token exchange -> store JWT.
 */
export function LoginPage() {
  const { setAuthFromToken } = useAppStore();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGoogleSuccess = async (idToken: string) => {
    setError(null);
    setLoading(true);
    try {
      const authResponse = await exchangeGoogleToken(idToken);
      storeAuth(authResponse);
      setAuthFromToken(authResponse.access_token, authResponse.user);
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Authentication failed. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = (msg: string) => {
    setError(msg);
  };

  return (
    <div className="page" style={{ maxWidth: 420, margin: '0 auto', paddingTop: 60 }}>
      <div className="card" style={{ textAlign: 'center', padding: 32 }}>
        <h1 style={{ marginBottom: 8 }}>BD Lead Assistant</h1>
        <p style={{ color: 'var(--muted)', marginBottom: 24 }}>
          Sign in with Google to start enriching leads
        </p>

        {loading ? (
          <p style={{ color: 'var(--muted)' }}>Verifying authentication...</p>
        ) : (
          <GoogleLoginButton onSuccess={handleGoogleSuccess} onError={handleGoogleError} />
        )}

        {error && (
          <p style={{ color: 'var(--danger)', marginTop: 16, fontSize: 14 }}>{error}</p>
        )}

        <div style={{ marginTop: 24, fontSize: 12, color: 'var(--muted)' }}>
          <p>Your Google account info is used only for authentication.</p>
          <p>CRM credentials are stored encrypted and never shared.</p>
        </div>
      </div>
    </div>
  );
}
