#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import os
import time

from datetime import datetime, timedelta
from threading import Thread
from typing import Any

from telegram import Bot, Message
from telegram.ext import Updater, Defaults

import commands
from common import log
from config import TOKEN
from db import Reminder


DATA: dict[str, Any] = {
    "BOT": None,
}


def do_checking_reminders():
    while True:
        bot: Bot | None = DATA["BOT"]
        if not bot:
            time.sleep(0.001)
            continue

        try:
            expected_time = datetime.now() - timedelta(seconds=1)
            query = (
                Reminder.select()
                .where(
                    (Reminder.is_sent == False)
                    & (Reminder.target_time <= expected_time)
                )
                .order_by(Reminder.target_time)
            )

            for reminder in query:
                log.info("Send reminder: %s", reminder)

                # TODO: На будущее
                if reminder.last_send_message_id is not None:
                    reply_to_message_id: int = reminder.last_send_message_id
                else:
                    reply_to_message_id: int = reminder.original_message_id

                rs: Message = bot.send_message(
                    chat_id=reminder.chat_id,
                    text="⌛",
                    reply_to_message_id=reply_to_message_id,
                )

                # TODO: На будущее
                reminder.last_send_message_id = rs.message_id
                reminder.is_sent = True
                reminder.save()

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
