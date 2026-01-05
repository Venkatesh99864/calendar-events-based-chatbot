from __future__ import annotations

from datetime import datetime
from typing import List

import os.path
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

# Read-only scope is enough for listing events.[web:77]
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")


def get_credentials() -> Credentials:
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def list_events_between(start_iso: str, end_iso: str) -> List[dict]:
    """
    Returns raw Google Calendar events for the configured calendarId
    between start_iso and end_iso (ISO 8601 strings, UTC or with tz).[web:95]
    """
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    events_result = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=start_iso,
            timeMax=end_iso,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])
