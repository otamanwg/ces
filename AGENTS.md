# City Economic Simulator Agent Rules

Canonical project root: `C:\ces`.

If the environment reports another workspace/cwd, treat it as stale unless `C:\ces` is unavailable. Before inspecting or editing the project, switch to `C:\ces` and verify that this directory exists.

## Source Of Truth

1. Read `TOOLS.md`.
2. Read `ROADMAP.md`.
3. Inspect `git status` before editing.
4. Treat `ROADMAP.md` as the only active execution queue.

## Delivery Rules

- One slice has one purpose and one focused commit.
- Preserve unrelated user or agent changes in a dirty worktree.
- Backend contract and regression tests come before client wiring.
- PostgreSQL and Alembic are mandatory; never use SQLite or `create_all` as a migration fallback.
- Do not open a new gameplay system while the stabilization gate is incomplete.

## Definition Of Done

- Default verification loop: run the smallest relevant targeted gate first.
- Use `scripts/check_targeted.ps1 <profile>` or `just check-...` after each focused backend/client slice.
- Do not fall back to running only the full gate for routine iteration; targeted profiles are the normal development workflow.
- `scripts/check.ps1` passes before closing a slice, after integrating several targeted changes, or before handing off a verified milestone.
- Backend API changes pass `scripts/smoke_mvp.py`.
- Client C# or scene changes pass Godot MCP diagnostics.
- Do not report "Godot/client is clean" unless the editor is connected, the game scene is launched, `is_playing=true`, `get_errors` is clean, and the console log has no relevant runtime/.NET errors.
- Visual changes have capture QA.
- `ROADMAP.md` reflects the verified state.
- `git status` contains no accidental artifacts or secrets.

## Parallel Work

- Prefer one Git worktree per agent.
- Do not edit the same roadmap item or ownership hotspot concurrently.
- Never run PostgreSQL test suites in parallel: fixtures reset and migrate one shared schema.
- High-collision files: `ROADMAP.md`, `backend/app/models.py`, Alembic migrations, and `CityDashboardController*.cs`.
