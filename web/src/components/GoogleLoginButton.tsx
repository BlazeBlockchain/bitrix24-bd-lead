import { useEffect, useRef, useState } from 'react';

interface GoogleLoginButtonProps {
  onSuccess: (idToken: string) => void;
  onError: (error: string) => void;
}

/**
 * Google Sign-In button using Google Identity Services (GIS).
 * Loads the GIS script on mount and renders the branded sign-in button.
 */
export function GoogleLoginButton({ onSuccess, onError }: GoogleLoginButtonProps) {
  const buttonRef = useRef<HTMLDivElement>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if GIS is already loaded
    if (typeof google !== 'undefined' && google?.accounts?.id) {
      setLoaded(true);
      return;
    }

    // Load the GIS script
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => setLoaded(true);
    script.onerror = () => {
      const msg = 'Failed to load Google Identity Services. Check your network connection.';
      setError(msg);
      onError(msg);
    };
    document.head.appendChild(script);

    return () => {
      // Cleanup if component unmounts before script loads
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, [onError]);

  useEffect(() => {
    if (!loaded || !buttonRef.current) return;

    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      const msg = 'VITE_GOOGLE_CLIENT_ID not configured in environment.';
      setError(msg);
      onError(msg);
      return;
    }

    try {
      google.accounts.id.initialize({
        client_id: clientId,
        callback: (response: { credential: string }) => {
          if (response.credential) {
            onSuccess(response.credential);
          } else {
            onError('No credential received from Google.');
          }
        },
        cancel_on_tap_outside: false,
      });

      google.accounts.id.renderButton(
        buttonRef.current,
        {
          type: 'standard',
          shape: 'rectangular',
          theme: 'outline',
          size: 'large',
          text: 'signin_with',
          width: 280,
        }
      );
    } catch (e) {
      const msg = `Google Sign-In initialization failed: ${e instanceof Error ? e.message : 'Unknown error'}`;
      setError(msg);
      onError(msg);
    }
  }, [loaded, onSuccess, onError]);

  if (error) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 16 }}>
        <p style={{ color: 'var(--red)' }}>{error}</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', minHeight: 48, alignItems: 'center' }}>
      <div ref={buttonRef} />
      {!loaded && <p style={{ color: 'var(--muted)' }}>Loading Google Sign-In...</p>}
    </div>
  );
}
