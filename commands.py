#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
import zoneinfo
from datetime import datetime, tzinfo, timezone

from telegram import Update, InlineKeyboardButton, Bot
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
)
from telegram.error import BadRequest

from config import MESS_MAX_LENGTH
from common import log_func, log, reply_error
from db import Reminder, Chat, User

# TODO:
# from utils import ParseResult, parse_command, get_pretty_datetime
from parser import ParseResult, Defaults, TimeUnit, parse_command
from regexp_patterns import (
    COMMAND_START,
    COMMAND_HELP,
    COMMAND_TZ,
    COMMAND_LIST,
    PATTERN_LIST,
    # PATTERN_DELETE_MESSAGE,  # TODO:
    PATTERN_REMINDER_PAGE,
    fill_string_pattern,
)
from third_party.telegram_bot_pagination import InlineKeyboardPaginator
from third_party.get_tz_from_offset__zoneinfo import get_tz as get_tz_from_offset
from third_party.is_equal_inline_keyboards import is_equal_inline_keyboards


# TODO:
# INLINE_BUTTON_TEXT_DELETE = "❌ Удалить"
#
#
# INLINE_BUTTON_DELETE = InlineKeyboardButton(
#     INLINE_BUTTON_TEXT_DELETE, callback_data=PATTERN_DELETE_MESSAGE
# )


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


def get_int_from_match(
    match: re.Match,
    name: str,
    default: int | None = None,
) -> int | None:
    try:
        return int(match[name])
    except:
        return default


def send_reminder(
    bot: Bot,
    chat: Chat,
    reminder: Reminder,
    message_id: int,
    reply_markup: str | None,
    as_new_message: bool = True,
):
    chat_id: int = chat.id

    tz_chat: tzinfo | None = get_tz(chat.tz)
    if tz_chat is None:
        bot.send_message(
            chat_id=chat_id,
            text=f"Не удалось найти часовой пояс {chat.tz!r}",
        )
        return

    target_datetime_utc = reminder.target_datetime_utc
    target_datetime = convert_tz(
        dt=target_datetime_utc,
        from_tz=timezone.utc,
        to_tz=tz_chat,
    )

    next_send_datetime_utc = reminder.next_send_datetime_utc
    next_send_datetime = convert_tz(
        dt=next_send_datetime_utc,
        from_tz=timezone.utc,
        to_tz=tz_chat,
    )

    # TODO: Перенести в db.py?
    if reminder.repeat_every:
        repeat_every: TimeUnit | None = TimeUnit.parse_value(reminder.repeat_every)
    else:
        repeat_every: TimeUnit | None = None

    lines: list[str] = [
        f"Напоминание установлено на {datetime_to_str(target_datetime)} (в UTC {datetime_to_str(target_datetime_utc)})",
        f"Ближайшее: {datetime_to_str(next_send_datetime)} (в UTC {datetime_to_str(next_send_datetime_utc)})",
        f"Повтор: {repeat_every.get_value() if repeat_every else 'нет'}",
    ]

    if not reminder.repeat_before:
        lines.append("Без напоминаний")
    else:
        lines.append("Напоминаний:")

        # TODO: Перенести в db.py
        import json

        repeat_before = [
            TimeUnit.parse_value(value) for value in json.loads(reminder.repeat_before)
        ]

        for time_unit in repeat_before:
            prev_dt = time_unit.get_prev_datetime(target_datetime)
            prev_dt_utc = convert_tz(
                dt=prev_dt,
                from_tz=tz_chat,
                to_tz=timezone.utc,
            )
            lines.append(
                f"    {time_unit.get_value()}: {prev_dt} (в UTC {datetime_to_str(prev_dt_utc)})"
            )

    text = "\n".join(lines)

    if len(text) > MESS_MAX_LENGTH:
        text = text[: MESS_MAX_LENGTH - 3] + "..."

    if as_new_message:
        bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            reply_to_message_id=message_id,
        )
    else:
        bot.edit_message_text(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            message_id=message_id,
        )


def get_reminders(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()

    message = update.effective_message
    chat = Chat.get_from(update.effective_chat)

    page: int = get_int_from_match(context.match, "page", default=1)
    filters = [
        (Reminder.chat_id == chat.id),
        # TODO: Нужно ли фильтровать по user_id? Отправка идет в chat
        (Reminder.user_id == update.effective_user.id),
    ]

    reminder: Reminder | None = Reminder.get_by_page(page=page, filters=filters)
    if not reminder:
        text = "Напоминаний нет"
        message.reply_text(text)
        return

    total = Reminder.count(filters)
    pattern = PATTERN_REMINDER_PAGE

    paginator = InlineKeyboardPaginator(
        page_count=total,
        current_page=page,
        data_pattern=fill_string_pattern(pattern, "{page}"),
    )
    # TODO: Удалять напоминание, а не сообщение
    #       Мб еще отдельным сообщением спрашивать?
    # paginator.add_before(INLINE_BUTTON_DELETE)

    reply_markup: str | None = paginator.markup

    # Fix error: "telegram.error.BadRequest: Message is not modified"
    if query and is_equal_inline_keyboards(reply_markup, query.message.reply_markup):
        return

    try:
        send_reminder(
            bot=context.bot,
            chat=chat,
            reminder=reminder,
            message_id=message.message_id,
            reply_markup=reply_markup,
            as_new_message=query is None,
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            return

        raise e


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

    # TODO: Дублирует send_reminder
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
def on_get_reminders(update: Update, context: CallbackContext):
    get_reminders(update, context)


@log_func(log)
def on_change_reminder_page(update: Update, context: CallbackContext):
    get_reminders(update, context)


# TODO:
# @log_func(log)
# def on_callback_delete_message(update: Update, _: CallbackContext):
#     query = update.callback_query
#
#     try:
#         query.delete_message()
#     except BadRequest as e:
#         if "Message can't be deleted for everyone" in str(e):
#             text = "Нельзя удалить сообщение, т.к. оно слишком старое. Остается только вручную его удалить"
#         else:
#             text = f"При попытке удаления сообщения возникла ошибка: {str(e)!r}"
#
#         query.answer(
#             text=text,
#             show_alert=True,
#         )
#         return
#
#     query.answer()


def on_error(update: Update, context: CallbackContext):
    reply_error(log, update, context)


def setup(dp: Dispatcher):
    dp.add_handler(CommandHandler(COMMAND_START, on_start))
    dp.add_handler(CommandHandler(COMMAND_HELP, on_start))

    dp.add_handler(CommandHandler(COMMAND_TZ, on_tz))

    dp.add_handler(CommandHandler(COMMAND_LIST, on_get_reminders))
    dp.add_handler(MessageHandler(Filters.regex(PATTERN_LIST), on_get_reminders))

    # TODO:
    # dp.add_handler(
    #     CallbackQueryHandler(on_callback_delete_message, pattern=PATTERN_DELETE_MESSAGE)
    # )
    dp.add_handler(
        CallbackQueryHandler(on_change_reminder_page, pattern=PATTERN_REMINDER_PAGE)
    )

    dp.add_handler(MessageHandler(Filters.text, on_request))

    dp.add_error_handler(on_error)
