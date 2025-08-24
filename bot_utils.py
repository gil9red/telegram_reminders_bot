#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import functools
import logging
from html import escape
from zoneinfo import ZoneInfoNotFoundError

from telegram import Update
from telegram.ext import CallbackContext

import db
from common import prepare_text


def log_func(log: logging.Logger):
    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(update: Update, context: CallbackContext):
            if update:
                chat_id: int | None = None
                user_id: int | None = None
                first_name: str | None = None
                last_name: str | None = None
                username: str | None = None
                language_code: str | None = None

                if update.effective_chat:
                    db.Chat.get_from(update.effective_chat).update_last_activity()

                    chat_id = update.effective_chat.id

                if update.effective_user:
                    db.User.get_from(update.effective_user).update_last_activity()

                    user_id = update.effective_user.id
                    first_name = update.effective_user.first_name
                    last_name = update.effective_user.last_name
                    username = update.effective_user.username
                    language_code = update.effective_user.language_code

                try:
                    message = update.effective_message.text
                except:
                    message = ""

                try:
                    query_data = update.callback_query.data
                except:
                    query_data = ""

                msg = (
                    f"[chat_id={chat_id}, user_id={user_id}, "
                    f"first_name={first_name!r}, last_name={last_name!r}, "
                    f"username={username!r}, language_code={language_code}, "
                    f"message={message!r}, query_data={query_data!r}]"
                )
                msg = func.__name__ + msg

                log.debug(msg)

            return func(update, context)

        return wrapper

    return actual_decorator


def reply_error(log: logging.Logger, update: Update, context: CallbackContext):
    log.error("Error: %s\nUpdate: %s", context.error, update, exc_info=context.error)
    if not update:
        return

    if isinstance(context.error, ZoneInfoNotFoundError):
        text: str = f"Не удалось найти часовой пояс {context.error.args[0]!r}"
    else:
        text: str = (
            f"⚠ Возникла непредвиденная ошибка {str(context.error)!r}.\n"
            f"Попробуйте повторить запрос или попробовать чуть позже..."
        )

    text: str = prepare_text(text)

    update.effective_message.reply_text(text, quote=True)


def get_blockquote_html(text: str) -> str:
    return f"<blockquote>{escape(text)}</blockquote>"


if __name__ == "__main__":
    # TODO: tests
    assert get_blockquote_html("") == "<blockquote></blockquote>"
    assert get_blockquote_html("Hello World") == "<blockquote>Hello World</blockquote>"
    assert (
        get_blockquote_html("Hello\n\nWorld\n!")
        == "<blockquote>Hello\n\nWorld\n!</blockquote>"
    )
    assert (
        get_blockquote_html("Hello&World") == "<blockquote>Hello&amp;World</blockquote>"
    )
