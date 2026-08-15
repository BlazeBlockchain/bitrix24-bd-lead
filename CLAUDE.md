# CLAUDE.md

Guidance for Claude Code when working in this repository.

<!-- SPECKIT START -->
**Active feature plan**: [specs/008-design-system-pass/plan.md](specs/008-design-system-pass/plan.md)
<!-- SPECKIT END -->

## What this is

**BD Lead AI** — an AI-native B2B business-development assistant. A rep supplies a company, contact,
and buying signal; the backend enriches it with an LLM and returns a preview (company snapshot,
personalized opener, three follow-up tasks), which is then pushed to a CRM (Bitrix24 or HubSpot).

Three surfaces sit on one backend:

| Component | Stack | Location |
|---|---|---|
| Backend | FastAPI + Postgres + Alembic | `backend/` |
| Web app | React 18 + TypeScript + Vite | `web/` |
| Browser extension | Chrome MV3, **vanilla JS, no build** | `extension/` |

## Hard constraints — do not regress these

- **`extension/` is buildless.** MV3, plain vanilla JS/HTML/CSS, loaded unpacked. No npm, no
  bundler, no ES modules, no `node_modules`. Classic scripts declaring globals. Generated assets
  (icons, token CSS) are produced by scripts in `scripts/` and **committed**, never built at load.
- **Never render API, page, or user content via `innerHTML` with interpolation.** `sidepanel.js`
  builds the preview with `createElement`/`textContent` deliberately. Keep it that way.
- **Do not hand-edit `version` in `extension/manifest.json`** or any other component file. It is
  generated from the root `VERSION` by `scripts/sync_versions.py`. Use `make bump-patch`.
- **Do not touch `manifest.json`'s `key`.** It pins the extension ID
  (`kopmahhdddlcipdggmgldkofjpneeboa`), which the Google OAuth redirect URI depends on. Changing it
  breaks sign-in.
- **Do not change the `/api/leads/enrich` or `/api/leads/push` contracts**, or the preview shape:
  `company_snapshot`, `personalized_opener`, `follow_ups[3]{title, description, due_in_days,
  rationale}`. Backend tests and the web app depend on them.
- **No font-size below 12px anywhere.** Extension pages must set an **explicit** `body` font-size:
  Chrome's UA stylesheet shrinks extension-page body to `0.75em`, so inheriting from `:root`
  silently yields 11.25px. This has already been a bug once.
- **The side panel is user-resizable** — it must never scroll horizontally at any width.
- **BD Lead Research skill content stays server-side.** Never embed or ship it to a client.
- **The citation on `buying_signal` may only be set by the server, from retrieval metadata.** The
  model cannot author a source: `_validate_buying_signal` strips `sources`/`source_url`/`finding`
  from model JSON unconditionally. A real link that does not support its claim is worse than no link,
  because it looks like proof — see `specs/010-verifiable-signal-source/`.
- **`search_suggestions` is the ONLY sanctioned `innerHTML` in the codebase**, rendered into a shadow
  root on both surfaces. Google's Search Suggestions must be displayed verbatim wherever grounded
  results are shown, and the terms forbid modifying them — so the fragment is server-*checked* and
  refused outright rather than sanitised, and a refusal drops the whole citation. This is not a
  general relaxation of the no-`innerHTML` rule.

## Open compliance item — needs legal sign-off

`retrieval_service._resolve_publisher_url` resolves Google's grounding redirect to the real publisher
URL. This **knowingly deviates** from the Gemini API terms ("you will not modify … the Grounded
Results"), because the raw `vertexaisearch.cloud.google.com` link hides the destination from the rep
and defeats the point of a citation. Decision recorded in
[specs/010-verifiable-signal-source/plan.md](specs/010-verifiable-signal-source/plan.md). **Do not
change it in either direction without asking the repo owner.** If legal declines, return the redirect
URI unmodified — nothing downstream depends on it being a publisher URL.

## Design

The visual language is defined by the handoff bundle at **`docs/design/`** — `README.md`
is the written spec, `styles.css` is the token source of truth. It is tracked in git as of the
008 design pass — it used to live untracked in the repo root.

`docs/UI_UX.md` is Phase-0 product/UX direction, **not** the visual spec, and it describes the
retired orange theme. Do not use it to pick colors.

The brand accent is the iris→violet→cyan gradient (`#4a7cff` → `#7c5cff` → `#22d3ee`) on near-black
navy (`--bg #05070d`). The legacy orange `#f97316` on `#0d1117` is **retired**.

Design tokens have one tracked upstream, `design/tokens.css`. Never edit the generated token block in
`web/src/index.css` or `extension/tokens.css` — edit the upstream and run `make sync-tokens`.

## Common commands

```bash
# Gates — both must stay green
cd backend && pytest tests/        # 77 passed
cd web && npm run build

make check-tokens                  # design tokens in sync + no retired colors
make sync-tokens                   # regenerate token blocks from design/tokens.css
make build-icons                   # rasterize design/mark.svg → extension/icons/*.png

make bump-patch                    # version bump (never hand-edit versions)
make dev                           # full stack with --build
```

## Operational gotchas that cost real time

- **`docker compose restart` does NOT pick up code changes.** `backend/` and `web/` are baked into
  their images with no bind mount. Use `docker compose up -d --build <service>`.
- **Extension changes need a reload** on the `chrome://extensions` card. Manifest changes always;
  panel/popup/options changes need the surface **closed and reopened**, not just reloaded.
- **Web JWTs last 60 minutes.** If screens look empty, check the session first. An expired token now
  logs the user out rather than rendering as empty data.
- Default dev ports: backend `:8000`, web `:8080`, plus postgres. `extension/config.js` points
  `WEB_BASE` at `http://localhost:8080`.
- Headless Chrome under WSL prints harmless `dbus` errors to stderr. Check the output file, not the
  stderr chatter.

## Spec-driven workflow

Features are planned under `specs/NNN-name/` via the speckit skills (`/speckit-specify`,
`/speckit-plan`, `/speckit-tasks`, `/speckit-implement`). Each feature dir holds `spec.md`,
`plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `tasks.md`.

This speckit install is minimal — `.specify/` contains only `feature.json` (no scripts, templates, or
constitution). Follow the structure established by existing feature dirs.

`.specify/feature.json` points at the active feature directory.

**Skill cost tiering** (`.claude/skills/*/SKILL.md` frontmatter):

| Tier | Skills | `model:` |
|---|---|---|
| Mechanical shell wrappers | the five `speckit-git-*` | `haiku`, tools scoped to `Bash, Read` |
| Template-driven documents | `checklist`, `clarify`, `constitution`, `taskstoissues` | `sonnet` |
| Real design reasoning | `specify`, `plan`, `tasks`, `analyze`, `implement` | inherits the session model |

Skills that write to git, create GitHub issues, or edit code (`git-*`, `taskstoissues`, `implement`,
`constitution`) are `disable-model-invocation: true` — **user-invocable only**, so they never fire on
the model's own initiative. `specify`, `plan` and `tasks` stay model-invocable so a prose request
("plan this with speckit") still works.
