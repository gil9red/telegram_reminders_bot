#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import zoneinfo
from datetime import datetime, tzinfo, timezone

from telegram import Update
from telegram.ext import (
    CallbackContext,
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
)

from common import log_func, log
from db import Reminder, Chat
from utils import ParseResult, parse_command, get_pretty_datetime
from third_party.get_tz_from_offset__zoneinfo import get_tz as get_tz_from_offset


def datetime_to_str(dt: datetime) -> str:
    return f"{dt:%d.%m.%Y %H:%M:%S}"


def get_context_value(context: CallbackContext) -> str | None:
    try:
        # Значение вытаскиваем из регулярки
        if context.match:
            return context.match.group(1)

        # Значение из значений команды
        return " ".join(context.args)

    except:
        pass

    return


@log_func(log)
def on_start(update: Update, _: CallbackContext):
    update.effective_message.reply_markdown(
        """
Введите что-нибудь, например: `напомни через 1 час`.
Для получения списка напоминаний, напишите: `список` или /list

Чтобы бот правильно работал с датами, нужно задать свой часовой пояс.
Для установки или получения часового пояса:
- /tz - для получения
- /tz <часовой пояс в IANA или +-часы:минуты> - для установки. Например:
  - `/tz Europe/Moscow`
  - `/tz +03:00`
        """
    )


@log_func(log)
def on_tz(update: Update, context: CallbackContext):
    chat = Chat.get_from(update.effective_chat)

    context_value: str | None = get_context_value(context)
    if context_value:
        is_set: bool = True
        value: str = context_value
    else:
        is_set: bool = False
        value: str = chat.tz

    try:
        tz: tzinfo = get_tz_from_offset(value)
    except Exception:
        try:
            tz: tzinfo = zoneinfo.ZoneInfo(value)
        except zoneinfo.ZoneInfoNotFoundError:
            update.effective_message.reply_text(
                f"Не удалось найти часовой пояс {value!r}"
            )
            return

    if is_set:
        if chat.tz == value:
            update.effective_message.reply_text(
                f"Часовой пояс {value!r} уже был установлен"
            )
            return

        chat.tz = value
        chat.save()

        update.effective_message.reply_text(f"Установлен часовой пояс {value!r}")
        return

    dt_utc = datetime.utcnow()

    dt = dt_utc.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(tz)

    update.effective_message.reply_text(
        f"Часовой пояс {value!r}, время {datetime_to_str(dt)}\n"
        f"Время в UTC: {datetime_to_str(dt_utc)}"
    )


@log_func(log)
def on_request(update: Update, _: CallbackContext):
    message = update.effective_message

    command = message.text
    log.debug(f"Command: {command!r}")

    parse_result: ParseResult | None = parse_command(command)
    if not parse_result:
        message.reply_text("Не получилось разобрать команду!")
        return

    finish_time = parse_result.target_datetime
    Reminder.add(
        original_message=message,
        target_datetime=finish_time,
        user=update.effective_user,
        chat=update.effective_chat,
    )

    message.reply_text(f"Напоминание установлено на {get_pretty_datetime(finish_time)}")


@log_func(log)
def on_get_reminders(update: Update, _: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    query = (
        Reminder.select()
        .where(
            (Reminder.chat_id == chat.id)
            & (Reminder.user_id == user.id)
            & (Reminder.is_sent == False)
        )
        .order_by(Reminder.target_datetime)
    )

    number = query.count()

    if number:
        text = f"Напоминаний ({number}):\n"
        for x in query:
            text += "    " + get_pretty_datetime(x.target_datetime) + "\n"
    else:
        text = "Напоминаний нет"

    message.reply_text(text)


def setup(dp: Dispatcher):
    dp.add_handler(CommandHandler("start", on_start))
    dp.add_handler(CommandHandler("help", on_start))

    dp.add_handler(CommandHandler("tz", on_tz))

    dp.add_handler(CommandHandler("list", on_get_reminders))
    dp.add_handler(MessageHandler(Filters.regex("(?i)^Список$"), on_get_reminders))

    dp.add_handler(MessageHandler(Filters.text, on_request))
