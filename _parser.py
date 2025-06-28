#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import enum
import re

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


PATTERN_TARGET_DATETIME = re.compile(
    r"(?:День рождения|Праздник|Напомни о) "
    r'"(?P<target>\w+)" (?P<day>\d{1,2}) (?P<month>\w+)'
    r"(:?.*?(?P<year>\d{4}))?"
    r"(:?.*?(?P<time>\d{2}:\d{2}))?",
    flags=re.IGNORECASE,
)
PATTERN_REPEAT_EVERY = re.compile(
    r"Повтор (?:раз в|каждый) (?P<unit>день|неделю|месяц|полгода|год)",
    flags=re.IGNORECASE,
)
PATTERN_REPEAT_BEFORE = re.compile(
    r"Напомнить (за .+)",
    flags=re.IGNORECASE,
)
PATTERN_REPEAT_BEFORE_TIME_UNIT = re.compile(
    r"за ((:?(?P<number>\d+) )?)(?P<day>дня|день|недел\w|месяц\w?)",
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

    def days(self) -> int:
        match self:
            case TimeUnitEnum.YEAR:
                return 365
            case TimeUnitEnum.MONTH:
                return 30
            case TimeUnitEnum.WEEK:
                return 7
            case TimeUnitEnum.DAY:
                return 1
            case _:
                raise Exception(f"Unsupported {self}")


@dataclass
class TimeUnit:
    number: int
    unit: TimeUnitEnum

    @classmethod
    def parse(cls, value: str) -> Optional["TimeUnit"]:
        match value:
            case "год" | "года":
                return cls(number=1, unit=TimeUnitEnum.YEAR)
            case "полгода":
                return cls(number=6, unit=TimeUnitEnum.MONTH)
            case "месяц" | "месяца" | "месяцев":
                return cls(number=1, unit=TimeUnitEnum.MONTH)
            case "неделю" | "недели" | "недель":
                return cls(number=1, unit=TimeUnitEnum.WEEK)
            case "день" | "дня" | "дней":
                return cls(number=1, unit=TimeUnitEnum.DAY)
            case _:
                return

    def get_timedelta(self) -> timedelta:
        return timedelta(days=self.number * self.unit.days())

    def __lt__(self, other: "TimeUnit") -> bool:
        return self.get_timedelta() < other.get_timedelta()


@dataclass
class ParseResult:
    target: str
    target_datetime: datetime
    repeat_every: TimeUnit | None = None
    repeat_before: list[TimeUnit] = field(default_factory=list)


@dataclass
class Defaults:
    hours: int
    minutes: int


def get_repeat_every(command: str) -> TimeUnit | None:
    m = PATTERN_REPEAT_EVERY.search(command)
    if not m:
        return

    return TimeUnit.parse(m.group("unit"))


def parse_repeat_before(command: str) -> list[TimeUnit]:
    items: list[TimeUnit] = []

    m = PATTERN_REPEAT_BEFORE.search(command)
    if not m:
        return items

    for m in PATTERN_REPEAT_BEFORE_TIME_UNIT.finditer(m.group()):
        number_value: str | None = m.group("number")
        if number_value is not None:
            number: int = int(number_value)
        else:
            number: int = 1

        day_value: str = m.group("day")
        time_unit: TimeUnit = TimeUnit.parse(day_value)
        time_unit.number = number

        items.append(time_unit)

    items.sort(reverse=True)

    return items


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
    now: datetime,
    default: Defaults,
) -> ParseResult | None:
    command = command.lower()

    m = PATTERN_TARGET_DATETIME.search(command)
    if not m:
        return

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
        repeat_every=get_repeat_every(command),
        repeat_before=parse_repeat_before(command),
    )


# TODO:
text = """
День рождения "xxx" 10 февраля. Повтор раз в год. Напомнить за месяц, за неделю, за 3 дня, за день
День рождения "xxx" 10 февраля. Повтор раз в полгода. Напомнить за месяц, за неделю, за 3 дня, за день
День рождения "xxx" 10 февраля. Повтор раз в месяц. Напомнить за месяц, за неделю, за 3 дня, за день
День рождения "xxx" 10 февраля. Повтор раз в месяц. Напомнить за месяц, за 2 недели, за неделю, за 3 дня, за день
День рождения "xxx" 10 февраля. Повтор раз в неделю. Напомнить за месяц, за неделю, за 3 дня, за день
День рождения "xxx" 10 февраля. Повтор каждый день
День рождения "xxx" 10 февраля в 14:55. Повтор каждый день
День рождения "xxx" 10 февраля 2027 года. Повтор каждый день
День рождения "xxx" 10 февраля 2027 года в 14:55. Повтор каждый день
Праздник "xxx" 10 февраля. Повтор каждый год
Праздник "xxx" 10 февраля 2026 года. Повтор каждый год
Напомни о "xxx" 10 февраля. Повтор раз в год. Напомнить за месяц, за неделю, за 3 дня, за день
Напомни о "xxx" 10 февраля
Напомни о "xxx" 10 февраля. Напомнить за неделю, за 3 дня, за день
Напомни о "xxx" 10 февраля. Напомнить за 3 дня, за день
День рождения "xxx" 10 февраля. Напомнить за месяц, за неделю, за 3 дня, за день
День рождения "xxx" 10 февраля. Напомнить за день, за неделю, за месяц, за 3 дня
Напомни о "xxx" 29 декабря 
""".strip()


now = datetime.utcnow()
default = Defaults(hours=11, minutes=0)

for line in text.splitlines():
    print(line)
    result = parse_command(line, now=now, default=default)
    print(result)
    print(result.target_datetime)
    for time_unit in result.repeat_before:
        print(result.target_datetime - time_unit.get_timedelta(), repr(f"{time_unit.number} {time_unit.unit.value}"))

    print()
