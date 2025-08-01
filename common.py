#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import functools
import logging
import sys

from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfoNotFoundError

from telegram import Update
from telegram.ext import CallbackContext

import config
import db


def get_logger(file_name: str, dir_name: Path = config.DIR / "logs") -> logging.Logger:
    log = logging.getLogger(file_name)
    log.setLevel(logging.DEBUG)

    dir_name = dir_name.resolve()
    dir_name.mkdir(parents=True, exist_ok=True)

    file_name = Path(file_name).resolve()
    file_name = dir_name / (file_name.name + ".log")

    formatter = logging.Formatter(
        "[%(asctime)s] %(filename)s[LINE:%(lineno)d] %(levelname)-8s %(message)s"
    )

    fh = RotatingFileHandler(
        file_name, maxBytes=10_000_000, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    return log


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
    if update:
        if isinstance(context.error, ZoneInfoNotFoundError):
            text = f"Не удалось найти часовой пояс {context.error.args[0]!r}"
        else:
            text = config.ERROR_TEXT

        update.effective_message.reply_text(text, quote=True)


def datetime_to_str(dt: datetime) -> str:
    return f"{dt:%d.%m.%Y %H:%M:%S}"


log = get_logger(__file__)
