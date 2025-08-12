#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import logging
import re
import sys

from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

import config


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


log = get_logger(__file__)
