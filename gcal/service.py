from googleapiclient.discovery import build
from .auth import get_credentials

_service = None


def get_calendar_service():
    global _service
    if _service is None:
        creds = get_credentials()
        _service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return _service