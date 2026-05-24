from datetime import datetime, timezone


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
