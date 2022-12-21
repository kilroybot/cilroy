from datetime import datetime, time, timedelta, timezone
from math import ceil
from typing import Iterable

from croniter import croniter


def next_time(base: datetime, interval: timedelta) -> datetime:
    utcbase = base.astimezone(timezone.utc)
    utcnow = datetime.now(timezone.utc)
    return utcbase + interval * ceil((utcnow - utcbase) / interval)


def next_time_from_hours(hours: Iterable[time]) -> datetime:
    now = datetime.now(timezone.utc)
    return min(
        next_time(
            datetime.combine(now.date(), hour, tzinfo=timezone.utc),
            timedelta(days=1),
        )
        for hour in hours
    )


def next_time_from_rule(rule: str) -> datetime:
    now = datetime.now(timezone.utc)
    return croniter(rule, now).get_next(datetime)


def seconds_until(dt: datetime) -> float:
    return (dt - datetime.now(timezone.utc)).total_seconds()


def utcmidnight() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime.combine(now.date(), time(), tzinfo=timezone.utc)
