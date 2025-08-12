#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import enum
import re

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Type


class ParserException(Exception):
    pass


PATTERN_TARGET_DATETIME = re.compile(
    r"""
    .*?
    # Причина
    "(?P<target>.+?)"\s*
    (
        # День месяц год в DD MMM YYYY, MMM - название месяца, а не номер
        (?P<day>\d{1,2})\s*(?P<month>\w+)(.*?(?P<year>\d{4}))?
        |
        # Относительные дни
        (?:в\s*)?(?:\s*следующ..\s*)?
        (?P<relative_day>
            сегодня|завтра|послезавтра
            |понедельник|вторник|среду|четверг|пятницу|субботу|воскресенье
        )
    )
    # Время в HH:MM
    (.*?(?P<time>\d{2}:\d{2}))?
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)

# TODO: Парсить даты с указанием количества
# TODO: Поддерживать тесты с указанием количества
PATTERN_REPEAT_EVERY = re.compile(
    r"Повтор\s*(?:раз\s*в|кажд\w{1,2})\s*((?P<number>\d+)\s*)?"
    r"(?P<unit>день|дн\w{1,2}|недел\w|месяц|полгода|год"
    r"|понедельник|вторник|среду|четверг|пятницу|суббот\w|воскресенье)",
    flags=re.IGNORECASE,
)
PATTERN_REPEAT_BEFORE = re.compile(
    r"Напомни(?:ть)?\s*(за\s*.+)",
    flags=re.IGNORECASE,
)
PATTERN_REPEAT_BEFORE_TIME_UNIT = re.compile(
    r"за\s*((?P<number>\d+)\s*)?(?P<day>дн\w+|день|недел\w|месяц\w?|полгода|год\w?)",
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
                raise ParserException(f"Неподдерживаемый элемент {self}")


class TimeUnitWeekDayEnum(enum.IntEnum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


@dataclass
class TimeUnit:
    number: int
    unit: TimeUnitEnum

    @classmethod
    def parse_text(cls, value: str) -> Optional["TimeUnit"]:
        if not value:
            return

        match value.lower():
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
class TimeUnitWeekDayUnit:
    unit: TimeUnitWeekDayEnum

    @classmethod
    def parse_text(cls, value: str) -> Optional["TimeUnitWeekDayUnit"]:
        if not value:
            return

        match value.lower():
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
            case "суббота" | "субботу":
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

    number_value: str | None = m.group("number")
    if number_value is not None:
        number: int = int(number_value)
    else:
        number: int = 1

    repeat_every: RepeatEvery | None = RepeatEvery.parse_text(m.group("unit"))
    if repeat_every and isinstance(repeat_every.unit, TimeUnit):
        repeat_every.unit.number *= number

    return repeat_every


def parse_repeat_before(command: str) -> list[TimeUnit]:
    if not command:
        return []

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
        time_unit.number *= number

        time_by_unit[time_unit.get_timedelta()] = time_unit

    return sorted(time_by_unit.values(), reverse=True)


def parse_month(month_value: str) -> int | None:
    if not month_value:
        return

    month_value: str = month_value.lower()
    try:
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
    except:
        return


def parse_command(
    command: str,
    dt: datetime,
    defaults: Defaults,
) -> ParseResult:
    command = command.strip()

    m = PATTERN_TARGET_DATETIME.search(command)
    if not m:
        raise ParserException(f"Команда {command!r} не соответствует шаблону")

    relative_day: str | None = m.group("relative_day")
    if relative_day:
        new_dt: datetime = dt

        value: str = relative_day.lower()
        match value:
            case "сегодня":
                pass
            case "завтра":
                new_dt += timedelta(days=1)
            case "послезавтра":
                new_dt += timedelta(days=2)
            case _:
                unit: TimeUnitWeekDayUnit | None = TimeUnitWeekDayUnit.parse_text(value)
                if not unit:
                    raise ParserException(f"Неподдерживаемый элемент {relative_day!r}")

                new_dt = unit.get_next_datetime(new_dt)

        day = new_dt.day
        month = new_dt.month
        year = new_dt.year

    else:
        day: int = int(m.group("day"))

        month_str: str = m.group("month")
        month: int | None = parse_month(month_str)
        if month is None:
            raise ParserException(f"Не удалось определить месяц {month_str!r}")

        year_value: str | None = m.group("year")
        year: int = int(year_value) if year_value else dt.year

    time_value: str | None = m.group("time")
    if time_value:
        parts = time_value.split(":")
        hours, minutes = map(int, parts)
    else:
        hours = defaults.hours
        minutes = defaults.minutes

    # TODO: Проверить високосные даты
    target_datetime = datetime(
        day=day, month=month, year=year, hour=hours, minute=minutes
    )

    # TODO: Тут нужно внимательнее проверить - мб не на год продлевать, а на повтор
    if target_datetime < dt:
        if relative_day == "сегодня":  # TODO:
            target_datetime += timedelta(days=1)
        else:
            target_datetime = target_datetime.replace(year=target_datetime.year + 1)

    return ParseResult(
        target=m.group("target"),
        target_datetime=target_datetime,
        repeat_every=get_repeat_every(command),
        repeat_before=parse_repeat_before(command),
    )
