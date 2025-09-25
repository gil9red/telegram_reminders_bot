#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
from third_party.regexp import fill_string_pattern


PATTERN_REMINDER_PAGE: re.Pattern = re.compile(r"^reminder page=(?P<page>\d+)$")
PATTERN_REMINDER_DELETE: re.Pattern = re.compile(r"^reminder#(?P<id>\d+)-delete$")
PATTERN_REMINDER_ASK_DELETE: re.Pattern = re.compile(r"^reminder#(?P<id>\d+)-ask-delete$")
PATTERN_DELETE_MESSAGE: re.Pattern = re.compile(r"^delete message$")

COMMAND_START: str = "start"
COMMAND_HELP: str = "help"

COMMAND_ADD: str = "add"

COMMAND_TZ: str = "tz"

COMMAND_LIST: str = "list"
PATTERN_LIST: re.Pattern = re.compile("^Список$", flags=re.IGNORECASE)


if __name__ == "__main__":
    # TODO: в тесты

    data: str = fill_string_pattern(PATTERN_REMINDER_PAGE, 999_999_999)
    print(len(data), data)
    assert data == "reminder page=999999999"

    data: str = fill_string_pattern(PATTERN_REMINDER_DELETE, 999_999_999)
    print(len(data), data)
    assert data == "reminder#999999999-delete"

    data: str = fill_string_pattern(PATTERN_REMINDER_ASK_DELETE, 999_999_999)
    print(len(data), data)
    assert data == "reminder#999999999-ask-delete"
