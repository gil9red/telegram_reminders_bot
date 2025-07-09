#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import os
import time

from datetime import datetime
from threading import Thread
from typing import Any

from telegram import Bot, Message
from telegram.ext import Updater, Defaults
from telegram.error import BadRequest

import commands
from common import datetime_to_str, log
from config import TOKEN
from db import Reminder


DATA: dict[str, Any] = {
    "BOT": None,
}


def process_check_reminders(bot: Bot):
    now = datetime.utcnow()

    query = (
        Reminder.select()
        .where(now >= Reminder.next_send_datetime_utc)
        .order_by(Reminder.next_send_datetime_utc)
    )

    for reminder in query:
        log.info("Send reminder: %s", reminder)

        # Отправка уведомления
        # Планирование следующей отправки
        try:
            has_next: bool = reminder.process_next_notify(now)

            next_send_datetime_utc = reminder.next_send_datetime_utc
            next_send_datetime = reminder.get_next_send_datetime()

            lines: list[str] = [f"⌛ {reminder.target}"]
            if has_next:
                lines.append(
                    f"Следующее: {datetime_to_str(next_send_datetime)} "
                    f"(в UTC {datetime_to_str(next_send_datetime_utc)})"
                )
            text: str = "\n".join(lines)

            reply_to_message_id: int | None = reminder.get_reply_to_message_id()
            while True:
                try:
                    rs: Message = bot.send_message(
                        chat_id=reminder.chat_id,
                        text=text,
                        reply_to_message_id=reply_to_message_id,
                    )
                    reminder.last_send_message_id = rs.message_id
                    reminder.last_send_datetime_utc = datetime.utcnow()

                    break

                except BadRequest as e:
                    if "Message to be replied not found" in str(e):
                        reply_to_message_id = None
                        continue

                    raise e

            reminder.save()

        except:
            log.exception("")

        finally:
            time.sleep(1)


def do_checking_reminders():
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


def main():
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
