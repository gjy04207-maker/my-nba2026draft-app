from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from apps.api.app import draft_data, runtime_state
from apps.api.app.live_sync import _parse_record_summary


class RuntimeStateStorageTests(unittest.TestCase):
    def test_file_runtime_state_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = os.path.join(temp_dir, "runtime_state.json")
            with patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "",
                    "POSTGRES_URL": "",
                    "RENDER_POSTGRES_URL": "",
                    "DRAFT_RUNTIME_STATE_PATH": state_path,
                },
                clear=False,
            ):
                payload = {
                    "updated_at": "2026-03-26T00:00:00Z",
                    "teams": [],
                    "players": [],
                    "boards": [],
                    "draft_order": [],
                    "order_sources": [],
                    "pick_values": {},
                }
                result = runtime_state.save_runtime_state(payload, source="test_file_round_trip")
                loaded = runtime_state.load_runtime_state()
                self.assertEqual(result["storage_mode"], "file")
                self.assertEqual(loaded["updated_at"], payload["updated_at"])

    def test_draft_data_prefers_runtime_state_when_available(self) -> None:
        repository_payload = draft_data.get_repository_draft_data()
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = os.path.join(temp_dir, "runtime_state.json")
            with patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "",
                    "POSTGRES_URL": "",
                    "RENDER_POSTGRES_URL": "",
                    "DRAFT_RUNTIME_STATE_PATH": state_path,
                },
                clear=False,
            ):
                runtime_payload = {
                    **repository_payload,
                    "updated_at": "2026-03-26T12:00:00Z",
                    "live_context": {"sync_status": "live"},
                }
                runtime_state.save_runtime_state(runtime_payload, source="test_runtime_priority")
                draft_data.reset_cache()
                loaded = draft_data.get_draft_data(force_refresh=True)
                self.assertEqual(loaded["updated_at"], "2026-03-26T12:00:00Z")
                self.assertEqual(loaded["live_context"]["sync_status"], "live")

    def test_draft_data_falls_back_to_repository_when_runtime_load_fails(self) -> None:
        repository_payload = draft_data.get_repository_draft_data()
        with patch("apps.api.app.runtime_state.load_runtime_state", side_effect=RuntimeError("db down")):
            draft_data.reset_cache()
            loaded = draft_data.get_draft_data(force_refresh=True)
        self.assertEqual(loaded["updated_at"], repository_payload["updated_at"])
        self.assertEqual(len(loaded["players"]), len(repository_payload["players"]))

    def test_describe_runtime_state_reports_error_instead_of_raising(self) -> None:
        with patch("apps.api.app.runtime_state.load_runtime_state", side_effect=RuntimeError("db down")):
            summary = runtime_state.describe_runtime_state()
        self.assertEqual(summary["has_persisted_state"], False)
        self.assertEqual(summary["runtime_error"], "db down")


class LiveSyncHelpersTests(unittest.TestCase):
    def test_parse_record_summary(self) -> None:
        wins, losses, win_pct = _parse_record_summary("41-32")
        self.assertEqual(wins, 41)
        self.assertEqual(losses, 32)
        self.assertAlmostEqual(win_pct, 0.562, places=3)


if __name__ == "__main__":
    unittest.main()
