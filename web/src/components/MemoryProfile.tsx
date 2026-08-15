import React, { useState, useEffect } from 'react';
import { useAppStore } from '../stores/appStore';
import {
  getMemoryProfile,
  saveMemoryProfile,
  type MemoryProfileResponse,
} from '../api/client';

/**
 * Memory Profile Editor (T024).
 * Allows user to save tone samples, ICP industries, and follow-up cadence.
 * These are injected into the LLM for personalized lead enrichment.
 */
export const MemoryProfile: React.FC = () => {
  const { isLoggedIn } = useAppStore();

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [editingOpener, setEditingOpener] = useState<string>('');

  // Form state
  const [icpIndustries, setIcpIndustries] = useState<string>(''); // comma-separated input
  const [cadence1, setCadence1] = useState<number>(4);
  const [cadence2, setCadence2] = useState<number>(9);
  const [cadence3, setCadence3] = useState<number>(14);
  const [toneSamples, setToneSamples] = useState<any[]>([]);

  // Load memory profile on mount
  useEffect(() => {
    if (isLoggedIn) {
      loadProfile();
    }
  }, [isLoggedIn]);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const profile: MemoryProfileResponse = await getMemoryProfile();
      setIcpIndustries((profile.icp_industries || []).join(', '));
      const cadence = profile.typical_cadence || [4, 9, 14];
      setCadence1(cadence[0] || 4);
      setCadence2(cadence[1] || 9);
      setCadence3(cadence[2] || 14);
      setToneSamples(profile.tone_samples || []);
      setMessage(null);
    } catch (err) {
      console.debug('Failed to load memory profile (may be new user):', err);
      // New user; start with defaults
      setToneSamples([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!isLoggedIn) {
      window.location.href = '/login';
      return;
    }

    setSaving(true);
    setMessage(null);

    try {
      const industries = icpIndustries
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const cadence = [cadence1, cadence2, cadence3];

      await saveMemoryProfile({
        icp_industries: industries.length > 0 ? industries : undefined,
        typical_cadence: cadence,
        tone_samples: toneSamples.map((ts) => ({
          opener: ts.opener || '',
          outcome: ts.outcome || undefined,
        })),
      });

      setMessage({ type: 'success', text: 'Memory profile saved!' });
      // Reload to confirm persistence
      await loadProfile();
    } catch (err) {
      setMessage({ type: 'error', text: `Failed to save: ${(err as Error).message}` });
    } finally {
      setSaving(false);
    }
  };

  const handleAddToneSample = () => {
    if (!editingOpener.trim()) {
      setMessage({ type: 'error', text: 'Please enter an opener' });
      return;
    }

    const newSample = {
      id: Date.now().toString(),
      opener: editingOpener,
      outcome: 'accepted', // default; can be edited later
      accepted_at: new Date().toISOString(),
    };

    setToneSamples((prev) => [newSample, ...prev]);
    setEditingOpener('');
    setMessage({ type: 'success', text: 'Tone sample added!' });
  };

  const handleRemoveToneSample = (id: string) => {
    setToneSamples((prev) => prev.filter((ts) => ts.id !== id));
  };

  if (!isLoggedIn) {
    return (
      <div className="page">
        <h1>Memory Profile</h1>
        <div className="card">
          <p>Please sign in to customize your memory profile.</p>
          <button onClick={() => window.location.href = '/login'}>Sign in with Google</button>
        </div>
      </div>
    );
  }

  return (
    <div className="main-content">
      <div className="card" style={{ maxWidth: 620 }}>
        <h2>Memory Profile</h2>
        <p style={{ color: 'var(--muted)', fontSize: 13 }}>
          Customize how AI enriches leads based on your personal tone, target industries, and follow-up cadence.
        </p>

        {loading ? (
          <p>Loading profile...</p>
        ) : (
          <>
            {/* ICP Industries */}
            <div style={{ marginBottom: 16 }}>
              <label>
                Target Industries <span style={{ color: 'var(--muted)', fontSize: 12 }}>(comma-separated)</span>
              </label>
              <input
                type="text"
                value={icpIndustries}
                onChange={(e) => setIcpIndustries(e.target.value)}
                placeholder="e.g., SaaS, FinTech, B2B"
                disabled={saving}
              />
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
                Examples: SaaS, FinTech, Healthcare, B2B, Enterprise, Startups
              </div>
            </div>

            {/* Typical Cadence */}
            <div style={{ marginBottom: 16 }}>
              <label>Typical Follow-up Cadence (days between outreach)</label>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 8 }}>
                <div style={{ flex: 1 }}>
                  <input
                    type="number"
                    min="1"
                    value={cadence1}
                    onChange={(e) => setCadence1(parseInt(e.target.value) || 4)}
                    disabled={saving}
                    style={{ width: '100%' }}
                  />
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>1st follow-up</div>
                </div>
                <span style={{ color: 'var(--muted)' }}>→</span>
                <div style={{ flex: 1 }}>
                  <input
                    type="number"
                    min="1"
                    value={cadence2}
                    onChange={(e) => setCadence2(parseInt(e.target.value) || 9)}
                    disabled={saving}
                    style={{ width: '100%' }}
                  />
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>2nd follow-up</div>
                </div>
                <span style={{ color: 'var(--muted)' }}>→</span>
                <div style={{ flex: 1 }}>
                  <input
                    type="number"
                    min="1"
                    value={cadence3}
                    onChange={(e) => setCadence3(parseInt(e.target.value) || 14)}
                    disabled={saving}
                    style={{ width: '100%' }}
                  />
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>3rd follow-up</div>
                </div>
              </div>
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>
                Current cadence: +{cadence1} / +{cadence2} / +{cadence3} days
              </div>
            </div>

            {/* Tone Samples */}
            <div style={{ marginBottom: 16 }}>
              <label>Tone Samples</label>
              <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
                Add example openers that have worked well for you. These help AI understand your personal style.
              </p>

              {/* Add new tone sample */}
              <div style={{ marginTop: 12, marginBottom: 16, padding: 12, backgroundColor: 'var(--bg-subtle)', borderRadius: 4 }}>
                <textarea
                  value={editingOpener}
                  onChange={(e) => setEditingOpener(e.target.value)}
                  placeholder="Paste a successful opening email (e.g., 'Hi John, saw your Series B announcement—here's how we helped similar companies...')"
                  style={{ width: '100%', minHeight: 80, marginBottom: 8 }}
                  disabled={saving}
                />
                <button
                  onClick={handleAddToneSample}
                  disabled={!editingOpener.trim() || saving}
                  style={{ opacity: !editingOpener.trim() || saving ? 0.6 : 1 }}
                >
                  Add Sample
                </button>
              </div>

              {/* List tone samples */}
              {toneSamples.length > 0 ? (
                <div style={{ marginBottom: 16 }}>
                  <h4 style={{ marginBottom: 8 }}>Saved Tone Samples ({toneSamples.length})</h4>
                  {toneSamples.map((sample) => (
                    <div
                      key={sample.id}
                      style={{
                        padding: 12,
                        marginBottom: 8,
                        backgroundColor: 'var(--bg-subtle)',
                        borderRadius: 4,
                        borderLeft: '3px solid var(--accent)',
                      }}
                    >
                      <p style={{ margin: '0 0 8px 0', fontSize: 13 }}>{sample.opener}</p>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: 12, color: 'var(--muted)' }}>
                          Status: <strong>{sample.outcome || 'pending'}</strong>
                          {sample.accepted_at && ` • ${new Date(sample.accepted_at).toLocaleDateString()}`}
                        </span>
                        <button
                          onClick={() => handleRemoveToneSample(sample.id)}
                          className="secondary"
                          disabled={saving}
                          style={{ padding: '4px 8px', fontSize: 12 }}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ fontSize: 12, color: 'var(--muted)', fontStyle: 'italic' }}>No tone samples yet. Add one to get started.</p>
              )}
            </div>

            {/* Message */}
            {message && (
              <div
                style={{
                  marginBottom: 16,
                  padding: '8px 12px',
                  borderRadius: 4,
                  backgroundColor: message.type === 'success' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                  color: message.type === 'success' ? '#22c55e' : '#ef4444',
                  fontSize: 13,
                }}
              >
                {message.text}
              </div>
            )}

            {/* Save button */}
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={handleSave}
                disabled={saving}
                style={{
                  opacity: saving ? 0.6 : 1,
                  cursor: saving ? 'not-allowed' : 'pointer',
                }}
              >
                {saving ? 'Saving...' : 'Save Memory Profile'}
              </button>
              <button
                onClick={loadProfile}
                className="secondary"
                disabled={saving}
              >
                Reload
              </button>
            </div>
          </>
        )}
      </div>

      <div className="stub-note" style={{ marginTop: 24 }}>
        <h3>How it works</h3>
        <ul style={{ fontSize: 12, lineHeight: 1.7 }}>
          <li>Your <strong>tone samples</strong> teach AI your personal style for cold outreach.</li>
          <li><strong>ICP industries</strong> filter what types of companies you target.</li>
          <li><strong>Cadence</strong> is used to schedule follow-up tasks at your preferred intervals.</li>
          <li>These settings personalize every lead enrichment in the Composer.</li>
        </ul>
      </div>
    </div>
  );
};
