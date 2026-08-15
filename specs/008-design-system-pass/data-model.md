# Data Model: Design System Pass

This feature has no persisted data and no API entities. Its "model" is the design token set, the
artwork, and the surface/state taxonomy. Defining them precisely is what makes FR-003 (drift is
detectable) and FR-011 (inert sections are honest) testable.

## Entity: Design token set

One `:root` block in `design/tokens.css`, transcribed from the handoff's `styles.css`. Every token
below MUST be present in both derived files; the drift check compares name **and** value.

### Surfaces
| Token | Value |
|---|---|
| `--bg` | `#05070d` |
| `--bg-elev` | `#0a0e18` |
| `--panel` | `rgba(255,255,255,0.025)` |
| `--panel-2` | `rgba(255,255,255,0.045)` |

### Lines
| Token | Value |
|---|---|
| `--border` | `rgba(255,255,255,0.07)` |
| `--border-hover` | `rgba(255,255,255,0.14)` |
| `--border-strong` | `rgba(255,255,255,0.2)` |

### Text ramp
| Token | Value |
|---|---|
| `--text` | `#eaecf2` |
| `--text-soft` | `#b0b6c4` |
| `--muted` | `#6b7385` |
| `--muted-dim` | `#4a5160` |

### Brand
| Token | Value |
|---|---|
| `--accent` | `#4a7cff` |
| `--accent2` | `#7c5cff` |
| `--accent3` | `#22d3ee` |
| `--grad` | `linear-gradient(135deg,#4a7cff 0%,#7c5cff 55%,#22d3ee 100%)` |
| `--grad-soft` | same hues at 14–18% alpha |
| `--grad-text` | `linear-gradient(100deg,#8ab0ff,#b4a3ff 50%,#7cdff0)` |

### Semantic
| Token | Value | Use |
|---|---|---|
| `--green` | `#10b981` | success, connected, pushed |
| `--gold` | `#f5b841` | warning; HubSpot brand tint |
| `--red` | `#ef4444` | error, session expiry |

### Radius / type / density / depth
| Token | Value |
|---|---|
| `--r-sm` / `--r-md` / `--r-lg` / `--r-xl` | `8px` / `10px` / `14px` / `18px` |
| `--font-ui` | `"Inter", -apple-system, system-ui, sans-serif` |
| `--font-mono` | `"JetBrains Mono", "SF Mono", ui-monospace, monospace` |
| `--pad` / `--gap` | `22px` / `14px` (regular); compact `15/9`; comfy `28/19` |
| `--glow-accent` | `0 4px 16px rgba(74,124,255,.28), inset 0 1px 0 rgba(255,255,255,.18)` |
| `--sh-pop` | `0 28px 70px rgba(0,0,0,.6), 0 8px 22px rgba(0,0,0,.4)` |

**Retired — MUST NOT appear anywhere after this feature**: `#f97316`, `#0d1117`, `#161b22`,
`#30363d`, `#e6edf3`, `#8b949e`, `#38bdf8`, `#4ade80`, `#f87171`, and the single `--radius`.
The drift check greps for these as a regression guard.

### Type ramp (12px floor applied)
The handoff specifies chips at ~11px and body at 12.5–14px. Rescaled so nothing computes below 12:

| Role | Size |
|---|---|
| chip / meta | 12px (was ~11) |
| body small | 13px |
| body | 14px |
| section heading | 15px |
| panel title | 16px |
| H1 (web) | 24–30px |

## Entity: Logo mark

| Property | Value |
|---|---|
| Source | `design/mark.svg`, 128×128 viewBox |
| Composition | bolt glyph, white, on `--grad` rounded square (`.bd-mark` in the handoff) |
| Corner radius | proportional to size — ~23% of edge |
| Raster outputs | `extension/icons/{16,48,128}.png`, transparent outside the rounded square |
| Vector output | `web/public/favicon.svg` |
| Constraint | no text in the mark; must stay legible at 16px (SC-005) |
| Validity test | each PNG's byte size and decoded dimensions are non-trivial — the 428-byte blank is the anti-example |

## Entity: Surface

| Surface | File(s) | Width | Density | Data available |
|---|---|---|---|---|
| Web app | `web/src/**` | fluid, sidebar 232px | regular | full |
| Side panel | `extension/sidepanel.*` | user-resizable | compact | full |
| Launcher popup | `extension/popup.*` | 320px fixed | compact | session + API status only |
| Options | `extension/options.*` | fluid | regular | settings only |

All four consume the same token set. They differ only in width constraint, density, and which data
they have — never in visual language.

## Entity: Brief section state

Each section of the lead brief is in exactly one state:

| State | Meaning | Presentation |
|---|---|---|
| `populated` | backend returned the data | full designed treatment |
| `partial` | fewer items than designed (e.g. <3 follow-ups) | render what exists + explanatory note (existing behavior, preserved) |
| `inert` | backend cannot supply this field at all | designed container, muted, explicitly labelled unavailable, non-interactive |
| `error` | request failed | error treatment using `--red` |

**Inert is a permanent, honest state, not a loading state.** It MUST NOT use a spinner or skeleton
shimmer, both of which imply data is arriving. It MUST be reachable by assistive tech as
unavailable, and MUST NOT display invented values.

Sections that are `inert` under the current contract: buying signal (source/date), contact
confidence, outreach email, CRM field mapping, source count, research-step progress.

Sections that are `populated`: company snapshot, personalized opener, follow-ups.
