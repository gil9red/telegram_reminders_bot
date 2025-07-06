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
# TODO:
# from utils import ParseResult, parse_command, get_pretty_datetime
from parser import ParseResult, Defaults, parse_command
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
    # TODO: Обновить примеры команд
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

    now = datetime.utcnow()
    default = Defaults(hours=10, minutes=0)

    parse_result: ParseResult | None = parse_command(command, dt=now, default=default)
    if not parse_result:
        message.reply_text("Не получилось разобрать команду!")
        return

    tz_chat: tzinfo | None = get_tz(chat.tz)
    if tz_chat is None:
        message.reply_text(f"Не удалось найти часовой пояс {chat.tz!r}")
        return

    # Время в часовом поясе пользователя
    target_datetime = parse_result.target_datetime

    target_datetime_utc = convert_tz(
        dt=target_datetime,
        from_tz=tz_chat,
        to_tz=timezone.utc,
    )

    # TODO: Дублирует код из do_checking_reminders
    before_dates: list[datetime] = [
        unit.get_prev_datetime(target_datetime_utc)
        for unit in parse_result.repeat_before
    ]
    before_dates.append(target_datetime_utc)

    next_dates: list[datetime] = [d for d in before_dates if d > now]

    next_send_datetime_utc = min(next_dates)

    # TODO: Проверка на дубликат команды
    Reminder.add(
        original_message_id=message.message_id,
        original_message_text=message.text,
        target=parse_result.target,
        target_datetime_utc=target_datetime_utc,
        next_send_datetime_utc=next_send_datetime_utc,
        repeat_every=parse_result.repeat_every,
        repeat_before=parse_result.repeat_before,
        user=User.get_from(update.effective_user),
        chat=Chat.get_from(update.effective_chat),
    )

    next_send_datetime = convert_tz(
        dt=next_send_datetime_utc,
        from_tz=timezone.utc,
        to_tz=tz_chat,
    )

    lines: list[str] = [
        f"Напоминание установлено на {datetime_to_str(target_datetime)}"
        f" (в UTC {datetime_to_str(target_datetime_utc)})",
        f"Ближайшее: {datetime_to_str(next_send_datetime)} (в UTC {datetime_to_str(next_send_datetime_utc)})",
        f"Повтор: {parse_result.repeat_every.get_value() if parse_result.repeat_every else 'нет'}",
    ]

    if not parse_result.repeat_before:
        lines.append("Без напоминаний")
    else:
        lines.append("Напоминаний:")

        for time_unit in parse_result.repeat_before:
            prev_dt = time_unit.get_prev_datetime(parse_result.target_datetime)
            prev_dt_utc = convert_tz(
                dt=prev_dt,
                from_tz=tz_chat,
                to_tz=timezone.utc,
            )
            lines.append(
                f"    {time_unit.get_value()}: {prev_dt} (в UTC {datetime_to_str(prev_dt_utc)})"
            )

    message.reply_text("\n".join(lines))


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
            & (Reminder.is_active == True)
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
            next_send_datetime = convert_tz(
                dt=x.next_send_datetime_utc,
                from_tz=timezone.utc,
                to_tz=tz_chat,
            )
            # TODO: Больше информации
            text += (
                f"    {datetime_to_str(target_datetime)} (в UTC {datetime_to_str(x.target_datetime_utc)})\n"
                f"        Ближайшее: {datetime_to_str(next_send_datetime)} (в UTC {datetime_to_str(x.next_send_datetime_utc)})\n\n"
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
