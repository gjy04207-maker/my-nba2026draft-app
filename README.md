# 2026 Mock Draft Simulator

## What This Version Adds
- Public deployment path for the frontend and API
- Persistent runtime state for the live draft dataset
- Admin-only runtime publish and sync endpoints
- Cron-friendly sync script for live team rosters and team records

## Recommended Production Stack
- Frontend: Vercel, root directory `apps/web`
- API: Render, using `render.yaml`
- Runtime storage: PostgreSQL via `DATABASE_URL`

## Local Run
API:

```bash
cd "/Users/gaojunyao/Documents/my-successful-nba-mockdraft-app"
apps/api/.venv/bin/python -m uvicorn apps.api.app.main:app --reload --host 127.0.0.1 --port 8000
```

Web:

```bash
cd "/Users/gaojunyao/Documents/my-successful-nba-mockdraft-app/apps/web"
npm run dev
```

## Runtime Storage
The API loads runtime data in this order:

1. PostgreSQL row from `DATABASE_URL`
2. JSON file from `DRAFT_RUNTIME_STATE_PATH`
3. Repository snapshot in `data/draft/draft_data.json`

If you do not configure runtime storage, the site still works, but live updates are not persisted across redeploys.

## Admin Endpoints
All admin endpoints require the `X-Admin-Token` header and a configured `ADMIN_TOKEN`.

- `GET /api/admin/runtime/status`
- `POST /api/admin/runtime/publish`
- `POST /api/admin/runtime/sync`

Public runtime visibility:

- `GET /api/draft/runtime-status`

## Publish Current Draft Payload
Use this after you rebuild the workbook dataset locally:

```bash
cd "/Users/gaojunyao/Documents/my-successful-nba-mockdraft-app"
python3 scripts/publish_runtime_state.py --source manual_publish
```

## Sync Live Team Data
This refreshes team rosters and current record summaries from ESPN and writes them into runtime storage:

```bash
cd "/Users/gaojunyao/Documents/my-successful-nba-mockdraft-app"
python3 scripts/sync_live_runtime.py
```

## Deployment Notes
- On Vercel, set `BACKEND_ORIGIN` to your public API URL.
- On Render, set `CORS_ALLOW_ORIGINS` to your Vercel site URL.
- For persistent updates, prefer `DATABASE_URL` over `DRAFT_RUNTIME_STATE_PATH`.
