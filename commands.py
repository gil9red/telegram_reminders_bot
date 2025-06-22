#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from telegram import Update
from telegram.ext import (
    CallbackContext,
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
)

from common import log_func, log
from db import Reminder
from utils import parse_command, get_pretty_datetime


@log_func(log)
def on_start(update: Update, _: CallbackContext):
    update.effective_message.reply_markdown(
        'Введите что-нибудь, например: `напомни через 1 час`.\n'
        'Для получения списка напоминаний, напишите: `список`'
    )


@log_func(log)
def on_request(update: Update, _: CallbackContext):
    message = update.effective_message

    command = message.text
    log.debug(f"Command: {command!r}")

    finish_time = parse_command(command)
    if not finish_time:
        message.reply_text("Не получилось разобрать команду!")
        return

    Reminder.add(
        original_message=message,
        target_time=finish_time,
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
        .order_by(Reminder.target_time)
    )

    number = query.count()

    if number:
        text = f"Напоминаний ({number}):\n"
        for x in query:
            text += "    " + get_pretty_datetime(x.target_time) + "\n"
    else:
        text = "Напоминаний нет"

    message.reply_text(text)


def setup(dp: Dispatcher):
    dp.add_handler(CommandHandler("start", on_start))
    dp.add_handler(CommandHandler("help", on_start))

    dp.add_handler(MessageHandler(Filters.regex("(?i)^Список$"), on_get_reminders))

    dp.add_handler(MessageHandler(Filters.text, on_request))
