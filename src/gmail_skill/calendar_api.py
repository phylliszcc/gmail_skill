"""Google Calendar API: list events, create event."""
from datetime import datetime, timedelta, timezone

from .auth import get_calendar_service


def list_events(days_ahead: int = 7, calendar_id: str = "primary") -> list[dict]:
    service = get_calendar_service()

    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        maxResults=50,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    return [
        {
            "id": e["id"],
            "title": e.get("summary", "(no title)"),
            "start": e.get("start", {}).get("dateTime") or e.get("start", {}).get("date"),
            "end": e.get("end", {}).get("dateTime") or e.get("end", {}).get("date"),
            "location": e.get("location", ""),
            "description": e.get("description", ""),
            "attendees": [a.get("email") for a in e.get("attendees", [])],
            "status": e.get("status", ""),
            "link": e.get("htmlLink", ""),
        }
        for e in result.get("items", [])
    ]


def create_event(
    title: str,
    start: str,
    end: str,
    attendees: list[str] | None = None,
    description: str = "",
    location: str = "",
    timezone: str = "Asia/Shanghai",
    calendar_id: str = "primary",
    send_notifications: bool = True,
) -> dict:
    """
    Create a calendar event.
    start / end: ISO 8601, e.g. "2026-05-27T14:00:00+08:00"
    """
    service = get_calendar_service()

    body: dict = {
        "summary": title,
        "start": {"dateTime": start, "timeZone": timezone},
        "end": {"dateTime": end, "timeZone": timezone},
    }
    if description:
        body["description"] = description
    if location:
        body["location"] = location
    if attendees:
        body["attendees"] = [{"email": a} for a in attendees]

    created = service.events().insert(
        calendarId=calendar_id,
        body=body,
        sendNotifications=send_notifications,
    ).execute()

    return {
        "id": created["id"],
        "title": created.get("summary", ""),
        "link": created.get("htmlLink", ""),
        "status": "created",
    }
