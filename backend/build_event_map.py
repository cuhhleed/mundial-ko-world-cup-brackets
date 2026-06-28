"""
One-off script to fetch the KO schedule from ESPN and write the event ID → slot_id
mapping to backend/app/espn/espn_event_map.json.

Run this once (with network access) before deploying so slot assignment is pinned
to real ESPN event IDs and won't desync if FIFA reschedules a match.

Usage:
    cd backend
    poetry run python build_event_map.py

After running, commit the populated espn_event_map.json. The printed summary lets
you verify the corrected feeder table against ESPN's real schedule.
"""

import json
from pathlib import Path

from app.espn.adapter import _runtime_event_map, get_match_schedule

OUTPUT_PATH = Path(__file__).parent / "app" / "espn" / "espn_event_map.json"


def main() -> None:
    print("Fetching KO schedule from ESPN (2026-06-28 → 2026-07-20)...")
    get_match_schedule("20260628", "20260720")

    event_map: dict[str, str] = dict(_runtime_event_map)

    if not event_map:
        print(
            "WARNING: No events were mapped. Check network access and ESPN API availability."
        )
        return

    OUTPUT_PATH.write_text(json.dumps(event_map, indent=2, sort_keys=True) + "\n")
    print(f"Written {len(event_map)} entries to {OUTPUT_PATH}")

    slot_ids = sorted(set(event_map.values()))
    print(f"\nSlot IDs assigned ({len(slot_ids)} unique):")
    for slot_id in slot_ids:
        print(f"  {slot_id}")


if __name__ == "__main__":
    main()
