__all__ = [
    "parse_timespec",
]

import re
from datetime import datetime, time, timedelta


def parse_delta(delta: str) -> timedelta | None:
    total_sec = 0
    for match in re.finditer(r"(\d+)([smhdwy])", delta, re.I):
        time_sec = int(match[1])
        match match[2]:
            case "m" | "M":
                time_sec *= 60
            case "h" | "H":
                time_sec *= 60 * 60
            case "d" | "D":
                time_sec *= 60 * 60 * 24
            case "w" | "W":
                time_sec *= 60 * 60 * 24 * 7
            case "y" | "Y":
                time_sec *= 60 * 60 * 24 * 365
        total_sec += time_sec
    if total_sec > 0:
        return timedelta(seconds=total_sec)
    return None


def parse_timespec(now: datetime, timespec: str) -> datetime:
    """Parse a time specification and return target datetime.

    The time specification is a string of the form:
    – HH:MM
    – YYYY-MM-DD_HH:MM
    – N[smhdwy]
    – N[smhdwy]N[smhdwy]...
    """
    if (delta := parse_delta(timespec)) is not None:
        return now + delta
    dt = timespec.split("_", maxsplit=1)
    if len(dt) == 2:  # date and time
        date = datetime.strptime(dt[0], "%Y-%m-%d").date()
        time_string = dt[1]
    else:  # only time
        date = now.date()
        time_string = dt[0]
    h, m = map(int, time_string.split(":", maxsplit=1))
    parsed_time = time(h, m)
    if parsed_time < now.time() and len(dt) == 1:
        return datetime.combine(now + timedelta(days=1), parsed_time)
    return datetime.combine(date, parsed_time)
