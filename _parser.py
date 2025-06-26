#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import enum
import re

from dataclasses import dataclass
from datetime import datetime


PATTERN_TARGET_DATETIME = re.compile(
    r'(?:День рождения|Праздник|Напомни о) "(?P<target>\w+)" в (?P<day>\d{1,2}) (?P<month>\w+)(:? (?P<year>\d{4}))?',
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


def get_target_datetime(text: str) -> datetime | None:
    text = text.lower()

    m = PATTERN_TARGET_DATETIME.search(text)
    if not m:
        return

    # TODO:
    return m


def get_repeat(text: str) -> TimeUnit | None:
    text = text.lower()

    m = PATTERN_REPEAT.search(text)
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


# TODO:
text = """
День рождения "xxx" в 10 февраля. Повтор раз в год. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения "xxx" в 10 февраля. Повтор раз в полгода. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения "xxx" в 10 февраля. Повтор раз в месяц. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения "xxx" в 10 февраля. Повтор раз в неделю. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения "xxx" в 10 февраля. Повтор каждый день
День рождения "xxx" в 10 февраля. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
Праздник "xxx" в 10 февраля. Повтор каждый год. Напоминать в тот же день
Праздник "xxx" в 10 февраля 2026 года. Повтор каждый год. Напоминать в тот же день
Напомни о "xxx" в 10 февраля. Повтор раз в год. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
""".strip()


for line in text.splitlines():
    print(line)
    print(get_target_datetime(line))
    repeat: TimeUnit | None = get_repeat(line)
    print(repeat)
    print()
