#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import enum
import re

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Type


PATTERN_TARGET_DATETIME = re.compile(
    r'(?:День рождения|Праздник|Напомни о) "(?P<target>.+?)" '
    r"(?P<day>\d{1,2}) (?P<month>\w+)"
    r"(:?.*?(?P<year>\d{4}))?"
    r"(:?.*?(?P<time>\d{2}:\d{2}))?",
    flags=re.IGNORECASE,
)
PATTERN_REPEAT_EVERY = re.compile(
    r"Повтор (?:раз в|каждый) "
    r"(?P<unit>день|неделю|месяц|полгода|год"
    r"|понедельник|вторник|среду|четверг|пятницу|суббота|воскресенье)",
    flags=re.IGNORECASE,
)
PATTERN_REPEAT_BEFORE = re.compile(
    r"Напомни(?:ть)? (за .+)",
    flags=re.IGNORECASE,
)
PATTERN_REPEAT_BEFORE_TIME_UNIT = re.compile(
    r"за ((:?(?P<number>\d+) )?)(?P<day>дн\w+|день|недел\w|месяц\w?)",
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


class TimeUnitWeekDayEnum(enum.IntEnum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


@dataclass
class TimeUnitWeekDayUnit:
    unit: TimeUnitWeekDayEnum

    @classmethod
    def parse_text(cls, value: str) -> Optional["TimeUnitWeekDayUnit"]:
        match value:
            case "понедельник":
                return cls(unit=TimeUnitWeekDayEnum.MONDAY)
            case "вторник":
                return cls(unit=TimeUnitWeekDayEnum.TUESDAY)
            case "среду":
                return cls(unit=TimeUnitWeekDayEnum.WEDNESDAY)
            case "четверг":
                return cls(unit=TimeUnitWeekDayEnum.THURSDAY)
            case "пятницу":
                return cls(unit=TimeUnitWeekDayEnum.FRIDAY)
            case "суббота":
                return cls(unit=TimeUnitWeekDayEnum.SATURDAY)
            case "воскресенье":
                return cls(unit=TimeUnitWeekDayEnum.SUNDAY)
            case _:
                return

    @classmethod
    def parse_value(cls, value: str) -> "TimeUnitWeekDayUnit":
        return cls(unit=TimeUnitWeekDayEnum[value])

    def get_value(self) -> str:
        return self.unit.name

    def get_next_datetime(self, dt: datetime) -> datetime:
        while True:
            dt += timedelta(days=1)
            if dt.isoweekday() == self.unit.value:
                break
        return dt


@dataclass
class TimeUnit:
    number: int
    unit: TimeUnitEnum

    @classmethod
    def parse_text(cls, value: str) -> Optional["TimeUnit"]:
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

    @classmethod
    def parse_value(cls, value: str) -> "TimeUnit":
        number_str, unit_str = value.split()
        return cls(number=int(number_str), unit=TimeUnitEnum(unit_str))

    def get_value(self) -> str:
        return f"{self.number} {self.unit.value}"

    def get_prev_datetime(self, dt: datetime) -> datetime:
        return dt - self.get_timedelta()

    def get_next_datetime(self, dt: datetime) -> datetime:
        return dt + self.get_timedelta()

    def get_timedelta(self) -> timedelta:
        return timedelta(days=self.number * self.unit.days())

    def __lt__(self, other: "TimeUnit") -> bool:
        return self.get_timedelta() < other.get_timedelta()


@dataclass
class RepeatEvery:
    unit: TimeUnit | TimeUnitWeekDayUnit

    @classmethod
    def get_unit_classes(cls) -> list[Type[TimeUnit] | Type[TimeUnitWeekDayUnit]]:
        return [TimeUnit, TimeUnitWeekDayUnit]

    @classmethod
    def parse_text(cls, value: str) -> Optional["RepeatEvery"]:
        for unit_cls in cls.get_unit_classes():
            if unit := unit_cls.parse_text(value):
                return cls(unit=unit)
        return

    @classmethod
    def parse_value(cls, value: str) -> Optional["RepeatEvery"]:
        for unit_cls in cls.get_unit_classes():
            try:
                if unit := unit_cls.parse_value(value):
                    return cls(unit=unit)
            except Exception:
                pass
        return

    def get_value(self) -> str:
        return self.unit.get_value()

    def get_next_datetime(self, dt: datetime) -> datetime:
        return self.unit.get_next_datetime(dt)


@dataclass
class ParseResult:
    target: str
    target_datetime: datetime
    repeat_every: RepeatEvery | None = None
    repeat_before: list[TimeUnit] = field(default_factory=list)


@dataclass
class Defaults:
    hours: int
    minutes: int


def get_repeat_every(command: str) -> RepeatEvery | None:
    m = PATTERN_REPEAT_EVERY.search(command)
    if not m:
        return

    return RepeatEvery.parse_text(m.group("unit"))


def parse_repeat_before(command: str) -> list[TimeUnit]:
    m = PATTERN_REPEAT_BEFORE.search(command)
    if not m:
        return []

    time_by_unit: dict[timedelta, TimeUnit] = dict()

    for m in PATTERN_REPEAT_BEFORE_TIME_UNIT.finditer(m.group()):
        number_value: str | None = m.group("number")
        if number_value is not None:
            number: int = int(number_value)
        else:
            number: int = 1

        day_value: str = m.group("day")
        time_unit: TimeUnit = TimeUnit.parse_text(day_value)
        time_unit.number = number

        time_by_unit[time_unit.get_timedelta()] = time_unit

    return sorted(time_by_unit.values(), reverse=True)


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
    dt: datetime,
    default: Defaults,
) -> ParseResult | None:
    command = command.strip()

    m = PATTERN_TARGET_DATETIME.search(command)
    if not m:
        return

    day: int = int(m.group("day"))
    month: int = parse_month(m.group("month"))

    year_value: str | None = m.group("year")
    if year_value is not None:
        year: int = int(year_value)
    else:
        year: int = dt.year

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

    if target_datetime < dt:
        target_datetime = target_datetime.replace(year=target_datetime.year + 1)

    return ParseResult(
        target=m.group("target"),
        target_datetime=target_datetime,
        repeat_every=get_repeat_every(command),
        repeat_before=parse_repeat_before(command),
    )


if __name__ == "__main__":
    now = datetime.now()

    repeat_every_month = RepeatEvery.parse_text("месяц")
    print(repeat_every_month)
    print(repeat_every_month.get_value())
    print(RepeatEvery.parse_value(repeat_every_month.get_value()))
    assert repeat_every_month == RepeatEvery.parse_value(repeat_every_month.get_value())
    print(repeat_every_month.get_next_datetime(now))
    print()

    repeat_every_thursday = RepeatEvery.parse_text("четверг")
    print(repeat_every_thursday)
    print(repeat_every_thursday.get_value())
    print(RepeatEvery.parse_value(repeat_every_thursday.get_value()))
    assert repeat_every_thursday == RepeatEvery.parse_value(
        repeat_every_thursday.get_value()
    )
    print(repeat_every_thursday.get_next_datetime(now))
    print()

    assert TimeUnit.parse_value("3 DAY") == TimeUnit(number=3, unit=TimeUnitEnum.DAY)
    assert TimeUnit.parse_value("1 YEAR") == TimeUnit(number=1, unit=TimeUnitEnum.YEAR)

    # TODO: Перенести в тесты
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
Напомни о "Звонок другу" 29 декабря
Напомни о "Звонок другу" 29 декабря. Напомнить за неделю, за 2 дня, за 7 дней, за 3 дня, за 2 дня, за день
Напомни о "xxx" 10 февраля в 14:55
Напомни о "xxx" 12 июля в 17:55. Напомни за неделю, за 3 дня, за 2 дня, за 1 день
Напомни о "Чатик 🍕" 17 июля в 12:00. Повтор каждый четверг
    """.strip()

    now = datetime.utcnow()
    default = Defaults(hours=11, minutes=0)

    for line in text.splitlines():
        print(line)

        result = parse_command(line, dt=now, default=default)
        print(result)
        print("Целевая дата:", result.target_datetime)
        print(
            "Следующая целевая дата:",
            result.repeat_every.get_next_datetime(result.target_datetime)
            if result.repeat_every
            else "Нет",
        )
        for time_unit in result.repeat_before:
            print(
                time_unit.get_prev_datetime(result.target_datetime),
                repr(time_unit.get_value()),
            )

        print()
