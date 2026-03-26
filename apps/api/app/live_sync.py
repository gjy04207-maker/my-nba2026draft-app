from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, urlopen

TEAM_CATALOG_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
TEAM_ROSTER_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster"
TEAM_SCHEDULE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _hex_color(value: str | None) -> str | None:
    if not value:
        return None
    return value if value.startswith("#") else f"#{value}"


def _pick_logo(team_payload: dict[str, Any]) -> str | None:
    for logo in team_payload.get("logos", []):
        rel = set(logo.get("rel", []))
        if "default" in rel:
            return logo.get("href")
    logos = team_payload.get("logos", [])
    return logos[0].get("href") if logos else None


def _normalize_roster_player(athlete: dict[str, Any]) -> dict[str, Any]:
    position = athlete.get("position") or {}
    return {
        "id": f"nba-{athlete.get('id')}",
        "source_id": str(athlete.get("id", "")),
        "asset_type": "roster_player",
        "name": athlete.get("displayName") or athlete.get("fullName") or "",
        "short_name": athlete.get("shortName"),
        "position": position.get("abbreviation", ""),
        "position_label": position.get("displayName"),
        "age": athlete.get("age"),
        "height": athlete.get("displayHeight"),
        "weight_lbs": athlete.get("weight"),
        "jersey": athlete.get("jersey"),
    }


def _parse_record_summary(record_summary: str | None) -> tuple[int | None, int | None, float | None]:
    if not record_summary or "-" not in record_summary:
        return None, None, None
    try:
        wins_raw, losses_raw = record_summary.split("-", 1)
        wins = int(wins_raw)
        losses = int(losses_raw)
    except ValueError:
        return None, None, None
    games = wins + losses
    win_pct = round(wins / games, 3) if games else None
    return wins, losses, win_pct


def _build_catalog_by_abbr() -> dict[str, dict[str, Any]]:
    payload = _fetch_json(TEAM_CATALOG_URL)
    teams = payload.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
    catalog: dict[str, dict[str, Any]] = {}
    for wrapped in teams:
        team = wrapped.get("team", {})
        abbr = str(team.get("abbreviation", "")).upper()
        if abbr:
            catalog[abbr] = team
    return catalog


def _refresh_team(
    team: dict[str, Any],
    catalog_team: dict[str, Any] | None,
    synced_at: str,
    *,
    refresh_rosters: bool,
    refresh_records: bool,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    espn_id = str(team.get("espn_id") or catalog_team.get("id") if catalog_team else "")
    if not espn_id:
        return team, None

    roster_payload = _fetch_json(TEAM_ROSTER_URL.format(team_id=espn_id)) if refresh_rosters else {}
    schedule_payload = _fetch_json(TEAM_SCHEDULE_URL.format(team_id=espn_id)) if refresh_records else {}

    detail = catalog_team or schedule_payload.get("team") or {}
    schedule_team = schedule_payload.get("team", {})
    roster_players = team.get("roster_players", [])
    if refresh_rosters:
        roster_players = sorted(
            (_normalize_roster_player(athlete) for athlete in roster_payload.get("athletes", [])),
            key=lambda item: (item.get("position") or "Z", item.get("name") or ""),
        )

    record_summary = schedule_team.get("recordSummary")
    wins, losses, win_pct = _parse_record_summary(record_summary)

    updated_team = {
        **team,
        "espn_id": espn_id,
        "name_en": detail.get("displayName") or team.get("name_en"),
        "city": detail.get("location") or team.get("city"),
        "nickname": detail.get("name") or team.get("nickname"),
        "slug": detail.get("slug") or team.get("slug"),
        "primary_color": _hex_color(detail.get("color")) or team.get("primary_color"),
        "secondary_color": _hex_color(detail.get("alternateColor")) or team.get("secondary_color"),
        "logo_url": _pick_logo(detail) or team.get("logo_url"),
        "roster_players": roster_players,
        "record_summary": record_summary,
        "standing_summary": schedule_team.get("standingSummary"),
        "season_summary": schedule_team.get("seasonSummary"),
        "last_synced_at": synced_at,
    }
    standing = {
        "team_id": team.get("id"),
        "team_name": team.get("name"),
        "team_abbr": team.get("abbr"),
        "record": record_summary,
        "wins": wins,
        "losses": losses,
        "win_pct": win_pct,
        "standing_summary": schedule_team.get("standingSummary"),
        "season_summary": schedule_team.get("seasonSummary"),
        "synced_at": synced_at,
        "source": "ESPN team schedule",
    }
    return updated_team, standing


def refresh_runtime_data(
    base_data: dict[str, Any],
    *,
    refresh_rosters: bool = True,
    refresh_records: bool = True,
) -> dict[str, Any]:
    synced_at = _iso_now()
    if not refresh_rosters and not refresh_records:
        return base_data

    catalog = _build_catalog_by_abbr()
    updated_teams: list[dict[str, Any]] = []
    standings: list[dict[str, Any]] = []
    failures: list[str] = []

    for team in base_data.get("teams", []):
        catalog_team = catalog.get(str(team.get("abbr", "")).upper())
        try:
            refreshed_team = dict(team)
            standing = None
            if refresh_rosters or refresh_records:
                refreshed_team, standing = _refresh_team(
                    team,
                    catalog_team,
                    synced_at,
                    refresh_rosters=refresh_rosters,
                    refresh_records=refresh_records,
                )
        except Exception as exc:  # pragma: no cover - defensive for live network calls
            refreshed_team = dict(team)
            standing = None
            failures.append(f"{team.get('abbr')}: {exc}")

        updated_teams.append(refreshed_team)
        if standing and refresh_records:
            standings.append(standing)

    standings.sort(
        key=lambda entry: (
            -(entry.get("win_pct") or 0.0),
            -(entry.get("wins") or 0),
            entry.get("team_name") or "",
        )
    )

    live_context = dict(base_data.get("live_context", {}))
    live_context["sync_status"] = "partial" if failures else "live"
    live_context["last_synced_at"] = synced_at
    live_context["standings"] = standings if refresh_records else live_context.get("standings", [])
    live_context["sources"] = [
        {
            "id": "espn_team_catalog",
            "label": "ESPN Team Catalog",
            "updated_at": synced_at,
            "status": "live",
        },
        {
            "id": "espn_team_rosters",
            "label": "ESPN Team Rosters",
            "updated_at": synced_at,
            "status": "live" if refresh_rosters else "skipped",
        },
        {
            "id": "espn_team_records",
            "label": "ESPN Team Schedule Record Summary",
            "updated_at": synced_at,
            "status": "live" if refresh_records else "skipped",
        },
    ]
    if failures:
        live_context["errors"] = failures
    else:
        live_context.pop("errors", None)

    return {
        **base_data,
        "updated_at": synced_at,
        "teams": updated_teams,
        "live_context": live_context,
    }
