#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import os
import time

from threading import Thread
from typing import Any

from telegram import Bot, Message
from telegram.ext import Updater, Defaults
from telegram.error import BadRequest, Unauthorized

from telegram_reminders_bot import commands
from telegram_reminders_bot.common import (
    datetimes_pair_to_str,
    prepare_text,
    log,
    get_utc_naive_now,
)
from telegram_reminders_bot.config import TOKEN
from telegram_reminders_bot.db import Reminder

DATA: dict[str, Any] = {
    "BOT": None,
}


def process_check_reminders(bot: Bot):
    now_utc = get_utc_naive_now()

    query = (
        Reminder.select()
        .where(now_utc >= Reminder.next_send_datetime_utc)
        .order_by(Reminder.next_send_datetime_utc)
    )

    for reminder in query:
        log.info("Send reminder: %s", reminder)

        # Отправка уведомления
        # Планирование следующей отправки
        try:
            target_datetime_str: str = datetimes_pair_to_str(
                reminder.get_target_datetime(), reminder.target_datetime_utc
            )
            lines: list[str] = [
                f"🎯 {reminder.target}",
                "",
                f"📅 Целевая дата: {target_datetime_str}",
            ]

            has_next: bool = reminder.process_next_notify(now_utc)
            if has_next:
                next_send_datetime_str: str = datetimes_pair_to_str(
                    reminder.get_next_send_datetime(), reminder.next_send_datetime_utc
                )
                lines.append(f"🚀 Следующее: {next_send_datetime_str}")

            text: str = prepare_text("\n".join(lines))

            reply_to_message_id: int | None = reminder.get_reply_to_message_id()
            while True:
                try:
                    rs: Message = bot.send_message(
                        chat_id=reminder.chat_id,
                        text=text,
                        reply_to_message_id=reply_to_message_id,
                    )
                    reminder.last_send_message_id = rs.message_id
                    reminder.last_send_datetime_utc = get_utc_naive_now()
                    reminder.save()

                    break

                except BadRequest as e:
                    if "Message to be replied not found" in str(e):
                        reply_to_message_id = None
                        continue

                    raise e

                except Unauthorized:
                    log.exception(
                        f"Нет доступа к чату #{reminder.chat_id}. Напоминание будет удалено"
                    )
                    reminder.delete_instance()
                    break

        except:
            log.exception("")

        finally:
            time.sleep(1)


def do_checking_reminders() -> None:
    while True:
        bot: Bot | None = DATA["BOT"]
        if not bot:
            time.sleep(0.001)
            continue

        try:
            process_check_reminders(bot)
        except:
            log.exception("")
        finally:
            time.sleep(1)


def main() -> None:
    log.debug("Start")

    cpu_count = os.cpu_count()
    workers = cpu_count
    log.debug(f"System: CPU_COUNT={cpu_count}, WORKERS={workers}")

    updater = Updater(
        TOKEN,
        workers=workers,
        defaults=Defaults(run_async=True),
    )
    bot = updater.bot
    log.debug(f"Bot name {bot.first_name!r} ({bot.name})")

    DATA["BOT"] = bot

    dp = updater.dispatcher
    commands.setup(dp)

    updater.start_polling()
    updater.idle()

    log.debug("Finish")


if __name__ == "__main__":
    Thread(target=do_checking_reminders).start()

    while True:
        try:
            main()
        except:
            log.exception("")

            timeout = 15
            log.info(f"Restarting the bot after {timeout} seconds")
            time.sleep(timeout)
