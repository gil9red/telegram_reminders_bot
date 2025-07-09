#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from datetime import datetime, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from third_party.get_tz_from_offset__zoneinfo import get_tz as get_tz_from_offset


def convert_tz(dt: datetime, from_tz: tzinfo, to_tz: tzinfo) -> datetime:
    return (
        dt.replace(tzinfo=from_tz)  # Указание часового пояса (дата не меняется)
        .astimezone(to_tz)  # Изменение времени и часового пояса (дата изменилась)
        .replace(tzinfo=None)  # Удаление часового пояса (дата не меняется)
    )


def get_tz(value: str) -> tzinfo:
    try:
        return get_tz_from_offset(value)
    except Exception:
        try:
            return ZoneInfo(value)
        except ZoneInfoNotFoundError:
            pass

        raise ZoneInfoNotFoundError(value)


if __name__ == "__main__":
    print(get_tz("+02:30"))
    print(get_tz("-02:30"))
    print(get_tz("UTC"))
    print(get_tz("Europe/Moscow"))
    print()

    try:
        print(get_tz("dfgsdfsdfdsf"))
    except ZoneInfoNotFoundError as e:
        print(e)
        print(e.args)
