#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import unittest
from datetime import datetime, timezone, timedelta, time

from peewee import SqliteDatabase

from telegram_reminders_bot.common import get_tz, convert_tz
from telegram_reminders_bot.db import (
    BaseModel,
    Reminder,
    User,
    Chat,
)
from telegram_reminders_bot.parser import (
    ParseResult,
    parse_command,
    get_nearest_datetime,
)


# NOTE: https://docs.peewee-orm.com/en/latest/peewee/database.html#testing-peewee-applications
class TestCaseDb(unittest.TestCase):
    def setUp(self) -> None:
        self.models = BaseModel.get_inherited_models()
        self.test_db = SqliteDatabase(":memory:")
        self.test_db.bind(self.models, bind_refs=False, bind_backrefs=False)
        self.test_db.connect()
        self.test_db.create_tables(self.models)

    def tearDown(self) -> None:
        self.test_db.drop_tables(self.models)
        self.test_db.close()


# TODO: Другие методы
class TestCaseDbReminder(TestCaseDb):
    def test_process_next_notify(self):
        # TODO: Проверить. Должно брать из 10:00
        #       command = '"Go!" завтра. Повтор каждый день'
        command = '"Go!" сегодня в 21:00. Повтор каждый день'

        tz_str = "+05:00"
        tz = get_tz(tz_str)

        now: datetime = datetime(year=2026, month=1, day=1, hour=11, minute=0)
        now_utc = convert_tz(
            dt=now,
            from_tz=tz,
            to_tz=timezone.utc,
        )

        parse_result: ParseResult = parse_command(command, dt=now)

        target_dt: datetime = parse_result.target_datetime
        self.assertEqual(
            datetime(year=2026, month=1, day=1, hour=21, minute=0),
            target_dt,
        )

        target_time: time = time(
            hour=target_dt.hour, minute=target_dt.minute, second=target_dt.second
        )
        target_datetime_utc: datetime = convert_tz(
            dt=target_dt,
            from_tz=tz,
            to_tz=timezone.utc,
        )

        # Следующая дата отправки
        next_send_datetime_utc: datetime = get_nearest_datetime(
            target_dt=target_datetime_utc,
            repeat_before=parse_result.repeat_before,
            dt=now_utc,
        )

        reminder = Reminder.add(
            original_message_id=123,
            original_message_text=command,
            target=parse_result.target,
            target_datetime_utc=target_datetime_utc,
            next_send_datetime_utc=next_send_datetime_utc,
            repeat_every=parse_result.repeat_every,
            repeat_before=parse_result.repeat_before,
            user=User(id=1, first_name="Ivan"),
            chat=Chat(id=1, type="private", tz=tz_str),
        )

        with self.subTest(msg="Текущая дата меньше целевой"):
            reminder.target_datetime_utc = target_datetime_utc
            reminder.next_send_datetime_utc = next_send_datetime_utc

            self.assertEqual(
                target_time,
                reminder.get_target_datetime().time(),
                "Время должно совпадать с заданным в команде или используемым по-умолчанию",
            )
            prev_target_datetime = reminder.get_target_datetime()
            prev_next_send_datetime = reminder.get_next_send_datetime()
            has_next: bool = reminder.process_next_notify(now_utc=now_utc)
            self.assertTrue(has_next)
            self.assertEqual(
                target_time,
                reminder.get_target_datetime().time(),
                "Время должно совпадать с заданным в команде или используемым по-умолчанию",
            )
            self.assertEqual(prev_target_datetime, reminder.get_target_datetime())
            self.assertEqual(prev_next_send_datetime, reminder.get_next_send_datetime())

        delta: timedelta = timedelta(seconds=5)
        with self.subTest(msg=f"Текущая дата больше целевой на {delta} (текущий день)"):
            reminder.target_datetime_utc = target_datetime_utc
            reminder.next_send_datetime_utc = next_send_datetime_utc

            now_utc = reminder.next_send_datetime_utc + delta
            self.assertEqual(
                target_time,
                reminder.get_target_datetime().time(),
                "Время должно совпадать с заданным в команде или используемым по-умолчанию",
            )
            has_next: bool = reminder.process_next_notify(now_utc=now_utc)
            self.assertTrue(has_next)
            self.assertEqual(
                target_time,
                reminder.get_target_datetime().time(),
                "Время должно совпадать с заданным в команде или используемым по-умолчанию",
            )

            next_target_datetime = datetime(
                year=2026, month=1, day=2, hour=21, minute=0
            )
            next_next_send_datetime = next_target_datetime
            self.assertEqual(next_target_datetime, reminder.get_target_datetime())
            self.assertEqual(next_next_send_datetime, reminder.get_next_send_datetime())

        delta: timedelta = timedelta(hours=2, seconds=5)
        with self.subTest(msg=f"Текущая дата больше целевой на {delta} (текущий день)"):
            reminder.target_datetime_utc = target_datetime_utc
            reminder.next_send_datetime_utc = next_send_datetime_utc

            now_utc = reminder.next_send_datetime_utc + delta
            now = convert_tz(dt=now_utc, from_tz=timezone.utc, to_tz=tz)
            self.assertEqual(
                target_time,
                reminder.get_target_datetime().time(),
                "Время должно совпадать с заданным в команде или используемым по-умолчанию",
            )
            has_next: bool = reminder.process_next_notify(now_utc=now_utc)
            self.assertTrue(has_next)
            self.assertEqual(
                target_time,
                reminder.get_target_datetime().time(),
                "Время должно совпадать с заданным в команде или используемым по-умолчанию",
            )

            next_target_datetime = datetime(
                year=2026, month=1, day=2, hour=21, minute=0
            )
            next_next_send_datetime = next_target_datetime
            self.assertEqual(next_target_datetime, reminder.get_target_datetime())
            self.assertEqual(next_next_send_datetime, reminder.get_next_send_datetime())

        delta: timedelta = timedelta(hours=12)
        with self.subTest(
            msg=f"Текущая дата больше целевой на {delta} (следующий день)"
        ):
            reminder.target_datetime_utc = target_datetime_utc
            reminder.next_send_datetime_utc = next_send_datetime_utc

            now_utc = reminder.next_send_datetime_utc + delta
            now = convert_tz(dt=now_utc, from_tz=timezone.utc, to_tz=tz)
            self.assertEqual(
                target_time,
                reminder.get_target_datetime().time(),
                "Время должно совпадать с заданным в команде или используемым по-умолчанию",
            )
            has_next: bool = reminder.process_next_notify(now_utc=now_utc)
            self.assertTrue(has_next)
            self.assertEqual(
                target_time,
                reminder.get_target_datetime().time(),
                "Время должно совпадать с заданным в команде или используемым по-умолчанию",
            )

            next_target_datetime = datetime(
                year=2026, month=1, day=2, hour=21, minute=0
            )
            next_next_send_datetime = next_target_datetime
            self.assertEqual(next_target_datetime, reminder.get_target_datetime())
            self.assertEqual(next_next_send_datetime, reminder.get_next_send_datetime())

        delta: timedelta = timedelta(hours=12, seconds=5)
        with self.subTest(
            msg=f"Текущая дата больше целевой на {delta} (следующий день)"
        ):
            reminder.target_datetime_utc = target_datetime_utc
            reminder.next_send_datetime_utc = next_send_datetime_utc

            now_utc = reminder.next_send_datetime_utc + delta
            self.assertEqual(
                target_time,
                reminder.get_target_datetime().time(),
                "Время должно совпадать с заданным в команде или используемым по-умолчанию",
            )
            has_next: bool = reminder.process_next_notify(now_utc=now_utc)
            self.assertTrue(has_next)
            self.assertEqual(
                target_time,
                reminder.get_target_datetime().time(),
                "Время должно совпадать с заданным в команде или используемым по-умолчанию",
            )

            next_target_datetime = datetime(
                year=2026, month=1, day=2, hour=21, minute=0
            )
            next_next_send_datetime = next_target_datetime
            self.assertEqual(next_target_datetime, reminder.get_target_datetime())
            self.assertEqual(next_next_send_datetime, reminder.get_next_send_datetime())

        delta: timedelta = timedelta(days=7, seconds=5)
        with self.subTest(
            msg=f"Текущая дата больше целевой на {delta} (следующая неделя)"
        ):
            reminder.target_datetime_utc = target_datetime_utc
            reminder.next_send_datetime_utc = next_send_datetime_utc

            now_utc = reminder.next_send_datetime_utc + delta
            self.assertEqual(
                target_time,
                reminder.get_target_datetime().time(),
                "Время должно совпадать с заданным в команде или используемым по-умолчанию",
            )
            has_next: bool = reminder.process_next_notify(now_utc=now_utc)
            self.assertTrue(has_next)
            self.assertEqual(
                target_time,
                reminder.get_target_datetime().time(),
                "Время должно совпадать с заданным в команде или используемым по-умолчанию",
            )

            next_target_datetime = datetime(
                year=2026, month=1, day=9, hour=21, minute=0
            )
            next_next_send_datetime = next_target_datetime
            self.assertEqual(next_target_datetime, reminder.get_target_datetime())
            self.assertEqual(next_next_send_datetime, reminder.get_next_send_datetime())


if __name__ == "__main__":
    unittest.main()
