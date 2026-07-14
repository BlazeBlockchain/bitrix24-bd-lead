/**
 * Changelog Component (T033).
 *
 * Displays the project CHANGELOG.md imported at build time.
 * Single source of truth: repo-root CHANGELOG.md via Vite ?raw import.
 */

import changelogRaw from '@repo/CHANGELOG.md?raw';

export function Changelog() {
  return (
    <div className="page">
      <h1>Changelog</h1>
      <div className="card">
        <pre
          style={{
            overflow: 'auto',
            fontSize: 13,
            lineHeight: 1.6,
            fontFamily: 'var(--mono)',
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
          }}
        >
          {changelogRaw}
        </pre>
      </div>
    </div>
  );
}
