#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from datetime import datetime
from unittest import TestCase

from common import datetime_to_str, prepare_text


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
