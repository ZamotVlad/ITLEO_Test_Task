import datetime
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

WEEKDAY_MAP = {
    0: "MO",
    1: "TU",
    2: "WE",
    3: "TH",
    4: "FR",
    5: "SA",
    6: "SU",
}


def get_google_flow():

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")],
            }
        },
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
    )
    # Явно вимикаємо PKCE
    flow.oauth2session._client.code_challenge_method = None
    return flow


def get_credentials(google_account):
    creds = Credentials(
        token=google_account.access_token,
        refresh_token=google_account.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        google_account.access_token = creds.token
        google_account.save(update_fields=["access_token"])
    return creds


def _get_anchor_date(weekday):
    """Повертає найближчу майбутню дату для заданого дня тижня."""
    today = datetime.date.today()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)


def sync_schedule_to_calendar(schedule_entry):
    """Синхронізує один запис розкладу з Google Calendar."""
    from accounts.models import User

    try:
        owner = User.objects.filter(role="owner").first()
        if not owner:
            return
        google_account = owner.google_account
        if not google_account.is_connected:
            return
    except Exception:
        return

    creds = get_credentials(google_account)
    service = build("calendar", "v3", credentials=creds)

    weekday_str = WEEKDAY_MAP.get(schedule_entry.weekday, "MO")
    anchor_date = _get_anchor_date(schedule_entry.weekday)

    start_dt = datetime.datetime.combine(anchor_date, schedule_entry.start_time)
    end_dt = datetime.datetime.combine(anchor_date, schedule_entry.end_time)

    # Attendees — студенти + викладач
    attendees = [{"email": s.email} for s in schedule_entry.group.students.filter(email__gt="")]
    if schedule_entry.group.teacher and schedule_entry.group.teacher.email:
        attendees.append({"email": schedule_entry.group.teacher.email})

    event = {
        "summary": f"{schedule_entry.group.name} — заняття",
        "description": (
            f"Викладач: "
            f"{schedule_entry.group.teacher.get_full_name() if schedule_entry.group.teacher else '—'}"
        ),
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": "Europe/Kyiv",
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": "Europe/Kyiv",
        },
        "recurrence": [f"RRULE:FREQ=WEEKLY;BYDAY={weekday_str}"],
        "attendees": attendees,
        "guestsCanSeeOtherGuests": False,
        "conferenceData": {
            "createRequest": {
                "requestId": f"academy-group-{schedule_entry.group.id}-{schedule_entry.weekday}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    if schedule_entry.google_event_id:
        try:
            service.events().update(
                calendarId="primary",
                eventId=schedule_entry.google_event_id,
                body=event,
                conferenceDataVersion=1,
            ).execute()
        except Exception:
            schedule_entry.google_event_id = ""
            schedule_entry.save(update_fields=["google_event_id"])

    if not schedule_entry.google_event_id:
        created = (
            service.events()
            .insert(
                calendarId="primary",
                body=event,
                conferenceDataVersion=1,
            )
            .execute()
        )
        schedule_entry.google_event_id = created["id"]
        schedule_entry.save(update_fields=["google_event_id"])


def sync_group_to_calendar(group):
    """Синхронізує весь розклад групи."""
    entries = group.schedule_entries.prefetch_related(
        "group__students",
        "group__teacher",
    ).all()
    for entry in entries:
        sync_schedule_to_calendar(entry)
