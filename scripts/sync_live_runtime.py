from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app import draft_data, live_sync, runtime_state


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Refresh live team data and persist it as runtime state.")
    parser.add_argument("--source", default="sync_live_runtime", help="Source label written to runtime storage.")
    parser.add_argument("--skip-rosters", action="store_true", help="Skip roster refresh.")
    parser.add_argument("--skip-records", action="store_true", help="Skip team record refresh.")
    args = parser.parse_args(argv)

    base_payload = runtime_state.load_runtime_state() or draft_data.get_repository_draft_data()
    synced = live_sync.refresh_runtime_data(
        base_payload,
        refresh_rosters=not args.skip_rosters,
        refresh_records=not args.skip_records,
    )
    result = runtime_state.save_runtime_state(synced, source=args.source)
    draft_data.reset_cache()
    print(
        json.dumps(
            {
                "ok": True,
                "updated_at": synced.get("updated_at"),
                "storage_mode": result.get("storage_mode"),
                "sync_status": synced.get("live_context", {}).get("sync_status"),
                "errors": synced.get("live_context", {}).get("errors", []),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
