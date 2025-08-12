#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
from datetime import datetime, tzinfo, timezone

from telegram import Update, Bot
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
from common import log_func, log, reply_error, datetime_to_str
from tz_utils import convert_tz, get_tz
from db import Reminder, Chat, User

from parser import (
    ParseResult,
    Defaults,
    RepeatEvery,
    parse_command,
    cals_next_send_datetime_utc,
)
from regexp_patterns import (
    COMMAND_START,
    COMMAND_HELP,
    COMMAND_ADD,
    COMMAND_TZ,
    COMMAND_LIST,
    PATTERN_LIST,
    # PATTERN_DELETE_MESSAGE,  # TODO:
    PATTERN_REMINDER_PAGE,
    fill_string_pattern,
)
from third_party.telegram_bot_pagination import InlineKeyboardPaginator
from third_party.is_equal_inline_keyboards import is_equal_inline_keyboards


# TODO:
# INLINE_BUTTON_TEXT_DELETE = "❌ Удалить"
#
#
# INLINE_BUTTON_DELETE = InlineKeyboardButton(
#     INLINE_BUTTON_TEXT_DELETE, callback_data=PATTERN_DELETE_MESSAGE
# )


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

    target_datetime_utc = reminder.target_datetime_utc
    target_datetime = reminder.get_target_datetime()

    next_send_datetime_utc = reminder.next_send_datetime_utc
    next_send_datetime = reminder.get_next_send_datetime()

    repeat_every: RepeatEvery | None = reminder.get_repeat_every()

    lines: list[str] = [
        f"Напоминание: {reminder.target}",
        f"Установлено на {datetime_to_str(target_datetime)} (в UTC {datetime_to_str(target_datetime_utc)})",
        f"Ближайшее: {datetime_to_str(next_send_datetime)} (в UTC {datetime_to_str(next_send_datetime_utc)})",
        f"Повтор: {repeat_every.get_value() if repeat_every else 'нет'}",
    ]

    repeat_before = reminder.get_repeat_before()
    if not repeat_before:
        lines.append("Без напоминаний")
    else:
        tz_chat: tzinfo = chat.get_tz()

        lines.append("Напоминаний:")

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
        message.reply_text(text, quote=True)
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
    # TODO: Обновить примеры команд добавить про команду /add или тоже самое, если написать
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

    # Получение и проверка часового пояса
    tz_chat: tzinfo = get_tz(value)

    dt_utc: datetime = datetime.utcnow()
    dt: datetime = convert_tz(
        dt=dt_utc,
        from_tz=timezone.utc,
        to_tz=tz_chat,
    )
    date_info: str = (
        f"\nВремя: {datetime_to_str(dt)}\nВремя в UTC: {datetime_to_str(dt_utc)}"
    )

    if is_set:
        if chat.tz == value:
            message.reply_markdown(
                f"Часовой пояс `{value}` уже был установлен.\n{date_info}",
                quote=True,
            )
            return

        chat.tz = value
        chat.save()

        message.reply_markdown(
            f"Установлен часовой пояс `{value}`.\n{date_info}",
            quote=True,
        )
        return

    message.reply_markdown(
        f"Часовой пояс `{value}`.\n{date_info}",
        quote=True,
    )


def add_reminder(command: str, update: Update):
    log.debug(f"Command: {command!r}")

    chat = Chat.get_from(update.effective_chat)
    message = update.effective_message

    tz_chat: tzinfo = get_tz(chat.tz)

    now_utc: datetime = datetime.utcnow()

    # Время в часовом поясе пользователя
    now_dt_chat: datetime = convert_tz(
        dt=now_utc,
        from_tz=timezone.utc,
        to_tz=tz_chat,
    )

    defaults = Defaults(hours=10, minutes=0)

    try:
        parse_result: ParseResult = parse_command(
            command, dt=now_dt_chat, defaults=defaults
        )
    except Exception as e:
        log.exception("Error on parse_command:")
        message.reply_markdown(
            text=f"Не получилось разобрать команду!\nПричина:\n```plaintext\n{e}```",
            quote=True,
        )
        return

    target_datetime: datetime = parse_result.target_datetime

    target_datetime_utc: datetime = convert_tz(
        dt=target_datetime,
        from_tz=tz_chat,
        to_tz=timezone.utc,
    )

    # Следующая дата отправки
    try:
        next_send_datetime_utc: datetime = cals_next_send_datetime_utc(
            target_datetime_utc=target_datetime_utc,
            repeat_before=parse_result.repeat_before,
            now_utc=now_utc,
        )
    except Exception as e:
        log.exception("Error on cals_next_send_datetime_utc:")
        message.reply_markdown(
            text=f"Не получилось выполнить команду!\nПричина:\n```plaintext\n{e}```",
            quote=True,
        )
        return

    # TODO: Проверка на дубликат команды
    reminder = Reminder.add(
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

    next_send_datetime: datetime = reminder.get_next_send_datetime()

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
        lines.append("Напоминания:")

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

    message.reply_text("\n".join(lines), quote=True)


@log_func(log)
def on_add(update: Update, context: CallbackContext):
    add_reminder(
        command=get_context_value(context),
        update=update,
    )


@log_func(log)
def on_request(update: Update, _: CallbackContext):
    add_reminder(
        command=update.effective_message.text,
        update=update,
    )


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

    dp.add_handler(CommandHandler(COMMAND_ADD, on_add))
    dp.add_handler(MessageHandler(Filters.text, on_request))

    dp.add_error_handler(on_error)
