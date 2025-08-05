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
    ParserException,
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


# TODO: Проверить все тесты и варианты значений
class TestParseCommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.now: datetime = datetime(year=2025, month=4, day=15, hour=10, minute=0)
        cls.default: Defaults = Defaults(hours=11, minutes=0)

    # @classmethod
    # def get_test_data(cls) -> list[tuple[str, tuple[ParseResult | ParserException]]]:
    #     return [
    #         (
    #             'День рождения "Иван" 10 февраля. Напомнить за неделю, за 3 дня, за день',
    #             ParseResult(
    #                 target="Иван",
    #                 target_datetime=datetime(year=2026, month=2, day=10, hour=cls.default.hours, minute=cls.default.minutes),
    #                 repeat_every=None,
    #                 repeat_before=[
    #                     TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
    #                     TimeUnit(number=3, unit=TimeUnitEnum.DAY),
    #                     TimeUnit(number=1, unit=TimeUnitEnum.DAY),
    #                 ],
    #             ),
    #         ),
    #         # (
    #         #         'День рождения "Иван" 10 февраля. Напомнить за день, за 3 дня, за неделю',
    #         #         [
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
    #         #             TimeUnit(number=3, unit=TimeUnitEnum.DAY),
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.DAY),
    #         #         ],
    #         # ),
    #         # (
    #         #         'День рождения "Иван" 10 февраля. Напомнить за месяц, за неделю, за 3 дня, за день',
    #         #         [
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
    #         #             TimeUnit(number=3, unit=TimeUnitEnum.DAY),
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.DAY),
    #         #         ],
    #         # ),
    #         # (
    #         #         'День рождения "Иван" 10 февраля. Напомнить за день, за неделю, за месяц, за 3 дня',
    #         #         [
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
    #         #             TimeUnit(number=3, unit=TimeUnitEnum.DAY),
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.DAY),
    #         #         ],
    #         # ),
    #         # (
    #         #         'День рождения "Иван" 10 февраля. Напомнить за месяц, за 2 недели, за неделю, за 3 дня, за день',
    #         #         [
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
    #         #             TimeUnit(number=2, unit=TimeUnitEnum.WEEK),
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
    #         #             TimeUnit(number=3, unit=TimeUnitEnum.DAY),
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.DAY),
    #         #         ],
    #         # ),
    #         # (
    #         #         'День рождения "Иван" 10 февраля. Напомнить за неделю, за 3 дня, за день',
    #         #         [
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
    #         #             TimeUnit(number=3, unit=TimeUnitEnum.DAY),
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.DAY),
    #         #         ],
    #         # ),
    #         # (
    #         #         'День рождения "Иван" 10 февраля. Напомнить за 3 дня, за день',
    #         #         [
    #         #             TimeUnit(number=3, unit=TimeUnitEnum.DAY),
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.DAY),
    #         #         ],
    #         # ),
    #         # (
    #         #         'День рождения "Иван" 10 февраля. Напомнить за 2 дня',
    #         #         [TimeUnit(number=2, unit=TimeUnitEnum.DAY)],
    #         # ),
    #         # (
    #         #         'День рождения "Иван" 10 февраля. Напомнить за день',
    #         #         [TimeUnit(number=1, unit=TimeUnitEnum.DAY)],
    #         # ),
    #         # (
    #         #         'День рождения "Иван" 10 февраля. Напомнить за неделю, за 2 дня, '
    #         #         'за 7 дней, за 3 дня, за 2 дня, за день',
    #         #         [
    #         #             TimeUnit(number=7, unit=TimeUnitEnum.DAY),
    #         #             TimeUnit(number=3, unit=TimeUnitEnum.DAY),
    #         #             TimeUnit(number=2, unit=TimeUnitEnum.DAY),
    #         #             TimeUnit(number=1, unit=TimeUnitEnum.DAY),
    #         #         ],
    #         # ),
    #         # ('День рождения "Иван" 10 февраля', []),
    #         # ('День рождения "Иван" 10 февраля.', []),
    #     ]

    def test_parse_absolute_date(self):
        command = 'День рождения "Иван" 10 февраля'
        result = parse_command(command, self.now, self.default)
        self.assertIsInstance(result, ParseResult)
        self.assertEqual(result.target, "Иван")
        self.assertEqual(result.target_datetime.day, 10)
        self.assertEqual(result.target_datetime.month, 2)
        self.assertEqual(result.target_datetime.year, 2026)
        self.assertEqual(result.target_datetime.hour, self.default.hours)
        self.assertEqual(result.target_datetime.minute, self.default.minutes)

    def test_parse_relative_today(self):
        # TODO: Проверить, что если сейчас 10:00, то нужно будет напомнить в 11:00
        command = 'Напомни о "Задача" сегодня'
        result = parse_command(command, self.now, self.default)
        self.assertEqual(result.target_datetime.day, self.now.day)
        self.assertEqual(result.target_datetime.month, self.now.month)
        self.assertEqual(result.target_datetime.year, self.now.year)
        self.assertEqual(result.target_datetime.hour, self.default.hours)
        self.assertEqual(result.target_datetime.minute, self.default.minutes)

    def test_parse_relative_tomorrow(self):
        # TODO: Добавить время
        command = 'Напомни о "Собрание" завтра'
        result = parse_command(command, self.now, self.default)
        expected_date = self.now + timedelta(days=1)
        self.assertEqual(result.target_datetime.day, expected_date.day)
        self.assertEqual(result.target_datetime.month, expected_date.month)
        self.assertEqual(result.target_datetime.year, expected_date.year)
        self.assertEqual(result.target_datetime.hour, self.default.hours)
        self.assertEqual(result.target_datetime.minute, self.default.minutes)

    def test_parse_relative_day_after_tomorrow(self):
        # TODO: Добавить время
        command = 'Напомни о "Собрание" послезавтра'
        result = parse_command(command, self.now, self.default)
        expected_date = self.now + timedelta(days=2)
        self.assertEqual(result.target_datetime.day, expected_date.day)
        self.assertEqual(result.target_datetime.month, expected_date.month)
        self.assertEqual(result.target_datetime.year, expected_date.year)
        self.assertEqual(result.target_datetime.hour, self.default.hours)
        self.assertEqual(result.target_datetime.minute, self.default.minutes)

    def test_parse_relative_next_weekday(self):
        command = 'Напомни о "Мероприятие" в следующий понедельник'
        result = parse_command(command, self.now, self.default)
        unit = TimeUnitWeekDayUnit.parse_text("понедельник")
        next_monday = unit.get_next_datetime(self.now)
        self.assertEqual(result.target_datetime.day, next_monday.day)
        self.assertEqual(result.target_datetime.month, next_monday.month)
        self.assertEqual(result.target_datetime.year, next_monday.year)
        self.assertEqual(result.target_datetime.hour, self.default.hours)
        self.assertEqual(result.target_datetime.minute, self.default.minutes)

    def test_parse_with_time(self):
        command = 'Напомни о "Встреча" 10 февраля в 14:55'
        result = parse_command(command, self.now, self.default)
        self.assertEqual(result.target_datetime.hour, 14)
        self.assertEqual(result.target_datetime.minute, 55)

    def test_parse_with_repeat_every(self):
        # for command, result in self.get_test_data():
        #     with self.subTest(command=command, result=result):
        #         actual = parse_command(command, self.now, self.default)
        #         self.assertEqual(result, actual, msg=f"Проблема с {command!r}")

        command = 'День рождения "Иван" 10 февраля. Повтор раз в год'
        result = parse_command(command, self.now, self.default)
        self.assertIsInstance(result.repeat_every, RepeatEvery)
        self.assertEqual(result.repeat_every.get_value(), "1 YEAR")

    def test_parse_with_repeat_before(self):
        for command, units in [
            (
                'День рождения "Иван" 10 февраля. Напомнить за неделю, за 3 дня, за день',
                [
                    TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (
                'День рождения "Иван" 10 февраля. Напомнить за день, за 3 дня, за неделю',
                [
                    TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (
                'День рождения "Иван" 10 февраля. Напомнить за месяц, за неделю, за 3 дня, за день',
                [
                    TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                    TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (
                'День рождения "Иван" 10 февраля. Напомнить за день, за неделю, за месяц, за 3 дня',
                [
                    TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                    TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (
                'День рождения "Иван" 10 февраля. Напомнить за месяц, за 2 недели, за неделю, за 3 дня, за день',
                [
                    TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                    TimeUnit(number=2, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (
                'День рождения "Иван" 10 февраля. Напомнить за неделю, за 3 дня, за день',
                [
                    TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (
                'День рождения "Иван" 10 февраля. Напомнить за 3 дня, за день',
                [
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            (
                'День рождения "Иван" 10 февраля. Напомнить за 2 дня',
                [TimeUnit(number=2, unit=TimeUnitEnum.DAY)],
            ),
            (
                'День рождения "Иван" 10 февраля. Напомнить за день',
                [TimeUnit(number=1, unit=TimeUnitEnum.DAY)],
            ),
            (
                'День рождения "Иван" 10 февраля. Напомнить за неделю, за 2 дня, '
                'за 7 дней, за 3 дня, за 2 дня, за день',
                [
                    TimeUnit(number=7, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=2, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
            ('День рождения "Иван" 10 февраля', []),
            ('День рождения "Иван" 10 февраля.', []),
        ]:
            with self.subTest(command=command, units=units):
                result = parse_command(command, self.now, self.default)
                self.assertEqual(result.repeat_before, units)

    def test_invalid_input(self):
        with self.assertRaises(ParserException):
            parse_command("Некорректная команда", self.now, self.default)


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
