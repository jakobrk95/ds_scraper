# src/main.py
from __future__ import annotations

import time
from datetime import datetime, timezone

from .events import fetch_events_raw, extract_events_basic
from .games import fetch_game_raw, parse_game_markets
from .config import BASE_DIR, LEAD_TIME_MINUTES
from .db import init_db, save_odds


def parse_iso_utc(ts: str) -> datetime:
    """
    Parse ISO 8601 timestamp with 'Z' as UTC, e.g. 2025-11-30T23:00:00Z
    into a timezone-aware datetime in UTC.
    """
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def main():
    print(f"[MAIN] Starting scraper with LEAD_TIME_MINUTES={LEAD_TIME_MINUTES}")

    # Initialize DB (creates tables if not exist)
    init_db()

    # 1) Get all events in the configured date range
    raw_events = fetch_events_raw()

    # 2) Extract ids and teams
    events = extract_events_basic(raw_events)

    now = datetime.now(timezone.utc)
    print(f"[MAIN] Current UTC time: {now.isoformat()}")

    # Optional: still write to text file if you like
    out_path = BASE_DIR / "data" / "games" / "games_parsed.txt"
    processed_count = 0

    with out_path.open("w", encoding="utf-8") as out:
        for i, event in enumerate(events, start=1):
            event_id = event["event_id"]
            home = event["home_team"]
            away = event["away_team"]
            start_time_str = event["start_time"]

            start_dt = parse_iso_utc(start_time_str)
            minutes_to_kickoff = (start_dt - now).total_seconds() / 60.0

            print(
                f"[MAIN] ({i}/{len(events)}) {event_id}: "
                f"{home} vs {away} | start={start_dt.isoformat()} | "
                f"Δt={minutes_to_kickoff:.1f} min"
            )

            # Only scrape if game is within the window
            if 0 <= minutes_to_kickoff <= LEAD_TIME_MINUTES:
                print(f"[MAIN] → Scraping odds for event {event_id}")

                # Fetch & parse
                game_data = fetch_game_raw(event_id)
                parsed = parse_game_markets(game_data)

                # Save to DB
                save_odds(event, parsed)

                # Optional: still log to text file
                out.write(f"Event {event_id}: {home} vs {away}\n")

                if parsed.get("match_result"):
                    out.write("  MATCH_RESULT:\n")
                    for mr in parsed["match_result"]:
                        out.write(f"    {mr['team']}: {mr['price']}\n")

                if parsed.get("over_under_2_5"):
                    out.write("  TOTAL_GOALS_OVER/UNDER (2.5):\n")
                    for ou in parsed["over_under_2_5"]:
                        out.write(f"    {ou['outcome']}: {ou['price']}\n")

                out.write("\n")
                processed_count += 1

                time.sleep(5)
            else:
                print(
                    f"[MAIN] Skipping event {event_id} "
                    f"(minutes_to_kickoff={minutes_to_kickoff:.1f})"
                )

    print(
        f"[MAIN] Done. Scraped {processed_count} events within "
        f"{LEAD_TIME_MINUTES} minutes of kickoff."
    )
    print(f"[MAIN] Output → {out_path}")


if __name__ == "__main__":
    main()
