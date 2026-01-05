# ical_client.py
import os
from datetime import datetime
from typing import List

import requests
from ics import Calendar
from dotenv import load_dotenv

from calendar_utils import IST

load_dotenv()

ICAL_URL = os.getenv("ICAL_URL")


def list_events_between(start_dt: datetime, end_dt: datetime) -> List[dict]:
    """
    Download iCal from ICAL_URL and return events in a Google‑Calendar‑like format.
    start_dt and end_dt are timezone-aware datetimes (IST).
    """
    if not ICAL_URL:
        return []

    resp = requests.get(ICAL_URL, timeout=10)
    resp.raise_for_status()

    cal = Calendar(resp.text)

    events_json: List[dict] = []
    for ev in cal.events:
        if not ev.begin or not ev.end:
            continue

        begin = ev.begin.to("Asia/Kolkata").datetime
        end = ev.end.to("Asia/Kolkata").datetime

        if begin < start_dt or begin >= end_dt:
            continue

        events_json.append(
            {
                "summary": ev.name or "Event",
                "start": {"dateTime": begin.isoformat()},
                "end": {"dateTime": end.isoformat()},
                "location": ev.location or None,
                "htmlLink": None,
            }
        )

    return events_json
