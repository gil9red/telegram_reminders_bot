#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from datetime import datetime, tzinfo, timezone

from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
)
from telegram.error import BadRequest

from common import (
    log,
    datetimes_pair_to_str,
    prepare_text,
    get_int_from_match,
    convert_tz,
    get_tz,
)
from bot_utils import log_func, reply_error, get_blockquote_html
from db import Reminder, Chat, User

from parser import (
    TimeUnit,
    ParseResult,
    Defaults,
    RepeatEvery,
    parse_command,
    get_nearest_datetime,
)
from regexp_patterns import (
    COMMAND_START,
    COMMAND_HELP,
    COMMAND_ADD,
    COMMAND_TZ,
    COMMAND_LIST,
    PATTERN_LIST,
    PATTERN_REMINDER_PAGE,
    PATTERN_REMINDER_DELETE,
    PATTERN_REMINDER_ASK_DELETE,
    PATTERN_DELETE_MESSAGE,
    fill_string_pattern,
)
from third_party.telegram_bot_pagination import InlineKeyboardPaginator
from third_party.is_equal_inline_keyboards import is_equal_inline_keyboards

INLINE_BUTTON_TEXT_DELETE: str = "❌ Удалить"
INLINE_BUTTON_TEXT_YES: str = "✅ Да"
INLINE_BUTTON_TEXT_NO: str = "❌ Нет"


def get_delete_button_for_reminder(reminder_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=INLINE_BUTTON_TEXT_DELETE,
        callback_data=fill_string_pattern(PATTERN_REMINDER_ASK_DELETE, reminder_id),
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


def _fill_repeat_before(
    repeat_before: list[TimeUnit],
    target_datetime: datetime,
    tz_chat: tzinfo,
) -> list[str]:
    if not repeat_before:
        return ["Без напоминаний"]

    lines: list[str] = ["Напоминания:"]
    now_dt: datetime = datetime.now()

    for time_unit in repeat_before:
        prev_dt: datetime = time_unit.get_prev_datetime(target_datetime)
        prev_dt_utc: datetime = convert_tz(
            dt=prev_dt,
            from_tz=tz_chat,
            to_tz=timezone.utc,
        )

        line: str = (
            f"{time_unit.get_value()}: {datetimes_pair_to_str(prev_dt, prev_dt_utc)}"
        )
        if prev_dt < now_dt:  # Зачеркнуть прошедшие даты
            line = f"<del>{line}</del>"

        lines.append(f"    {line}")

    return lines


def send_reminder(
    bot: Bot,
    chat: Chat,
    reminder: Reminder,
    message_id: int,
    reply_markup: str | None,
    as_new_message: bool = True,
) -> None:
    chat_id: int = chat.id

    target_datetime_utc = reminder.target_datetime_utc
    target_datetime = reminder.get_target_datetime()

    next_send_datetime_utc = reminder.next_send_datetime_utc
    next_send_datetime = reminder.get_next_send_datetime()

    repeat_every: RepeatEvery | None = reminder.get_repeat_every()

    lines: list[str] = [
        "Напоминание:",
        get_blockquote_html(reminder.target),
        f"Установлено на {datetimes_pair_to_str(target_datetime, target_datetime_utc)}",
        f"Ближайшее: {datetimes_pair_to_str(next_send_datetime, next_send_datetime_utc)}",
        f"Повтор: {repeat_every.get_value() if repeat_every else 'нет'}",
    ]
    lines += _fill_repeat_before(
        repeat_before=reminder.get_repeat_before(),
        target_datetime=target_datetime,
        tz_chat=chat.get_tz(),
    )
    lines.append(
        f"\nОригинальное сообщение:\n"
        + get_blockquote_html(reminder.original_message_text)
    )

    lines.append("")
    create_datetime_utc: datetime = reminder.create_datetime_utc
    create_datetime: datetime = reminder.get_create_datetime()
    lines.append(
        f"Создано {datetimes_pair_to_str(create_datetime, create_datetime_utc)}"
    )

    text: str = prepare_text("\n".join(lines))
    parse_mode: str = ParseMode.HTML

    if as_new_message:
        bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            reply_to_message_id=message_id,
        )
    else:
        bot.edit_message_text(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
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
        message.reply_text("Напоминаний нет", quote=True)
        return

    total = Reminder.count(filters)
    pattern = PATTERN_REMINDER_PAGE

    paginator = InlineKeyboardPaginator(
        page_count=total,
        current_page=page,
        data_pattern=fill_string_pattern(pattern, "{page}"),
    )
    paginator.add_before(
        get_delete_button_for_reminder(reminder.id),
    )

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
def on_start(update: Update, _: CallbackContext) -> None:
    text = """
Введите что-нибудь или с добавление команды `/add "Встреча" сегодня в 18:00`, например:
- `Напомни о "🍕" 10 февраля`
- `"ДНС" 10 февраля в 14:55`
- `Напомни о "Покупки" сегодня`
- `Напомни о "Покупки" завтра в 12:00`
- `Напомни о "Покупки" через 2 дня в 12:00`
- `Напомни о "Покупки" в следующую субботу`
- `Напомни о "🍕" в четверг в 12:00. Повтор каждый четверг`
- `День рождения "xxx" 10 февраля 2027 года в 14:55. Повтор каждый день`
- `Праздник "xxx" 10 февраля. Повтор каждый год`
- `День рождения "^_^" 10 февраля. Повтор раз в год. Напомнить за месяц, за неделю, за 3 дня, за день`

Для получения списка напоминаний, напишите: `список` или /list.

Чтобы бот правильно работал с датами, нужно задать свой часовой пояс.
Для установки или получения часового пояса:
- /tz - для получения
- /tz <часовой пояс в IANA или +-часы:минуты> - для установки. Например:
  - `/tz Europe/Moscow`
  - `/tz +03:00`
    """
    update.effective_message.reply_markdown(
        prepare_text(text),
        quote=True,
    )


@log_func(log)
def on_tz(update: Update, context: CallbackContext) -> None:
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
    date_info: str = f"Время: {datetimes_pair_to_str(dt, dt_utc)}"

    if is_set:
        if chat.tz == value:
            message.reply_markdown(
                text=prepare_text(
                    f"Часовой пояс `{value}` уже был установлен.\n\n{date_info}"
                ),
                quote=True,
            )
            return

        chat.tz = value
        chat.save()

        message.reply_markdown(
            text=prepare_text(f"Установлен часовой пояс `{value}`.\n\n{date_info}"),
            quote=True,
        )
        return

    message.reply_markdown(
        text=prepare_text(f"Часовой пояс `{value}`.\n\n{date_info}"),
        quote=True,
    )


def add_reminder(command: str, update: Update) -> None:
    log.debug(f"Command: {command!r}")

    message = update.effective_message

    if not command:
        message.reply_text(
            text=prepare_text(
                "ℹ️ Пустая команда!\n"
                "Для создания напоминания нужно ввести команду.\n"
                "Пример команд можно посмотреть в /help"
            ),
            quote=True,
        )
        return

    chat = Chat.get_from(update.effective_chat)
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
        message.reply_html(
            text=prepare_text(
                f"Не получилось разобрать команду!\n"
                f"Причина:\n{get_blockquote_html(str(e))}"
            ),
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
        next_send_datetime_utc: datetime = get_nearest_datetime(
            target_dt=target_datetime_utc,
            repeat_before=parse_result.repeat_before,
            dt=now_utc,
        )
    except Exception as e:
        log.exception("Error on cals_next_send_datetime_utc:")
        message.reply_html(
            text=prepare_text(
                f"Не получилось выполнить команду!\n"
                f"Причина:\n{get_blockquote_html(str(e))}"
            ),
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
        f"Напоминание установлено на {datetimes_pair_to_str(target_datetime, target_datetime_utc)}",
        f"Ближайшее: {datetimes_pair_to_str(next_send_datetime, next_send_datetime_utc)}",
        f"Повтор: {parse_result.repeat_every.get_value() if parse_result.repeat_every else 'нет'}",
    ]
    lines += _fill_repeat_before(
        repeat_before=parse_result.repeat_before,
        target_datetime=target_datetime,
        tz_chat=tz_chat,
    )

    text: str = prepare_text("\n".join(lines))

    message.reply_html(
        text=text,
        reply_markup=InlineKeyboardMarkup.from_button(
            get_delete_button_for_reminder(reminder.id),
        ),
        quote=True,
    )


@log_func(log)
def on_add(update: Update, context: CallbackContext) -> None:
    add_reminder(
        command=get_context_value(context),
        update=update,
    )


@log_func(log)
def on_request(update: Update, _: CallbackContext) -> None:
    add_reminder(
        command=update.effective_message.text,
        update=update,
    )


@log_func(log)
def on_get_reminders(update: Update, context: CallbackContext) -> None:
    get_reminders(update, context)


@log_func(log)
def on_change_reminder_page(update: Update, context: CallbackContext) -> None:
    get_reminders(update, context)


@log_func(log)
def on_reminder_ask_delete(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if query:
        query.answer()

    message = update.effective_message
    reminder_id: int = get_int_from_match(context.match, "id")

    reminder: Reminder | None = Reminder.get_or_none(id=reminder_id)
    if not reminder:
        message.reply_text("⚠ Напоминания уже нет", quote=True)
        return

    target_datetime_utc = reminder.target_datetime_utc
    target_datetime = reminder.get_target_datetime()

    create_datetime_utc = reminder.create_datetime_utc
    create_datetime = reminder.get_create_datetime()

    # TODO: Какой-нибудь общий метод для текста по напоминаниям?
    lines: list[str] = [
        "Удалить напоминание?",
        "",
        f"Установлено на {datetimes_pair_to_str(target_datetime, target_datetime_utc)}",
        "",
        "Оригинальное сообщение:",
        get_blockquote_html(reminder.original_message_text),
        "",
        f"Создано {datetimes_pair_to_str(create_datetime, create_datetime_utc)}",
    ]
    text: str = prepare_text("\n".join(lines))

    message.reply_html(
        text=prepare_text(text),
        reply_markup=InlineKeyboardMarkup.from_row(
            [
                InlineKeyboardButton(
                    text=INLINE_BUTTON_TEXT_YES,
                    callback_data=fill_string_pattern(
                        PATTERN_REMINDER_DELETE, reminder.id
                    ),
                ),
                InlineKeyboardButton(
                    text=INLINE_BUTTON_TEXT_NO,
                    callback_data=fill_string_pattern(
                        PATTERN_DELETE_MESSAGE, reminder.id
                    ),
                ),
            ]
        ),
        quote=True,
    )


@log_func(log)
def on_reminder_delete(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if query:
        query.answer()

    message = update.effective_message
    reminder_id: int = get_int_from_match(context.match, "id")

    reminder: Reminder | None = Reminder.get_or_none(id=reminder_id)
    if not reminder:
        message.reply_text("⚠ Напоминания уже нет", quote=True)
        return

    reminder.delete_instance()

    message.reply_markdown(
        # TODO: Мб вывести оригинальное сообщение?
        text=prepare_text("Напоминание было удалено!"),
        quote=True,
    )


@log_func(log)
def on_delete_message(update: Update, _: CallbackContext) -> None:
    query = update.callback_query

    try:
        query.delete_message()
    except BadRequest as e:
        if "Message can't be deleted for everyone" in str(e):
            text = "Нельзя удалить сообщение, т.к. оно слишком старое. Остается только вручную его удалить"
        else:
            text = f"При попытке удаления сообщения возникла ошибка: {str(e)!r}"

        query.answer(
            text=text,
            show_alert=True,
        )
        return

    query.answer()


def on_error(update: Update, context: CallbackContext) -> None:
    reply_error(log, update, context)


def setup(dp: Dispatcher) -> None:
    dp.add_handler(CommandHandler(COMMAND_START, on_start))
    dp.add_handler(CommandHandler(COMMAND_HELP, on_start))

    dp.add_handler(CommandHandler(COMMAND_TZ, on_tz))

    dp.add_handler(CommandHandler(COMMAND_LIST, on_get_reminders))
    dp.add_handler(MessageHandler(Filters.regex(PATTERN_LIST), on_get_reminders))

    dp.add_handler(
        CallbackQueryHandler(on_change_reminder_page, pattern=PATTERN_REMINDER_PAGE)
    )

    dp.add_handler(
        CallbackQueryHandler(
            on_reminder_ask_delete, pattern=PATTERN_REMINDER_ASK_DELETE
        )
    )
    dp.add_handler(
        CallbackQueryHandler(on_reminder_delete, pattern=PATTERN_REMINDER_DELETE)
    )
    dp.add_handler(
        CallbackQueryHandler(on_delete_message, pattern=PATTERN_DELETE_MESSAGE)
    )

    dp.add_handler(CommandHandler(COMMAND_ADD, on_add))
    dp.add_handler(MessageHandler(Filters.text, on_request))

    dp.add_error_handler(on_error)
