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
from db import Reminder, Chat, User
from utils import ParseResult, parse_command, get_pretty_datetime
from third_party.get_tz_from_offset__zoneinfo import get_tz as get_tz_from_offset


def datetime_to_str(dt: datetime) -> str:
    return f"{dt:%d.%m.%Y %H:%M:%S}"


def get_tz(value: str) -> tzinfo | None:
    try:
        return get_tz_from_offset(value)
    except Exception:
        try:
            return zoneinfo.ZoneInfo(value)
        except zoneinfo.ZoneInfoNotFoundError:
            return


def convert_tz(dt: datetime, from_tz: tzinfo, to_tz: tzinfo) -> datetime:
    return (
        dt.replace(tzinfo=from_tz)  # Указание часового пояса (дата не меняется)
        .astimezone(to_tz)  # Изменение времени и часового пояса (дата изменилась)
        .replace(tzinfo=None)  # Удаление часового пояса (дата не меняется)
    )


def get_context_value(context: CallbackContext) -> str | None:
    try:
        # Значение вытаскиваем из регулярки
        if context.match:
            return context.match.group(1)

        # Значение из значений команды
        return " ".join(context.args)

    except:
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
    message = update.effective_message

    context_value: str | None = get_context_value(context)
    if context_value:
        is_set: bool = True
        value: str = context_value
    else:
        is_set: bool = False
        value: str = chat.tz

    tz_chat: tzinfo | None = get_tz(value)
    if tz_chat is None:
        message.reply_text(f"Не удалось найти часовой пояс {value!r}")
        return

    if is_set:
        if chat.tz == value:
            message.reply_text(f"Часовой пояс {value!r} уже был установлен")
            return

        chat.tz = value
        chat.save()

        message.reply_text(f"Установлен часовой пояс {value!r}")
        return

    dt_utc = datetime.utcnow()
    dt = convert_tz(
        dt=dt_utc,
        from_tz=timezone.utc,
        to_tz=tz_chat,
    )

    message.reply_text(
        f"Часовой пояс {value!r}, время {datetime_to_str(dt)}\n"
        f"Время в UTC: {datetime_to_str(dt_utc)}"
    )


@log_func(log)
def on_request(update: Update, _: CallbackContext):
    chat = Chat.get_from(update.effective_chat)
    message = update.effective_message

    command = message.text
    log.debug(f"Command: {command!r}")

    parse_result: ParseResult | None = parse_command(command)
    if not parse_result:
        message.reply_text("Не получилось разобрать команду!")
        return

    tz_chat: tzinfo | None = get_tz(chat.tz)
    if tz_chat is None:
        message.reply_text(f"Не удалось найти часовой пояс {chat.tz!r}")
        return

    # Время в часовом поясе пользователя
    finish_time = parse_result.target_datetime

    finish_time_utc = convert_tz(
        dt=finish_time,
        from_tz=tz_chat,
        to_tz=timezone.utc,
    )
    Reminder.add(
        original_message_id=message.message_id,
        original_message_text=message.text,
        target_datetime_utc=finish_time_utc,
        user=User.get_from(update.effective_user),
        chat=Chat.get_from(update.effective_chat),
    )

    message.reply_text(
        f"Напоминание установлено на {get_pretty_datetime(finish_time)}"
        f" (в UTC {get_pretty_datetime(finish_time_utc)})"
    )


@log_func(log)
def on_get_reminders(update: Update, _: CallbackContext):
    message = update.effective_message
    chat = Chat.get_from(update.effective_chat)

    tz_chat: tzinfo | None = get_tz(chat.tz)
    if tz_chat is None:
        message.reply_text(f"Не удалось найти часовой пояс {chat.tz!r}")
        return

    query = (
        Reminder.select()
        .where(
            (Reminder.chat_id == chat.id)
            & (Reminder.user_id == update.effective_user.id)
            & (Reminder.is_sent == False)
        )
        .order_by(Reminder.target_datetime_utc)
    )

    number = query.count()

    if number:
        # TODO: Пагинация
        text = f"Напоминаний ({number}):\n"
        for x in query:
            target_datetime = convert_tz(
                dt=x.target_datetime_utc,
                from_tz=timezone.utc,
                to_tz=tz_chat,
            )
            text += (
                f"    {get_pretty_datetime(target_datetime)} "
                f"(в UTC {get_pretty_datetime(x.target_datetime_utc)})\n"
            )
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
