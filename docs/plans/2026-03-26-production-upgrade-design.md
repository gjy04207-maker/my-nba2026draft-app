# 2026-03-26 Production Upgrade Design

## Goal
- Make the mock draft app deployable as a public website.
- Allow runtime data to update without editing the codebase on every change.
- Keep the first production step small: one public frontend, one API, one persistent runtime state.

## Chosen Approach
- Frontend stays on Next.js and is deployed separately.
- API stays on FastAPI and becomes the single source of truth for draft data.
- Runtime data can come from:
  - repository snapshots as fallback
  - persisted live snapshot storage as primary source
- Admin-only sync endpoints refresh runtime data from external sources or uploaded/rebuilt prospect data.

## Runtime Data Model
- Treat the existing `draft_data.json` payload as the canonical runtime envelope.
- Add a `live_context` object for:
  - standings
  - sync timestamps
  - active data source labels
- Store the full runtime envelope in persistent storage so the API can boot from it on every deployment.

## Persistence
- Use PostgreSQL when `DATABASE_URL` is present.
- Fall back to a JSON file path when `DRAFT_RUNTIME_STATE_PATH` is configured.
- Fall back again to repository snapshots when no runtime storage is configured.

## Admin Operations
- Secure admin endpoints with `X-Admin-Token`.
- Support:
  - checking sync status
  - publishing a full runtime payload
  - refreshing standings and roster snapshots

## Deployment
- Frontend: Vercel-friendly env-based config.
- API: Render-friendly `requirements.txt`, `render.yaml`, and env-driven host/CORS/runtime settings.
