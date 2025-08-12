#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re

from datetime import datetime, tzinfo
from unittest import TestCase

from common import (
    datetime_to_str,
    prepare_text,
    get_int_from_match,
    get_tz,
    convert_tz,
    ZoneInfoNotFoundError,
)


class TestCaseCommon(TestCase):
    def test_datetime_to_str(self):
        now: datetime = datetime(year=2025, month=8, day=9, hour=22, minute=0)
        self.assertEqual("09.08.2025 22:00:00", datetime_to_str(now))

    def test_prepare_text(self):
        self.assertTrue(prepare_text("1234567890", max_length=6) == "123...")

        max_length: int = 4096
        text: str = "1" * max_length
        self.assertTrue(prepare_text(text, max_length=max_length) == text)

        max_length: int = 4096
        text: str = "1" * max_length * 2
        self.assertTrue(len(prepare_text(text, max_length=max_length)) == max_length)

    def test_get_int_from_match(self):
        self.assertEqual(
            123,
            get_int_from_match(
                re.search(r"(?P<number>\d+)", "123"), name="number", default=None
            ),
        )

        self.assertEqual(
            None,
            get_int_from_match(
                re.search(r"(?P<number>\d+)", "abc"), name="number", default=None
            ),
        )

        self.assertEqual(
            1,
            get_int_from_match(
                re.search(r"(?P<number>\d+)", "abc"), name="number", default=1
            ),
        )

    def test_convert_tz(self):
        dt: datetime = datetime(year=2025, month=8, day=9, hour=18, minute=0)
        tz_utc: tzinfo = get_tz("UTC")
        tz_0230: tzinfo = get_tz("+02:30")

        self.assertEqual(
            datetime(year=2025, month=8, day=9, hour=15, minute=30),
            convert_tz(
                dt=dt,
                from_tz=tz_0230,
                to_tz=tz_utc,
            ),
        )

        self.assertEqual(
            datetime(year=2025, month=8, day=9, hour=20, minute=30),
            convert_tz(
                dt=dt,
                from_tz=tz_utc,
                to_tz=tz_0230,
            ),
        )

    def test_get_tz(self):
        self.assertEqual("UTC+02:30", str(get_tz("+02:30")))
        self.assertEqual("UTC-02:30", str(get_tz("-02:30")))
        self.assertEqual("UTC", str(get_tz("UTC")))
        self.assertEqual("Europe/Moscow", str(get_tz("Europe/Moscow")))

        with self.assertRaises(ZoneInfoNotFoundError):
            get_tz("dfgsdfsdfdsf")
