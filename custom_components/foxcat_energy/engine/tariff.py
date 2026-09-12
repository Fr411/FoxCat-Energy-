from __future__ import annotations

from datetime import datetime


def minute_of_day(now: datetime) -> float:
    return now.hour * 60 + now.minute + now.second / 60


def is_peak(now: datetime) -> bool:
    m = minute_of_day(now)
    return (420 <= m < 660) or (1020 <= m < 1320)


def is_offpeak(now: datetime) -> bool:
    return not is_peak(now)


def is_offpeak_day(now: datetime) -> bool:
    m = minute_of_day(now)
    return 660 <= m < 1020


def is_offpeak_night(now: datetime) -> bool:
    m = minute_of_day(now)
    return m < 420 or m >= 1320


def machine_power_window(now: datetime) -> bool:
    m = minute_of_day(now)
    return m >= 1290 or m < 420 or 630 <= m < 1020
