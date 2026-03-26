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
    parser = argparse.ArgumentParser(description="Publish draft runtime data to persistent storage.")
    parser.add_argument(
        "--input",
        default=str(ROOT / "data" / "draft" / "draft_data.json"),
        help="Path to the draft runtime JSON payload.",
    )
    parser.add_argument("--source", default="publish_runtime_state", help="Source label written to runtime storage.")
    parser.add_argument("--refresh-live", action="store_true", help="Refresh rosters and team records before publishing.")
    parser.add_argument("--skip-rosters", action="store_true", help="Skip roster refresh when --refresh-live is enabled.")
    parser.add_argument("--skip-records", action="store_true", help="Skip team record refresh when --refresh-live is enabled.")
    args = parser.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Draft payload not found: {input_path}")

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if args.refresh_live:
        payload = live_sync.refresh_runtime_data(
            payload,
            refresh_rosters=not args.skip_rosters,
            refresh_records=not args.skip_records,
        )

    result = runtime_state.save_runtime_state(payload, source=args.source)
    draft_data.reset_cache()
    print(
        json.dumps(
            {
                "ok": True,
                "updated_at": payload.get("updated_at"),
                "storage_mode": result.get("storage_mode"),
                "teams_count": len(payload.get("teams", [])),
                "players_count": len(payload.get("players", [])),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
