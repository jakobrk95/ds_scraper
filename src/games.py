import json
from typing import Dict, Any

import requests

from .config import DANSKE_SPIL_BASE, DEFAULT_HEADERS, GAMES_DIR


def fetch_game_raw(event_id: int) -> dict:
    """Fetch details for a single event and save raw JSON."""
    url = f"{DANSKE_SPIL_BASE}/q/events-by-ids"

    params = {
        "eventIds": event_id,
        "includeChildMarkets": "true",
        "includeCollections": "true",
        "includePriorityCollectionChildMarkets": "true",
        "includePriceHistory": "false",
        "includeCommentary": "true",
        "includeIncidents": "true",
        "includeRace": "false",
        "includeMedia": "true",
        "includePools": "true",
        "includeNonFixedOdds": "false",
        "lang": "da-DK",
        "channel": "I",
    }

    print(f"[GAME] Requesting game details for event_id={event_id}")
    resp = requests.get(url, headers=DEFAULT_HEADERS, params=params, timeout=10)
    resp.raise_for_status()

    data = resp.json()

    out_path = GAMES_DIR / f"game_{event_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[GAME] Saved raw game → {out_path}")
    return data


def parse_game_markets(game_data: dict) -> Dict[str, Any]:
    """Parse MATCH_RESULT and TOTAL_GOALS_OVER/UNDER (2.5)."""
    events = game_data["data"]["events"]
    if not events:
        return {}

    markets = events[0]["markets"]

    match_result = []
    over_under_2_5 = []

    for market in markets:
        group_code = market.get("groupCode")
        handicap = market.get("handicapValue")

        if group_code == "MATCH_RESULT":
            for outcome in market["outcomes"]:
                team = outcome["name"]
                price = outcome["prices"][0]["decimal"]
                match_result.append({"team": team, "price": price})

        elif group_code == "TOTAL_GOALS_OVER/UNDER" and handicap == 2.5:
            for outcome in market["outcomes"]:
                name = outcome["name"]
                price = outcome["prices"][0]["decimal"]
                over_under_2_5.append({"outcome": name, "price": price})

    return {
        "match_result": match_result,
        "over_under_2_5": over_under_2_5,
    }