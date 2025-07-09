#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import zoneinfo
from datetime import datetime, tzinfo

from third_party.get_tz_from_offset__zoneinfo import get_tz as get_tz_from_offset


def convert_tz(dt: datetime, from_tz: tzinfo, to_tz: tzinfo) -> datetime:
    return (
        dt.replace(tzinfo=from_tz)  # Указание часового пояса (дата не меняется)
        .astimezone(to_tz)  # Изменение времени и часового пояса (дата изменилась)
        .replace(tzinfo=None)  # Удаление часового пояса (дата не меняется)
    )


def get_tz(value: str) -> tzinfo | None:
    try:
        return get_tz_from_offset(value)
    except Exception:
        try:
            return zoneinfo.ZoneInfo(value)
        except zoneinfo.ZoneInfoNotFoundError:
            return
