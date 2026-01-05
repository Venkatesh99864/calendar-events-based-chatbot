from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import pytz
from dateutil import parser as date_parser

IST = pytz.timezone("Asia/Kolkata")


@dataclass
class CalendarEvent:
    title: str
    start: datetime
    end: datetime
    location: Optional[str]
    html_link: Optional[str]


def parse_events(raw_events: List[dict]) -> List[CalendarEvent]:
    events: List[CalendarEvent] = []
    for ev in raw_events:
        start = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date")
        end = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date")
        if not start or not end:
            continue
        start_dt = date_parser.parse(start)
        if not start_dt.tzinfo:
            start_dt = IST.localize(start_dt)
        else:
            start_dt = start_dt.astimezone(IST)

        end_dt = date_parser.parse(end)
        if not end_dt.tzinfo:
            end_dt = IST.localize(end_dt)
        else:
            end_dt = end_dt.astimezone(IST)

        events.append(
            CalendarEvent(
                title=ev.get("summary") or "Event",
                start=start_dt,
                end=end_dt,
                location=ev.get("location"),
                html_link=ev.get("htmlLink"),
            )
        )
    return events


def day_range(now: datetime, offset_days: int = 0) -> Tuple[datetime, datetime]:
    base = now.astimezone(IST).replace(hour=0, minute=0, second=0, microsecond=0)
    start = base + timedelta(days=offset_days)
    end = start + timedelta(days=1)
    return start, end


def upcoming_7_days_range(now: datetime) -> Tuple[datetime, datetime]:
    start = now.astimezone(IST)
    end = start + timedelta(days=7)
    return start, end


def filter_events(events: List[CalendarEvent], start: datetime, end: datetime) -> List[CalendarEvent]:
    return [e for e in events if start <= e.start < end]
