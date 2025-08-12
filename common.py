#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import logging
import re
import sys

from datetime import datetime, tzinfo
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import config
from third_party.get_tz_from_offset__zoneinfo import get_tz as get_tz_from_offset


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


def datetime_to_str(dt: datetime) -> str:
    return f"{dt:%d.%m.%Y %H:%M:%S}"


def prepare_text(text: str, max_length: int = config.MESS_MAX_LENGTH) -> str:
    postfix: str = "..."
    if len(text) > max_length:
        text = text[: max_length - len(postfix)] + postfix

    return text


def get_int_from_match(
    match: re.Match,
    name: str,
    default: int | None = None,
) -> int | None:
    try:
        return int(match[name])
    except:
        return default


def convert_tz(dt: datetime, from_tz: tzinfo, to_tz: tzinfo) -> datetime:
    return (
        dt.replace(tzinfo=from_tz)  # Указание часового пояса (дата не меняется)
        .astimezone(to_tz)  # Изменение времени и часового пояса (дата изменилась)
        .replace(tzinfo=None)  # Удаление часового пояса (дата не меняется)
    )


def get_tz(value: str) -> tzinfo:
    try:
        return get_tz_from_offset(value)
    except Exception:
        try:
            return ZoneInfo(value)
        except ZoneInfoNotFoundError:
            pass

        raise ZoneInfoNotFoundError(value)


log = get_logger(__file__)
