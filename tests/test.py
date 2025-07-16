#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import unittest

# TODO:
from datetime import datetime

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
    def get_test_data(cls) -> list[tuple[list[str], TimeUnit]]:
        return [
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
        ]

    def test_parse_text(self):
        for text_list, unit in self.get_test_data():
            with self.subTest(text_list=text_list, unit=unit):
                for text in text_list:
                    self.assertEqual(unit, TimeUnit.parse_text(text))

    def test_parse_value(self):
        for _, unit in self.get_test_data():
            with self.subTest(unit=unit):
                value = unit.get_value()
                self.assertEqual(unit, TimeUnit.parse_value(value))

    def test_get_value(self):
        1 / 0

    def test_get_prev_datetime(self):
        1 / 0

    def test_get_next_datetime(self):
        1 / 0

    def test_get_timedelta(self):
        1 / 0


class TestCaseTimeUnitWeekDayUnit(unittest.TestCase):
    def test_parse_text(self):
        1 / 0

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
        1 / 0

    def test_parse_value(self):
        1 / 0

    def test_get_value(self):
        1 / 0

    def test_get_next_datetime(self):
        1 / 0


if __name__ == "__main__":
    unittest.main()
