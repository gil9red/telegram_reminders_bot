#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import unittest

# TODO:
from datetime import datetime, timedelta

from peewee import SqliteDatabase

from db import (
    BaseModel,
    # TODO:
    Reminder,
    db,
)
from parser import (
    TimeUnitEnum,
    TimeUnitWeekDayEnum,
    RepeatEvery,
    TimeUnit,
    TimeUnitWeekDayUnit,
)


# NOTE: https://docs.peewee-orm.com/en/latest/peewee/database.html#testing-peewee-applications
class TestCaseDb(unittest.TestCase):
    def setUp(self):
        self.models = BaseModel.get_inherited_models()
        self.test_db = SqliteDatabase(":memory:")
        self.test_db.bind(self.models, bind_refs=False, bind_backrefs=False)
        self.test_db.connect()
        self.test_db.create_tables(self.models)

    def tearDown(self):
        db.bind(self.models, bind_refs=False, bind_backrefs=False)

    def test_TODO(self):
        # TODO:
        pass


# TODO:
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
        for text_list, unit in [
            (
                ["год", "года"],
                TimeUnit(number=1, unit=TimeUnitEnum.YEAR),
            ),
            (
                ["полгода"],
                TimeUnit(number=6, unit=TimeUnitEnum.MONTH),
            ),
            (
                ["месяц", "месяца", "месяцев"],
                TimeUnit(number=1, unit=TimeUnitEnum.MONTH),
            ),
            (
                ["неделю", "недели", "недель"],
                TimeUnit(number=1, unit=TimeUnitEnum.WEEK),
            ),
            (
                ["день", "дня", "дней"],
                TimeUnit(number=1, unit=TimeUnitEnum.DAY),
            ),
        ]:
            with self.subTest(text_list=text_list, unit=unit):
                for text in text_list:
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


class TestCaseTimeUnitWeekDayUnit(unittest.TestCase):
    def test_parse_text(self):
        for text, unit in [
            (
                "понедельник",
                TimeUnitWeekDayUnit(unit=TimeUnitWeekDayEnum.MONDAY),
            ),
            (
                "вторник",
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
        ]:
            with self.subTest(text=text, unit=unit):
                self.assertEqual(unit, TimeUnitWeekDayUnit.parse_text(text))

    def test_parse_value(self):
        1 / 0

    def test_get_value(self):
        1 / 0

    def test_get_next_datetime(self):
        1 / 0


# TODO:
class TestCaseParserRepeatEvery(unittest.TestCase):
    def test_get_unit_classes(self):
        self.assertEqual(
            [TimeUnit, TimeUnitWeekDayUnit], RepeatEvery.get_unit_classes()
        )

    def test_parse_text(self):
        # TODO: Все варианты
        for text in ["месяц", "четверг"]:
            with self.subTest(text=text):
                repeat_every_month = RepeatEvery.parse_text(text)
                self.assertIsNotNone(repeat_every_month)

        # TODO: Вариант с невалидным

    def test_parse_value(self):
        1 / 0

    def test_get_value(self):
        1 / 0

    def test_get_next_datetime(self):
        1 / 0


if __name__ == "__main__":
    unittest.main()
