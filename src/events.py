# src/events.py
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict

import requests

from .config import (
    DANSKE_SPIL_BASE,
    DEFAULT_HEADERS,
    START_TIME_FROM,
    START_TIME_TO,
    EVENTS_DIR,
)


def _get_event_date_range() -> tuple[str, str]:
    """
    Decide which date range to use for the event list API.

    Priority:
      1) If START_TIME_FROM and START_TIME_TO are set in .env, use those.
      2) Otherwise, use a dynamic range: now -> now + 365 days.

    Returns ISO 8601 strings with trailing 'Z', e.g. "2025-12-06T16:30:00Z".
    """
    # If user explicitly set values in .env, respect that
    if START_TIME_FROM and START_TIME_TO:
        print(
            f"[EVENTS] Using date range from .env: "
            f"{START_TIME_FROM} -> {START_TIME_TO}"
        )
        return START_TIME_FROM, START_TIME_TO

    # Otherwise, use a rolling window: now to 1 year ahead
    now = datetime.now(timezone.utc)
    start_dt = now
    end_dt = now + timedelta(days=365)

    start_str = start_dt.isoformat().replace("+00:00", "Z")
    end_str = end_dt.isoformat().replace("+00:00", "Z")

    print(
        "[EVENTS] Using dynamic date range: "
        f"{start_str} -> {end_str} (now -> now + 365 days)"
    )
    return start_str, end_str


def fetch_events_raw() -> dict:
    """
    Call the event-list endpoint and return the parsed JSON.
    Also writes raw JSON to data/events/events_raw.json
    """
    start_time_from, start_time_to = _get_event_date_range()

    url = f"{DANSKE_SPIL_BASE}/q/event-list"

    params = {
        "startTimeFrom": start_time_from,
        "startTimeTo": start_time_to,
        "maxEvents": 64,
        "orderEventsBy": "startTime",
        "maxMarkets": 10,
        "orderMarketsBy": "displayOrder",
        "excludeEventsWithNoMarkets": "false",
        "eventSortsIncluded": "MTCH",
        "includeChildMarkets": "true",
        "prioritisePrimaryMarkets": "true",
        "includeCommentary": "true",
        "includeMedia": "true",
        "drilldownTagIds": "23746",
        "excludeDrilldownTagIds": "20769,22796,22797",
        "useMarketGroupCodeCombis": "true",
        "marketGroupCodeCombiId": 1,
        "lang": "da-DK",
        "channel": "I",
    }

    print(f"[EVENTS] Requesting event list: {url}")
    resp = requests.get(url, headers=DEFAULT_HEADERS, params=params, timeout=10)
    resp.raise_for_status()

    data = resp.json()

    out_path = EVENTS_DIR / "events_raw.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[EVENTS] Saved raw events → {out_path}")
    return data


def extract_events_basic(data: dict) -> List[Dict]:
    """
    Take raw JSON from fetch_events_raw and extract:
    - event_id
    - start_time
    - home_team
    - away_team
    """
    events = data["data"]["events"]
    result: List[Dict] = []

    for event in events:
        event_id = event["id"]
        start_time = event["startTime"]

        home_team = None
        away_team = None

        for team in event.get("teams", []):
            if team.get("side") == "HOME":
                home_team = team.get("name")
            elif team.get("side") == "AWAY":
                away_team = team.get("name")

        result.append(
            {
                "event_id": event_id,
                "start_time": start_time,
                "home_team": home_team,
                "away_team": away_team,
            }
        )

    txt_path = EVENTS_DIR / "events.txt"
    with txt_path.open("w", encoding="utf-8") as f:
        for r in result:
            f.write(
                f"Event ID: {r['event_id']}, "
                f"Start: {r['start_time']}, "
                f"Home: {r['home_team']}, "
                f"Away: {r['away_team']}\n"
            )

    print(f"[EVENTS] Extracted {len(result)} events → {txt_path}")
    return result
