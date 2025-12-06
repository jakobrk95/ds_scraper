import json
from typing import List, Dict

import requests

from .config import (
    DANSKE_SPIL_BASE,
    DEFAULT_HEADERS,
    START_TIME_FROM,
    START_TIME_TO,
    EVENTS_DIR,
)


def fetch_events_raw() -> dict:
    """Fetch list of events and save raw JSON."""
    if not START_TIME_FROM or not START_TIME_TO:
        raise RuntimeError("START_TIME_FROM and START_TIME_TO must be set in .env")

    url = f"{DANSKE_SPIL_BASE}/q/event-list"

    params = {
        "startTimeFrom": START_TIME_FROM,
        "startTimeTo": START_TIME_TO,
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

    print(f"[EVENTS] Requesting event list")
    resp = requests.get(url, headers=DEFAULT_HEADERS, params=params, timeout=10)
    resp.raise_for_status()

    data = resp.json()

    out_path = EVENTS_DIR / "events_raw.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[EVENTS] Saved raw events → {out_path}")
    return data


def extract_events_basic(data: dict) -> List[Dict]:
    """Extract event_id, start_time, home_team, away_team."""
    events = data["data"]["events"]
    result = []

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