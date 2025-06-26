#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import enum
import re

from dataclasses import dataclass
from datetime import datetime


PATTERN_TARGET_DATETIME = re.compile(
    r"(?:День рождения|Праздник|Напомни о) "
    r'"(?P<target>\w+)" (?P<day>\d{1,2}) (?P<month>\w+)'
    r"(:?.*?(?P<year>\d{4}))?"
    r"(:?.*?(?P<time>\d{2}:\d{2}))?",
    flags=re.IGNORECASE,
)
PATTERN_REPEAT = re.compile(
    r"Повтор (?:раз в|каждый) (?P<unit>день|неделю|месяц|полгода|год)",
    flags=re.IGNORECASE,
)


class AutoName(enum.Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name


class TimeUnitEnum(AutoName):
    YEAR = enum.auto()
    MONTH = enum.auto()
    WEEK = enum.auto()
    DAY = enum.auto()


@dataclass
class TimeUnit:
    number: int
    unit: TimeUnitEnum


@dataclass
class ParseResult:
    target: str
    target_datetime: datetime
    repeat: TimeUnit | None = None


@dataclass
class Defaults:
    hours: int
    minutes: int


def get_repeat(command: str) -> TimeUnit | None:
    m = PATTERN_REPEAT.search(command)
    if not m:
        return

    match m.group("unit"):
        case "год":
            return TimeUnit(number=1, unit=TimeUnitEnum.YEAR)
        case "полгода":
            return TimeUnit(number=6, unit=TimeUnitEnum.MONTH)
        case "месяц":
            return TimeUnit(number=1, unit=TimeUnitEnum.MONTH)
        case "неделю":
            return TimeUnit(number=1, unit=TimeUnitEnum.WEEK)
        case "день":
            return TimeUnit(number=1, unit=TimeUnitEnum.DAY)
        case _:
            return


def parse_month(month_value: str) -> int:
    return [
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    ].index(month_value) + 1


def parse_command(
    command: str,
    default: Defaults = Defaults(hours=11, minutes=0),
) -> ParseResult | None:
    command = command.lower()

    m = PATTERN_TARGET_DATETIME.search(command)
    if not m:
        return

    now: datetime = datetime.now()

    print(m.groupdict())
    day: int = int(m.group("day"))
    month: int = parse_month(m.group("month"))

    year_value: str | None = m.group("year")
    if year_value is not None:
        year: int = int(year_value)
    else:
        year: int = now.year

    time_value: str | None = m.group("time")
    if time_value:
        parts = time_value.split(":")
        hours, minutes = map(int, parts)
    else:
        hours = default.hours
        minutes = default.minutes

    # TODO: Проверить високосные даты
    target_datetime = datetime(
        day=day, month=month, year=year, hour=hours, minute=minutes
    )

    if target_datetime < now:
        target_datetime = target_datetime.replace(year=target_datetime.year + 1)

    return ParseResult(
        target=m.group("target"),
        target_datetime=target_datetime,
        repeat=get_repeat(command),
    )


# TODO:
text = """
День рождения "xxx" 10 февраля. Повтор раз в год. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения "xxx" 10 февраля. Повтор раз в полгода. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения "xxx" 10 февраля. Повтор раз в месяц. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения "xxx" 10 февраля. Повтор раз в неделю. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения "xxx" 10 февраля. Повтор каждый день
День рождения "xxx" 10 февраля в 14:55. Повтор каждый день
День рождения "xxx" 10 февраля 2027 года. Повтор каждый день
День рождения "xxx" 10 февраля 2027 года в 14:55. Повтор каждый день
День рождения "xxx" 10 февраля. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
Праздник "xxx" 10 февраля. Повтор каждый год. Напоминать в тот же день
Праздник "xxx" 10 февраля 2026 года. Повтор каждый год. Напоминать в тот же день
Напомни о "xxx" 10 февраля. Повтор раз в год. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
Напомни о "xxx" 10 февраля
""".strip()


for line in text.splitlines():
    print(line)
    print(parse_command(line))
    print()
