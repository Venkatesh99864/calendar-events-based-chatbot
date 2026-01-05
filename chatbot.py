# chatbot.py

import os
from datetime import datetime
from typing import Dict, Any, List

from dotenv import load_dotenv
from groq import Groq  # Groq SDK

from calendar_utils import (
    parse_events,
    day_range,
    upcoming_7_days_range,
    filter_events,
    IST,
)
from ical_client import list_events_between

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"  # chat-capable Groq model

MENU_TEXT = (
    "\nPlease choose one of the following options:\n"
    "\n"
    "1.View today's schedule\n"
    "2.View upcoming events (next 7 days)\n"
    "3.Request an appointment\n"
    "4.Know location of the next public meeting\n"
    "5.Contact office team"
)


def groq_chat(system_prompt: str, user_prompt: str) -> str:
    """Call Groq chat completion with system + user prompts."""
    chat_completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return chat_completion.choices[0].message.content.strip()


def fetch_all_events_context(now: datetime) -> str:
    """
    Load events for today and the next 7 days from the iCal feed
    and return them as plain-text context for Groq.
    """
    start_today, end_today = day_range(now, 0)
    start_up, end_up = upcoming_7_days_range(now)

    raw_today = list_events_between(start_today, end_today)
    raw_upcoming = list_events_between(start_up, end_up)

    events_today = parse_events(raw_today)
    events_upcoming = parse_events(raw_upcoming)

    def fmt(ev_list: List):
        lines = []
        for e in ev_list:
            date_str = e.start.strftime("%Y-%m-%d")
            time_str = f"{e.start.strftime('%H:%M')}–{e.end.strftime('%H:%M')}"
            loc = e.location or "Location not specified"
            lines.append(f"{date_str} | {time_str} | {e.title} | {loc}")
        return "\n".join(lines) if lines else "None"

    return (
        f"TODAY_EVENTS:\n{fmt(events_today)}\n\n"
        f"UPCOMING_7_DAYS_EVENTS:\n{fmt(events_upcoming)}"
    )


def handle_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entrypoint called from app.py.

    payload:
      - message: str  (user text)
      - conversation_state: dict (ignored here, kept for future extensions)
    """
    raw_text: str = (payload.get("message", "") or "").strip()

    # Map simple menu numbers to natural language so Groq understands.
    if raw_text == "1":
        user_text = "Show me today's schedule."
    elif raw_text == "2":
        user_text = "Show me upcoming events for the next 7 days."
    elif raw_text == "3":
        # Explicit appointment option so system_prompt rule can trigger
        user_text = "Appointment option selected."
    elif raw_text == "4":
        user_text = "Tell me the location of the next public meeting."
    elif raw_text == "5":
        user_text = "Contact office team."
    else:
        user_text = raw_text

    now = datetime.now(tz=IST)

    # Build events context (today + upcoming 7 days)
    events_context = fetch_all_events_context(now)

    system_prompt = (
        "You are Madhav's schedule assistant chatbot for citizens.\n"
        "You receive:\n"
        "1) A list of today's events and upcoming 7‑day events in this format:\n"
        "   YYYY-MM-DD | HH:MM–HH:MM | Title | Location\n"
        "2) A user message.\n\n"
        "OUTPUT RULES (IMPORTANT):\n"
        "- When the user asks for today's schedule (or sends '1', 'today's schedule', "
        "  'may I know today's all events', etc.):\n"
        "  * DO NOT repeat the greeting or the menu again.\n"
        "  * Answer in this exact style (including spaces, line breaks and numbering):\n"
        "    'Here’s Madhav's schedule for today, <Month name> <day>, <year>:\n"
        "\n"
        "    1. Event Name: <title>\n"
        "       Date: DD-01-YYYY\n"
        "       Time: hh:mm AM - hh:mm PM\n"
        "       Location: <location or \"Location not specified\">\n"
        "\n"
        "    2. Event Name: <title of second event>\n"
        "       Date: DD-01-YYYY\n"
        "       Time: ...\n"
        "       Location: ...\n"
        "\n"
        "    (continue numbering 3., 4., etc. for more events)\n"
        "\n"
        "    If you need more details or assistance with anything else, feel free to ask!'\n"
        "  * Important: Put a blank line between each event block and indent "
        "    the Date/Time/Location lines with 3 spaces so it looks like:\n"
        "    '1. Event Name: Meeting\\n"
        "       Date: 03-01-2026\\n"
        "       Time: 10:00 AM - 10:00 AM\\n"
        "       Location: Srikakulam, Andhra Pradesh, India'\n"
        "- For tomorrow questions, use the same numbered format but start with:\n"
        "  'Here are the events for tomorrow, <Month name> <day>, <year>:'\n"
        "- For specific place/time questions (e.g. 'srikakulam meeting time today'):\n"
        "  * Do NOT show all events.\n"
        "  * Only output one block like:\n"
        "    'The meeting in <place> today is scheduled as follows:\n"
        "     Event Name: ...\n"
        "     Date: DD-MM-YYYY\n"
        "     Time: ...\n"
        "     Location: ...'\n"
        "- APPOINTMENT OPTION (user chooses option 3 or says they want an appointment):\n"
        "  * If the message mentions 'Appointment option selected' or clearly asks to "
        "    request an appointment, reply exactly with:\n"
        "    'For appointment,\n please contact this number: 9182565685.'\n"
        "    Do not show the menu again in the same message.\n"
        "- For option '5' or messages like '5', 'contact office team', 'office team contact':\n"
        "  * Reply exactly:\n"
        "    'Office team contact number: 9182565685.\n"
        "     Is there anything else I can assist you with?'\n"
        "- Only when the user greets you (hi / hello / namasthe) or sends unclear text "
        "  like 'kk', 'ok', then you should show the greeting + menu in this wording:\n"
        "    'Namasthe 👋\n"
        "     I am Madhav's assistant. How can I help you?\n"
        f"     {MENU_TEXT}'\n"
        "- Never invent new events. Use only the events from EVENTS_DATA.\n"
        "- Keep answers short and never repeat the greeting+menu before every schedule answer.\n"
    )

    user_prompt = (
        f"CURRENT_DATE_IST: {now.strftime('%Y-%m-%d')}\n\n"
        f"EVENTS_DATA:\n{events_context}\n\n"
        f"USER_QUESTION:\n{user_text}"
    )

    reply = groq_chat(system_prompt, user_prompt)
    return {"reply": reply, "state": {}}
