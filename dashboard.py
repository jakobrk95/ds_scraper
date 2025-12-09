import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / "data" / "odds.sqlite3"


@st.cache_resource
def get_connection() -> sqlite3.Connection:
    """Create and cache a SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    return conn


@st.cache_data
def load_events() -> pd.DataFrame:
    """Load all events into a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT event_id, start_time, home_team, away_team
        FROM events
        ORDER BY start_time ASC
        """,
        conn,
    )
    return df


@st.cache_data
def load_odds_for_event(event_id: int) -> pd.DataFrame:
    """Load odds for a given event_id into a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT market_type, selection, price, scraped_at
        FROM odds
        WHERE event_id = ?
        ORDER BY market_type, selection
        """,
        conn,
        params=(event_id,),
    )
    return df


def main():
    st.title("Danske Spil Odds Dashboard 📊")

    if not DB_PATH.exists():
        st.error(f"Database not found at {DB_PATH}. "
                 f"Did you copy odds.sqlite3 from the server to ./data?")
        return

    events_df = load_events()

    if events_df.empty:
        st.warning("No events found in the database yet.")
        return

    # Sidebar filters
    st.sidebar.header("Filters")

    # Convert start_time to date for filtering
    events_df["start_date"] = pd.to_datetime(events_df["start_time"]).dt.date
    unique_dates = sorted(events_df["start_date"].unique())

    selected_date = st.sidebar.selectbox("Select date", unique_dates)

    filtered_events = events_df[events_df["start_date"] == selected_date]

    if filtered_events.empty:
        st.warning("No events for the selected date.")
        return

    event_label_map = {
        row["event_id"]: f"{row['home_team']} vs {row['away_team']} (id={row['event_id']})"
        for _, row in filtered_events.iterrows()
    }

    selected_event_id = st.sidebar.selectbox(
        "Select match",
        list(event_label_map.keys()),
        format_func=lambda eid: event_label_map[eid],
    )

    st.subheader("Event info")
    st.write(
        events_df[events_df["event_id"] == selected_event_id][
            ["event_id", "start_time", "home_team", "away_team"]
        ]
    )

    # Load odds for this event
    odds_df = load_odds_for_event(int(selected_event_id))

    if odds_df.empty:
        st.warning("No odds found for this event.")
        return

    st.subheader("Odds table")
    st.dataframe(odds_df)

    # Simple bar charts per market
    for market in odds_df["market_type"].unique():
        st.markdown(f"### {market}")
        market_df = odds_df[odds_df["market_type"] == market]

        st.bar_chart(
            market_df.set_index("selection")["price"],
        )


if __name__ == "__main__":
    main()
