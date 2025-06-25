#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import enum
import re

from dataclasses import dataclass


PATTERN_REPEAT = re.compile(
    r"Повтор (?:раз в|каждый) (?P<unit>день|неделю|месяц|полгода|год).",
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


def get_repeat(text: str) -> TimeUnit | None:
    m = PATTERN_REPEAT.search(text.lower())
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
День рождения xxx в dd mmmm. Повтор раз в год. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения xxx в dd mmmm. Повтор раз в полгода. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения xxx в dd mmmm. Повтор раз в месяц. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения xxx в dd mmmm. Повтор раз в неделю. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения xxx в dd mmmm. Повтор каждый день. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
День рождения xxx в dd mmmm. Напоминать за месяц, за неделю, за 3 дня, за день, в тот же день
Праздник xxx в dd mmmm. Повтор каждый год. Напоминать в тот же день
""".strip()


for line in text.splitlines():
    print(line)
    repeat: TimeUnit | None = get_repeat(line)
    print(repeat)
    print()
