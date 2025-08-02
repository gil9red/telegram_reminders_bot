#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import unittest
from datetime import datetime, timedelta

from parser import (
    TimeUnitEnum,
    TimeUnitWeekDayEnum,
    RepeatEvery,
    TimeUnit,
    TimeUnitWeekDayUnit,
    Defaults,
    ParseResult,
    parse_month,
    get_repeat_every,
    parse_repeat_before,
    parse_command,
)


class TestCaseParserCommon(unittest.TestCase):
    def test_TimeUnitEnum_days(self):
        self.assertEqual(365, TimeUnitEnum.YEAR.days())
        self.assertEqual(30, TimeUnitEnum.MONTH.days())
        self.assertEqual(7, TimeUnitEnum.WEEK.days())
        self.assertEqual(1, TimeUnitEnum.DAY.days())

        for value, enum_value in [
            ("YEAR", TimeUnitEnum.YEAR),
            ("MONTH", TimeUnitEnum.MONTH),
            ("WEEK", TimeUnitEnum.WEEK),
            ("DAY", TimeUnitEnum.DAY),
        ]:
            with self.subTest(value=value, enum_value=enum_value):
                self.assertEqual(value, enum_value.value)
                self.assertEqual(value, enum_value.name)
                self.assertEqual(enum_value, TimeUnitEnum(value))
                self.assertEqual(enum_value, TimeUnitEnum[enum_value.name])

    def test_TimeUnitWeekDayEnum(self):
        for value, enum_value in [
            (1, TimeUnitWeekDayEnum.MONDAY),
            (2, TimeUnitWeekDayEnum.TUESDAY),
            (3, TimeUnitWeekDayEnum.WEDNESDAY),
            (4, TimeUnitWeekDayEnum.THURSDAY),
            (5, TimeUnitWeekDayEnum.FRIDAY),
            (6, TimeUnitWeekDayEnum.SATURDAY),
            (7, TimeUnitWeekDayEnum.SUNDAY),
        ]:
            with self.subTest(value=value, enum_value=enum_value):
                self.assertEqual(value, enum_value.value)
                self.assertEqual(enum_value, TimeUnitWeekDayEnum(value))
                self.assertEqual(enum_value, TimeUnitWeekDayEnum[enum_value.name])

    def test_ParseResult(self):
        target = "target"
        target_datetime = datetime.now()

        result: ParseResult = ParseResult(
            target=target,
            target_datetime=target_datetime,
        )
        self.assertEqual(target, result.target)
        self.assertEqual(target_datetime, result.target_datetime)
        self.assertIsNone(result.repeat_every)
        self.assertEqual([], result.repeat_before)

        repeat_every = RepeatEvery(unit=TimeUnit(number=10, unit=TimeUnitEnum.DAY))
        repeat_before = [
            TimeUnit(number=1, unit=TimeUnitEnum.DAY),
            TimeUnit(number=2, unit=TimeUnitEnum.DAY),
            TimeUnit(number=3, unit=TimeUnitEnum.DAY),
        ]

        result: ParseResult = ParseResult(
            target=target,
            target_datetime=target_datetime,
            repeat_every=repeat_every,
            repeat_before=repeat_before,
        )
        self.assertEqual(target, result.target)
        self.assertEqual(target_datetime, result.target_datetime)
        self.assertEqual(repeat_every, result.repeat_every)
        self.assertEqual(repeat_before, result.repeat_before)

    def test_Defaults(self):
        defaults = Defaults(hours=10, minutes=30)
        self.assertEqual(10, defaults.hours)
        self.assertEqual(30, defaults.minutes)

    def test_get_repeat_every(self):
        for prefix in ["Повтор раз в", "Повтор каждый"]:
            for values, repeat_every in TestCaseParserRepeatEvery.get_test_text():
                with self.subTest(
                    prefix=prefix, values=values, repeat_every=repeat_every
                ):
                    for value in values:
                        text = f"{prefix} {value}"
                        self.assertEqual(
                            repeat_every,
                            get_repeat_every(text),
                            msg=f"Проблема парсинга {text!r}",
                        )

    def test_parse_repeat_before(self):
        for text, units in [
            (
                "Напомнить за месяц, за неделю, за 3 дня, за день",
                [
                    TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                    TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (
                "Напомнить за день, за неделю, за месяц, за 3 дня",
                [
                    TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                    TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (
                "Напомнить за месяц, за 2 недели, за неделю, за 3 дня, за день",
                [
                    TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                    TimeUnit(number=2, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (
                "Напомнить за неделю, за 3 дня, за день",
                [
                    TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (
                "Напомнить за 3 дня, за день",
                [
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (
                "Напомнить за 2 дня",
                [TimeUnit(number=2, unit=TimeUnitEnum.DAY)],
            ),
            (
                "Напомнить за день",
                [TimeUnit(number=1, unit=TimeUnitEnum.DAY)],
            ),
            (
                "Напомнить за неделю, за 2 дня, за 7 дней, за 3 дня, за 2 дня, за день",
                [
                    TimeUnit(number=7, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=2, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (None, []),
            ("None", []),
        ]:
            with self.subTest(text=text, units=units):
                self.assertEqual(units, parse_repeat_before(text))

    def test_parse_month(self):
        for number, month in [
            (1, "января"),
            (1, "Января"),
            (2, "февраля"),
            (3, "марта"),
            (4, "апреля"),
            (5, "мая"),
            (6, "июня"),
            (7, "июля"),
            (8, "августа"),
            (9, "сентября"),
            (9, "СЕНТЯБРЯ"),
            (10, "октября"),
            (11, "ноября"),
            (12, "декабря"),
            (None, "None"),
            (None, ""),
            (None, None),
        ]:
            with self.subTest(number=number, month=month):
                self.assertEqual(number, parse_month(month))

    def test_parse_command(self):
        # TODO:
        1 / 0


class TestCaseTimeUnit(unittest.TestCase):
    @classmethod
    def get_test_data(cls) -> list[tuple[str, TimeUnit]]:
        return [
            ("1 DAY", TimeUnit(number=1, unit=TimeUnitEnum.DAY)),
            ("10 DAY", TimeUnit(number=10, unit=TimeUnitEnum.DAY)),
            ("1 WEEK", TimeUnit(number=1, unit=TimeUnitEnum.WEEK)),
            ("2 WEEK", TimeUnit(number=2, unit=TimeUnitEnum.WEEK)),
            ("1 MONTH", TimeUnit(number=1, unit=TimeUnitEnum.MONTH)),
            ("3 MONTH", TimeUnit(number=3, unit=TimeUnitEnum.MONTH)),
            ("1 YEAR", TimeUnit(number=1, unit=TimeUnitEnum.YEAR)),
            ("2 YEAR", TimeUnit(number=2, unit=TimeUnitEnum.YEAR)),
        ]

    def test_parse_text(self):
        for values, unit in [
            (
                ["год", "года", "ГОДА"],
                TimeUnit(number=1, unit=TimeUnitEnum.YEAR),
            ),
            (
                ["полгода", "полГОДА"],
                TimeUnit(number=6, unit=TimeUnitEnum.MONTH),
            ),
            (
                ["месяц", "месяца", "месяцев", "МЕСЯЦа"],
                TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
            ),
            (
                ["неделю", "недели", "недель", "НЕДЕЛЬ"],
                TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
            ),
            (
                ["день", "дня", "дней", "ДНЯ"],
                TimeUnit(number=1, unit=TimeUnitEnum.DAY),
            ),
            (
                ["None", "", None],
                None,
            ),
        ]:
            with self.subTest(values=values, unit=unit):
                for text in values:
                    self.assertEqual(unit, TimeUnit.parse_text(text))

    def test_parse_value(self):
        for _, unit in self.get_test_data():
            with self.subTest(unit=unit):
                value = unit.get_value()
                self.assertEqual(unit, TimeUnit.parse_value(value))

    def test_get_value(self):
        for value, unit in self.get_test_data():
            with self.subTest(value=value, unit=unit):
                self.assertEqual(value, unit.get_value())

    def test_get_prev_datetime(self):
        dt = datetime(year=2020, month=1, day=1, hour=10, minute=0, second=0)

        for _, unit in self.get_test_data():
            with self.subTest(unit=unit):
                self.assertEqual(dt - unit.get_timedelta(), unit.get_prev_datetime(dt))

    def test_get_next_datetime(self):
        dt = datetime(year=2020, month=1, day=1, hour=10, minute=0, second=0)

        for _, unit in self.get_test_data():
            with self.subTest(unit=unit):
                self.assertEqual(dt + unit.get_timedelta(), unit.get_next_datetime(dt))

    def test_get_timedelta(self):
        for _, unit in self.get_test_data():
            with self.subTest(unit=unit):
                days = unit.number * unit.unit.days()
                self.assertEqual(timedelta(days=days), unit.get_timedelta())

    def test_sorting(self):
        data: list[TimeUnit] = [
            TimeUnit(number=1, unit=TimeUnitEnum.DAY),
            TimeUnit(number=10, unit=TimeUnitEnum.DAY),
            TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
            TimeUnit(number=2, unit=TimeUnitEnum.WEEK),
            TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
            TimeUnit(number=3, unit=TimeUnitEnum.MONTH),
            TimeUnit(number=1, unit=TimeUnitEnum.YEAR),
            TimeUnit(number=2, unit=TimeUnitEnum.YEAR),
        ]
        data_sorted: list[TimeUnit] = [
            TimeUnit(number=1, unit=TimeUnitEnum.DAY),
            TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
            TimeUnit(number=10, unit=TimeUnitEnum.DAY),
            TimeUnit(number=2, unit=TimeUnitEnum.WEEK),
            TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
            TimeUnit(number=3, unit=TimeUnitEnum.MONTH),
            TimeUnit(number=1, unit=TimeUnitEnum.YEAR),
            TimeUnit(number=2, unit=TimeUnitEnum.YEAR),
        ]

        self.assertEqual(data_sorted, sorted(data))
        self.assertEqual(data_sorted[::-1], sorted(data, reverse=True))


class TestCaseTimeUnitWeekDayUnit(unittest.TestCase):
    @classmethod
    def get_test_data(cls) -> list[tuple[str, TimeUnitWeekDayUnit]]:
        return [
            (
                "понедельник",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.MONDAY),
            ),
            (
                "ПОНЕДЕЛЬНИК",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.MONDAY),
            ),
            (
                "вторник",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.TUESDAY),
            ),
            (
                "вторНИК",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.TUESDAY),
            ),
            (
                "среду",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.WEDNESDAY),
            ),
            (
                "четверг",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.THURSDAY),
            ),
            (
                "пятницу",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.FRIDAY),
            ),
            (
                "суббота",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SATURDAY),
            ),
            (
                "воскресенье",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SUNDAY),
            ),
        ]

    def test_parse_text(self):
        for text, unit in self.get_test_data() + [
            # Invalid
            ("None", None),
            ("", None),
            (None, None),
        ]:
            with self.subTest(text=text, unit=unit):
                self.assertEqual(unit, TimeUnitWeekDayUnit.parse_text(text))

    def test_parse_value(self):
        for _, unit in self.get_test_data():
            with self.subTest(unit=unit):
                value = unit.get_value()
                self.assertEqual(unit, TimeUnitWeekDayUnit.parse_value(value))

    def test_get_value(self):
        for value, unit in [
            (
                "MONDAY",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.MONDAY),
            ),
            (
                "TUESDAY",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.TUESDAY),
            ),
            (
                "WEDNESDAY",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.WEDNESDAY),
            ),
            (
                "THURSDAY",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.THURSDAY),
            ),
            (
                "FRIDAY",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.FRIDAY),
            ),
            (
                "SATURDAY",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SATURDAY),
            ),
            (
                "SUNDAY",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SUNDAY),
            ),
        ]:
            with self.subTest(value=value, unit=unit):
                self.assertEqual(value, unit.get_value())

    def test_get_next_datetime(self):
        dt = datetime(year=2025, month=7, day=1, hour=10, minute=0, second=0)

        for value, unit in [
            (
                datetime(year=2025, month=7, day=7, hour=10, minute=0, second=0),
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.MONDAY),
            ),
            (
                datetime(year=2025, month=7, day=8, hour=10, minute=0, second=0),
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.TUESDAY),
            ),
            (
                datetime(year=2025, month=7, day=2, hour=10, minute=0, second=0),
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.WEDNESDAY),
            ),
            (
                datetime(year=2025, month=7, day=3, hour=10, minute=0, second=0),
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.THURSDAY),
            ),
            (
                datetime(year=2025, month=7, day=4, hour=10, minute=0, second=0),
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.FRIDAY),
            ),
            (
                datetime(year=2025, month=7, day=5, hour=10, minute=0, second=0),
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SATURDAY),
            ),
            (
                datetime(year=2025, month=7, day=6, hour=10, minute=0, second=0),
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SUNDAY),
            ),
        ]:
            with self.subTest(value=value, unit=unit):
                self.assertEqual(value, unit.get_next_datetime(dt))


class TestCaseParserRepeatEvery(unittest.TestCase):
    @classmethod
    def get_test_data(cls) -> list[tuple[str, RepeatEvery]]:
        return [
            ("1 DAY", RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.DAY))),
            ("10 DAY", RepeatEvery(unit=TimeUnit(number=10, unit=TimeUnitEnum.DAY))),
            ("1 WEEK", RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.WEEK))),
            ("2 WEEK", RepeatEvery(unit=TimeUnit(number=2, unit=TimeUnitEnum.WEEK))),
            ("1 MONTH", RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.MONTH))),
            ("3 MONTH", RepeatEvery(unit=TimeUnit(number=3, unit=TimeUnitEnum.MONTH))),
            ("1 YEAR", RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.YEAR))),
            ("2 YEAR", RepeatEvery(unit=TimeUnit(number=2, unit=TimeUnitEnum.YEAR))),
            (
                "MONDAY",
                RepeatEvery(unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.MONDAY)),
            ),
            (
                "TUESDAY",
                RepeatEvery(unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.TUESDAY)),
            ),
            (
                "WEDNESDAY",
                RepeatEvery(
                    unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.WEDNESDAY)
                ),
            ),
            (
                "THURSDAY",
                RepeatEvery(
                    unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.THURSDAY)
                ),
            ),
            (
                "FRIDAY",
                RepeatEvery(unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.FRIDAY)),
            ),
            (
                "SATURDAY",
                RepeatEvery(
                    unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SATURDAY)
                ),
            ),
            (
                "SUNDAY",
                RepeatEvery(unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SUNDAY)),
            ),
        ]

    @classmethod
    def get_test_text(cls) -> list[tuple[list[str], RepeatEvery | None]]:
        return [
            (
                ["год", "года", "ГОДА"],
                RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.YEAR)),
            ),
            (
                ["полгода", "полГОДа"],
                RepeatEvery(unit=TimeUnit(number=6, unit=TimeUnitEnum.MONTH)),
            ),
            (
                ["месяц", "месяца", "месяцев", "МЕСЯЦев"],
                RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.MONTH)),
            ),
            (
                ["неделю", "недели", "недель", "НЕДель"],
                RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.WEEK)),
            ),
            (
                ["день", "дня", "дней", "дНЕЙ"],
                RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.DAY)),
            ),
            (
                ["понедельник", "ПОНЕДЕЛЬНИК"],
                RepeatEvery(unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.MONDAY)),
            ),
            (
                ["вторник", "вторНИК"],
                RepeatEvery(unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.TUESDAY)),
            ),
            (
                ["среду", "СРЕДУ"],
                RepeatEvery(
                    unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.WEDNESDAY)
                ),
            ),
            (
                ["четверг", "четВЕРГ"],
                RepeatEvery(
                    unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.THURSDAY)
                ),
            ),
            (
                ["пятницу", "ПЯТницу"],
                RepeatEvery(unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.FRIDAY)),
            ),
            (
                ["суббота", "СУБбота"],
                RepeatEvery(
                    unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SATURDAY)
                ),
            ),
            (
                ["воскресенье", "ВОСКРЕСЕНЬЕ"],
                RepeatEvery(unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SUNDAY)),
            ),
            (
                ["None", "", None],
                None,
            ),
        ]

    def test_get_unit_classes(self):
        self.assertEqual(
            [TimeUnit, TimeUnitWeekDayUnit], RepeatEvery.get_unit_classes()
        )

    def test_parse_text(self):
        for values, repeat_every in self.get_test_text():
            with self.subTest(values=values, repeat_every=repeat_every):
                for text in values:
                    self.assertEqual(repeat_every, RepeatEvery.parse_text(text))

    def test_parse_value(self):
        for value, repeat_every in self.get_test_data() + [
            # Invalid
            (
                "None",
                None,
            ),
            (
                "",
                None,
            ),
            (
                None,
                None,
            ),
        ]:
            with self.subTest(value=value, repeat_every=repeat_every):
                self.assertEqual(repeat_every, RepeatEvery.parse_value(value))

    def test_get_value(self):
        for value, repeat_every in self.get_test_data():
            with self.subTest(value=value, repeat_every=repeat_every):
                self.assertEqual(value, RepeatEvery.parse_value(value).get_value())

    def test_get_next_datetime(self):
        dt = datetime(year=2025, month=7, day=1, hour=10, minute=0, second=0)

        for value, repeat_every in [
            (
                datetime(year=2025, month=7, day=2, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.DAY)),
            ),
            (
                datetime(year=2025, month=7, day=11, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=10, unit=TimeUnitEnum.DAY)),
            ),
            (
                datetime(year=2025, month=7, day=8, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.WEEK)),
            ),
            (
                datetime(year=2025, month=7, day=15, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=2, unit=TimeUnitEnum.WEEK)),
            ),
            (
                datetime(year=2025, month=7, day=31, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.MONTH)),
            ),
            (
                datetime(year=2025, month=9, day=29, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=3, unit=TimeUnitEnum.MONTH)),
            ),
            (
                datetime(year=2026, month=7, day=1, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.YEAR)),
            ),
            (
                datetime(year=2027, month=7, day=1, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=2, unit=TimeUnitEnum.YEAR)),
            ),
            (
                datetime(year=2025, month=7, day=7, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.MONDAY)),
            ),
            (
                datetime(year=2025, month=7, day=8, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.TUESDAY)),
            ),
            (
                datetime(year=2025, month=7, day=2, hour=10, minute=0, second=0),
                RepeatEvery(
                    unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.WEDNESDAY)
                ),
            ),
            (
                datetime(year=2025, month=7, day=3, hour=10, minute=0, second=0),
                RepeatEvery(
                    unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.THURSDAY)
                ),
            ),
            (
                datetime(year=2025, month=7, day=4, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.FRIDAY)),
            ),
            (
                datetime(year=2025, month=7, day=5, hour=10, minute=0, second=0),
                RepeatEvery(
                    unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SATURDAY)
                ),
            ),
            (
                datetime(year=2025, month=7, day=6, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SUNDAY)),
            ),
        ]:
            with self.subTest(value=value, repeat_every=repeat_every):
                self.assertEqual(value, repeat_every.get_next_datetime(dt))


if __name__ == "__main__":
    unittest.main()
