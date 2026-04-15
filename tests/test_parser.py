#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import unittest
from datetime import datetime, timedelta

from src.telegram_reminders_bot.parser import (
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
    get_nearest_datetime,
)


class TestCaseParserCommon(unittest.TestCase):
    def test_TimeUnitEnum_days(self) -> None:
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

    def test_TimeUnitWeekDayEnum(self) -> None:
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

    def test_ParseResult(self) -> None:
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

    def test_Defaults(self) -> None:
        defaults = Defaults(hours=10, minutes=30)
        self.assertEqual(10, defaults.hours)
        self.assertEqual(30, defaults.minutes)

    def test_get_repeat_every(self) -> None:
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

    def test_parse_repeat_before(self) -> None:
        for text, units in [
            (
                "Напомнить за 3 года, за год, за полгода, за 3 месяца, за месяц, за 10 дней, за неделю, за 3 дня, за день",
                [
                    TimeUnit(number=3, unit=TimeUnitEnum.YEAR),
                    TimeUnit(number=1, unit=TimeUnitEnum.YEAR),
                    TimeUnit(number=6, unit=TimeUnitEnum.MONTH),
                    TimeUnit(number=3, unit=TimeUnitEnum.MONTH),
                    TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                    TimeUnit(number=10, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                    TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                    TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                ],
            ),
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

    def test_parse_month(self) -> None:
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

    def test_get_nearest_datetime(self) -> None:
        now: datetime = datetime(year=2025, month=8, day=9, hour=22, minute=0)
        target_dt: datetime = datetime(year=2026, month=1, day=10, hour=10, minute=0)

        with self.subTest(msg="ParserException"):
            with self.assertRaises(ParserException):
                get_nearest_datetime(dt=now, target_dt=now, repeat_before=[])

            with self.assertRaises(ParserException):
                get_nearest_datetime(
                    dt=now, target_dt=now - timedelta(seconds=1), repeat_before=[]
                )

            with self.assertRaises(ParserException):
                get_nearest_datetime(dt=target_dt, target_dt=now, repeat_before=[])

        with self.subTest(msg="Ok"):
            self.assertEqual(
                target_dt,
                get_nearest_datetime(dt=now, target_dt=target_dt, repeat_before=[]),
            )

            self.assertEqual(
                target_dt,
                get_nearest_datetime(
                    dt=now,
                    target_dt=target_dt,
                    repeat_before=[TimeUnit(number=1, unit=TimeUnitEnum.YEAR)],
                ),
            )
            self.assertEqual(
                target_dt,
                get_nearest_datetime(
                    dt=now,
                    target_dt=target_dt,
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.YEAR),
                        TimeUnit(number=6, unit=TimeUnitEnum.MONTH),
                    ],
                ),
            )

            self.assertEqual(
                target_dt - TimeUnit(number=1, unit=TimeUnitEnum.DAY).get_timedelta(),
                get_nearest_datetime(
                    dt=now,
                    target_dt=target_dt,
                    repeat_before=[TimeUnit(number=1, unit=TimeUnitEnum.DAY)],
                ),
            )
            self.assertEqual(
                target_dt - TimeUnit(number=2, unit=TimeUnitEnum.WEEK).get_timedelta(),
                get_nearest_datetime(
                    dt=now,
                    target_dt=target_dt,
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=2, unit=TimeUnitEnum.WEEK),
                    ],
                ),
            )
            self.assertEqual(
                target_dt - TimeUnit(number=3, unit=TimeUnitEnum.MONTH).get_timedelta(),
                get_nearest_datetime(
                    dt=now,
                    target_dt=target_dt,
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=2, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=3, unit=TimeUnitEnum.MONTH),
                    ],
                ),
            )

            self.assertEqual(
                target_dt - TimeUnit(number=3, unit=TimeUnitEnum.MONTH).get_timedelta(),
                get_nearest_datetime(
                    dt=now,
                    target_dt=target_dt,
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=2, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=3, unit=TimeUnitEnum.MONTH),
                        # NOTE: 6 месяцев и 1 год уже будут меньше now
                        TimeUnit(number=6, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=1, unit=TimeUnitEnum.YEAR),
                    ],
                ),
            )


class TestCaseParseCommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.now: datetime = datetime(year=2025, month=8, day=9, hour=22, minute=0)
        cls.defaults: Defaults = Defaults(hours=11, minutes=0)

    def assert_parse_result(self, command: str, result: ParseResult) -> None:
        actual_result = parse_command(command, self.now, self.defaults)
        self.assertEqual(result.target, actual_result.target)
        self.assertEqual(result.target_datetime, actual_result.target_datetime)
        self.assertEqual(result.repeat_before, actual_result.repeat_before)
        self.assertEqual(result.repeat_every, actual_result.repeat_every)
        self.assertEqual(result, actual_result)

    def test_parse_absolute_date(self) -> None:
        for command, result in [
            (
                'Напомни о "🍕" 10 февраля',
                ParseResult(
                    target="🍕",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Звонок другу" 29 декабря',
                ParseResult(
                    target="Звонок другу",
                    target_datetime=datetime(
                        2025, 12, 29, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                '"Звонок другу" 29 декабря',
                ParseResult(
                    target="Звонок другу",
                    target_datetime=datetime(
                        2025, 12, 29, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
        ]:
            with self.subTest(command=command):
                self.assert_parse_result(command, result)

    def test_parse_absolute_date_with_time(self) -> None:
        for command, result in [
            (
                'Напомни о "ДНС" 10 февраля в 14:55',
                ParseResult(
                    target="ДНС",
                    target_datetime=datetime(2026, 2, 10, 14, 55),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "ДНС" 10 февраля в 03:30',
                ParseResult(
                    target="ДНС",
                    target_datetime=datetime(2026, 2, 10, 3, 30),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
        ]:
            with self.subTest(command=command):
                self.assert_parse_result(command, result)

    def test_parse_relative_today(self) -> None:
        for command, result in [
            (
                'Напомни о "Покупки" сегодня',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" завтра',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" послезавтра',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 11, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Встреча "Колян" сегодня',
                ParseResult(
                    target="Колян",
                    target_datetime=datetime(
                        2025, 8, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                '"Встреча с Коляном" сегодня',
                ParseResult(
                    target="Встреча с Коляном",
                    target_datetime=datetime(
                        2025, 8, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
        ]:
            with self.subTest(command=command):
                self.assert_parse_result(command, result)

    def test_parse_relative_today_with_time(self) -> None:
        for command, result in [
            (
                'Напомни о "Покупки" сегодня в 18:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 10, 18, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" завтра в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 10, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" послезавтра в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 11, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Встреча "Колян" сегодня в 19:45',
                ParseResult(
                    target="Колян",
                    target_datetime=datetime(2025, 8, 10, 19, 45),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                '"Встреча с Коляном" сегодня в 19:45',
                ParseResult(
                    target="Встреча с Коляном",
                    target_datetime=datetime(2025, 8, 10, 19, 45),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
        ]:
            with self.subTest(command=command):
                self.assert_parse_result(command, result)

    def test_parse_relative_next_weekday(self) -> None:
        for command, result in [
            (
                'Напомни о "Покупки" в следующий понедельник',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 11, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" в следующий вторник',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 12, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" в следующую среду',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 13, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" в следующий четверг',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 14, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" в следующую пятницу',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 15, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" в следующую субботу',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 16, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" в следующее воскресенье',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Встреча "Колян" в понедельник',
                ParseResult(
                    target="Колян",
                    target_datetime=datetime(
                        2025, 8, 11, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Встреча "Колян" в пятницу',
                ParseResult(
                    target="Колян",
                    target_datetime=datetime(
                        2025, 8, 15, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                '"Колян" в пятницу',
                ParseResult(
                    target="Колян",
                    target_datetime=datetime(
                        2025, 8, 15, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
        ]:
            with self.subTest(command=command):
                self.assert_parse_result(command, result)

    def test_parse_relative_next_weekday_with_time(self) -> None:
        for command, result in [
            (
                'Напомни о "Покупки" в следующий понедельник в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 11, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" в следующий вторник в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 12, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" в следующую среду в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 13, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" в следующий четверг в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 14, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" в следующую пятницу в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 15, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" в следующую субботу в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 16, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" в следующее воскресенье в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 10, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Встреча "Колян" в понедельник в 19:45',
                ParseResult(
                    target="Колян",
                    target_datetime=datetime(2025, 8, 11, 19, 45),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Встреча "Колян" в пятницу в 19:45',
                ParseResult(
                    target="Колян",
                    target_datetime=datetime(2025, 8, 15, 19, 45),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                '"Колян" в пятницу в 19:45',
                ParseResult(
                    target="Колян",
                    target_datetime=datetime(2025, 8, 15, 19, 45),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
        ]:
            with self.subTest(command=command):
                self.assert_parse_result(command, result)

    def test_parse_relative_days_with_time(self) -> None:
        for command, result in [
            (
                'Напомни о "Покупки" через 1 день в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 10, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через день в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 10, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 2 дня в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 11, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 3 дня в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 12, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 4 дня в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 13, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 5 дней в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 14, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 6 дней в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 15, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 7 дней в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 16, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 10 дней в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 8, 19, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 50 дней в 12:00',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(2025, 9, 28, 12, 0),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
        ]:
            with self.subTest(command=command):
                self.assert_parse_result(command, result)

    def test_parse_relative_days(self) -> None:
        for command, result in [
            (
                'Напомни о "Покупки" через 1 день',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через день',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 2 дня',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 11, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 3 дня',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 12, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 4 дня',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 13, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 5 дней',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 14, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 6 дней',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 15, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 7 дней',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 16, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 10 дней',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 8, 19, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Покупки" через 50 дней',
                ParseResult(
                    target="Покупки",
                    target_datetime=datetime(
                        2025, 9, 28, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[],
                ),
            ),
        ]:
            with self.subTest(command=command):
                self.assert_parse_result(command, result)

    def test_parse_defaults(self) -> None:
        command = 'Напомни о "Встреча" 10 февраля'
        result = parse_command(
            command, self.now, defaults=Defaults(hours=14, minutes=55)
        )
        self.assertEqual(result.target_datetime.hour, 14)
        self.assertEqual(result.target_datetime.minute, 55)

    def test_parse_with_repeat_every(self) -> None:
        for command, result in [
            (
                'Напомни о "Чатик 🍕" 17 июля в 12:00. Повтор каждый понедельник',
                ParseResult(
                    target="Чатик 🍕",
                    target_datetime=datetime(2026, 7, 17, 12, 0),
                    repeat_every=RepeatEvery(
                        unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.MONDAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Чатик 🍕" 17 июля в 12:00. Повтор каждый вторник',
                ParseResult(
                    target="Чатик 🍕",
                    target_datetime=datetime(2026, 7, 17, 12, 0),
                    repeat_every=RepeatEvery(
                        unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.TUESDAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Чатик 🍕" 17 июля в 12:00. Повтор каждую среду',
                ParseResult(
                    target="Чатик 🍕",
                    target_datetime=datetime(2026, 7, 17, 12, 0),
                    repeat_every=RepeatEvery(
                        unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.WEDNESDAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Чатик 🍕" 17 июля в 12:00. Повтор каждый четверг',
                ParseResult(
                    target="Чатик 🍕",
                    target_datetime=datetime(2026, 7, 17, 12, 0),
                    repeat_every=RepeatEvery(
                        unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.THURSDAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Чатик 🍕" 17 июля в 12:00. Повтор каждую пятницу',
                ParseResult(
                    target="Чатик 🍕",
                    target_datetime=datetime(2026, 7, 17, 12, 0),
                    repeat_every=RepeatEvery(
                        unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.FRIDAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Чатик 🍕" 17 июля в 12:00. Повтор каждую субботу',
                ParseResult(
                    target="Чатик 🍕",
                    target_datetime=datetime(2026, 7, 17, 12, 0),
                    repeat_every=RepeatEvery(
                        unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SATURDAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "Чатик 🍕" 17 июля в 12:00. Повтор каждое воскресенье',
                ParseResult(
                    target="Чатик 🍕",
                    target_datetime=datetime(2026, 7, 17, 12, 0),
                    repeat_every=RepeatEvery(
                        unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.SUNDAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "🍕" в следующий четверг в 12:00. Повтор каждый четверг',
                ParseResult(
                    target="🍕",
                    target_datetime=datetime(2025, 8, 14, 12, 0),
                    repeat_every=RepeatEvery(
                        unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.THURSDAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Напомни о "🍕" в четверг в 12:00. Повтор каждый четверг',
                ParseResult(
                    target="🍕",
                    target_datetime=datetime(2025, 8, 14, 12, 0),
                    repeat_every=RepeatEvery(
                        unit=TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.THURSDAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'День рождения "123" 10 февраля. Повтор каждый день',
                ParseResult(
                    target="123",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.DAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'День рождения "-_-" 10 февраля в 14:55. Повтор каждый день',
                ParseResult(
                    target="-_-",
                    target_datetime=datetime(2026, 2, 10, 14, 55),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.DAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'День рождения "abc" 10 февраля 2027 года. Повтор каждый день',
                ParseResult(
                    target="abc",
                    target_datetime=datetime(
                        2027, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.DAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'День рождения "xxx" 10 февраля 2027 года в 14:55. Повтор каждый день',
                ParseResult(
                    target="xxx",
                    target_datetime=datetime(2027, 2, 10, 14, 55),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.DAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'День рождения "xxx" 10 февраля 2027 года в 14:55. Повтор каждые 4 дня',
                ParseResult(
                    target="xxx",
                    target_datetime=datetime(2027, 2, 10, 14, 55),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=4, unit=TimeUnitEnum.DAY)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Праздник "xxx" 10 февраля. Повтор каждую неделю',
                ParseResult(
                    target="xxx",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.WEEK)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Праздник "xxx" 10 февраля. Повтор каждые 2 недели',
                ParseResult(
                    target="xxx",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=2, unit=TimeUnitEnum.WEEK)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Праздник "xxx" 10 февраля. Повтор каждый месяц',
                ParseResult(
                    target="xxx",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.MONTH)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Праздник "xxx" 10 февраля. Повтор каждый 3 месяца',
                ParseResult(
                    target="xxx",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=3, unit=TimeUnitEnum.MONTH)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Праздник "xxx" 10 февраля. Повтор каждый год',
                ParseResult(
                    target="xxx",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.YEAR)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'Праздник "xxx" 10 февраля 2026 года. Повтор каждый год',
                ParseResult(
                    target="xxx",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.YEAR)
                    ),
                    repeat_before=[],
                ),
            ),
            (
                'День рождения "^_^" 10 февраля. Повтор раз в год. Напомнить за месяц, за неделю, за 3 дня, за день',
                ParseResult(
                    target="^_^",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.YEAR)
                    ),
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'День рождения "День рождения Ивана" 10 февраля. Повтор раз в полгода. Напомнить за месяц, за неделю, за 3 дня, за день',
                ParseResult(
                    target="День рождения Ивана",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=6, unit=TimeUnitEnum.MONTH)
                    ),
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'День рождения "!!!" 10 февраля. Повтор раз в месяц. Напомнить за месяц, за 2 недели, за неделю, за 3 дня, за день',
                ParseResult(
                    target="!!!",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.MONTH)
                    ),
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=2, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'День рождения "***" 10 февраля. Повтор раз в неделю. Напомнить за месяц, за неделю, за 3 дня, за день',
                ParseResult(
                    target="***",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.WEEK)
                    ),
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'Напомни о "🍕" 10 февраля. Повтор раз в год. Напомнить за месяц, за неделю, за 3 дня, за день',
                ParseResult(
                    target="🍕",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.YEAR)
                    ),
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'Напомни о "???" 12 июля в 17:55. Напомни за неделю, за 3 дня, за 2 дня, за 1 день',
                ParseResult(
                    target="???",
                    target_datetime=datetime(2026, 7, 12, 17, 55),
                    repeat_every=None,
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=2, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                '"???" 12 июля в 17:55. Напомни за неделю, за 3 дня, за 2 дня, за 1 день',
                ParseResult(
                    target="???",
                    target_datetime=datetime(2026, 7, 12, 17, 55),
                    repeat_every=None,
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=2, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
        ]:
            with self.subTest(command=command):
                self.assert_parse_result(command, result)

    def test_parse_with_repeat_before(self) -> None:
        for command, result in [
            (
                'День рождения "Поход" 10 февраля. Повтор раз в год. Напомнить за месяц, за неделю, за 3 дня, за день',
                ParseResult(
                    target="Поход",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.YEAR)
                    ),
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'День рождения "День рождения Ивана" 10 февраля. Повтор раз в полгода. Напомнить за месяц, за неделю, за 3 дня, за день',
                ParseResult(
                    target="День рождения Ивана",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=6, unit=TimeUnitEnum.MONTH)
                    ),
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'День рождения "!!!" 10 февраля. Повтор раз в месяц. Напомнить за месяц, за 2 недели, за неделю, за 3 дня, за день',
                ParseResult(
                    target="!!!",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.MONTH)
                    ),
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=2, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'День рождения "***" 10 февраля. Повтор раз в неделю. Напомнить за месяц, за неделю, за 3 дня, за день',
                ParseResult(
                    target="***",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.WEEK)
                    ),
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'Напомни о "🍕" 10 февраля. Повтор раз в год. Напомнить за месяц, за неделю, за 3 дня, за день',
                ParseResult(
                    target="🍕",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=RepeatEvery(
                        unit=TimeUnit(number=1, unit=TimeUnitEnum.YEAR)
                    ),
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'Напомни о "🍕" 10 февраля. Напомнить за 3 года, за год, за полгода, за 3 месяца, за месяц, за 10 дней, за неделю, за 3 дня, за день',
                ParseResult(
                    target="🍕",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[
                        TimeUnit(number=3, unit=TimeUnitEnum.YEAR),
                        TimeUnit(number=1, unit=TimeUnitEnum.YEAR),
                        TimeUnit(number=6, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=3, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=10, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'Напомни о "🍕" 10 февраля. Напомнить за неделю, за 3 дня, за день',
                ParseResult(
                    target="🍕",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'Напомни о "🍕" 10 февраля. Напомнить за 3 дня, за день',
                ParseResult(
                    target="🍕",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'День рождения "xxx" 10 февраля. Напомнить за месяц, за неделю, за 3 дня, за день',
                ParseResult(
                    target="xxx",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'День рождения "xxx" 10 февраля. Напомнить за день, за неделю, за месяц, за 3 дня',
                ParseResult(
                    target="xxx",
                    target_datetime=datetime(
                        2026, 2, 10, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[
                        TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
                        TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                'Напомни о "Звонок другу" 29 декабря. Напомнить за неделю, за 2 дня, за 7 дней, за 3 дня, за 2 дня, за день',
                ParseResult(
                    target="Звонок другу",
                    target_datetime=datetime(
                        2025, 12, 29, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[
                        TimeUnit(number=7, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=2, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
            (
                '"Звонок другу" 29 декабря. Напомнить за неделю, за 2 дня, за 7 дней, за 3 дня, за 2 дня, за день',
                ParseResult(
                    target="Звонок другу",
                    target_datetime=datetime(
                        2025, 12, 29, self.defaults.hours, self.defaults.minutes
                    ),
                    repeat_every=None,
                    repeat_before=[
                        TimeUnit(number=7, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=3, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=2, unit=TimeUnitEnum.DAY),
                        TimeUnit(number=1, unit=TimeUnitEnum.DAY),
                    ],
                ),
            ),
        ]:
            with self.subTest(command=command):
                self.assert_parse_result(command, result)

    def test_invalid_input(self) -> None:
        with self.assertRaises(ParserException):
            parse_command("Некорректная команда", self.now, self.defaults)


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

    def test_parse_text(self) -> None:
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

    def test_parse_value(self) -> None:
        for _, unit in self.get_test_data():
            with self.subTest(unit=unit):
                value = unit.get_value()
                self.assertEqual(unit, TimeUnit.parse_value(value))

    def test_get_value(self) -> None:
        for value, unit in self.get_test_data():
            with self.subTest(value=value, unit=unit):
                self.assertEqual(value, unit.get_value())

    def test_get_prev_datetime(self) -> None:
        dt = datetime(year=2020, month=1, day=1, hour=10, minute=0, second=0)

        for _, unit in self.get_test_data():
            with self.subTest(unit=unit):
                self.assertEqual(dt - unit.get_timedelta(), unit.get_prev_datetime(dt))

    def test_get_next_datetime(self) -> None:
        dt = datetime(year=2020, month=1, day=1, hour=10, minute=0, second=0)

        for _, unit in self.get_test_data():
            with self.subTest(unit=unit):
                self.assertEqual(dt + unit.get_timedelta(), unit.get_next_datetime(dt))

    def test_get_timedelta(self) -> None:
        for _, unit in self.get_test_data():
            with self.subTest(unit=unit):
                days = unit.number * unit.unit.days()
                self.assertEqual(timedelta(days=days), unit.get_timedelta())

    def test_sorting(self) -> None:
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

    def test_parse_text(self) -> None:
        for text, unit in self.get_test_data() + [
            # Invalid
            ("None", None),
            ("", None),
            (None, None),
        ]:
            with self.subTest(text=text, unit=unit):
                self.assertEqual(unit, TimeUnitWeekDayUnit.parse_text(text))

    def test_parse_value(self) -> None:
        for _, unit in self.get_test_data():
            with self.subTest(unit=unit):
                value = unit.get_value()
                self.assertEqual(unit, TimeUnitWeekDayUnit.parse_value(value))

    def test_get_value(self) -> None:
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

    def test_get_next_datetime(self) -> None:
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

    def test_get_unit_classes(self) -> None:
        self.assertEqual(
            [TimeUnit, TimeUnitWeekDayUnit], RepeatEvery.get_unit_classes()
        )

    def test_parse_text(self) -> None:
        for values, repeat_every in self.get_test_text():
            with self.subTest(values=values, repeat_every=repeat_every):
                for text in values:
                    self.assertEqual(repeat_every, RepeatEvery.parse_text(text))

    def test_parse_value(self) -> None:
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

    def test_get_value(self) -> None:
        for value, repeat_every in self.get_test_data():
            with self.subTest(value=value, repeat_every=repeat_every):
                self.assertEqual(value, RepeatEvery.parse_value(value).get_value())

    def test_get_next_datetime_TimeUnit(self) -> None:
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
                datetime(year=2025, month=8, day=1, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.MONTH)),
            ),
            (
                datetime(year=2025, month=10, day=1, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=3, unit=TimeUnitEnum.MONTH)),
            ),
            (
                datetime(year=2025, month=12, day=1, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=5, unit=TimeUnitEnum.MONTH)),
            ),
            (
                datetime(year=2026, month=2, day=1, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=7, unit=TimeUnitEnum.MONTH)),
            ),
            (
                datetime(year=2026, month=7, day=1, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.YEAR)),
            ),
            (
                datetime(year=2027, month=7, day=1, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=2, unit=TimeUnitEnum.YEAR)),
            ),
        ]:
            with self.subTest(value=value, repeat_every=repeat_every):
                self.assertEqual(value, repeat_every.get_next_datetime(dt))

    def test_get_next_datetime_TimeUnitWeekDayUnit(self) -> None:
        dt = datetime(year=2025, month=7, day=1, hour=10, minute=0, second=0)

        for value, repeat_every in [
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

    def test_get_next_datetime_leap_year_add_month(self) -> None:
        dt = datetime(year=2024, month=1, day=29, hour=10, minute=0, second=0)

        for value, repeat_every in [
            (
                datetime(year=2024, month=2, day=29, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.MONTH)),
            ),
            (
                datetime(year=2025, month=2, day=28, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=13, unit=TimeUnitEnum.MONTH)),
            ),
            (
                datetime(year=2028, month=2, day=29, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=49, unit=TimeUnitEnum.MONTH)),
            ),
        ]:
            with self.subTest(value=value, repeat_every=repeat_every):
                self.assertEqual(value, repeat_every.get_next_datetime(dt))

    def test_get_next_datetime_leap_year_add_year(self) -> None:
        dt = datetime(year=2024, month=2, day=29, hour=10, minute=0, second=0)

        for value, repeat_every in [
            (
                datetime(year=2025, month=2, day=28, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=1, unit=TimeUnitEnum.YEAR)),
            ),
            (
                datetime(year=2026, month=2, day=28, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=2, unit=TimeUnitEnum.YEAR)),
            ),
            (
                datetime(year=2027, month=2, day=28, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=3, unit=TimeUnitEnum.YEAR)),
            ),
            (
                datetime(year=2028, month=2, day=29, hour=10, minute=0, second=0),
                RepeatEvery(unit=TimeUnit(number=4, unit=TimeUnitEnum.YEAR)),
            ),
        ]:
            with self.subTest(value=value, repeat_every=repeat_every):
                self.assertEqual(value, repeat_every.get_next_datetime(dt))


if __name__ == "__main__":
    unittest.main()
