#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re

from third_party.regexp import fill_string_pattern


PATTERN_REMINDER_PAGE = re.compile(r"^reminder page=(?P<page>\d+)$")
# TODO:
# PATTERN_DELETE_MESSAGE = "delete_message"

# TODO:
PATTERN_SHOW_ORIGINAL_MESSAGE = re.compile(r"^reminder#(?P<id>\d+)-orig-mess$")

# TODO:
PATTERN_DELETE = re.compile(r"^reminder#(?P<id>\d+)-delete$")

COMMAND_START = "start"
COMMAND_HELP = "help"

COMMAND_ADD = "add"

COMMAND_TZ = "tz"

COMMAND_LIST = "list"
PATTERN_LIST = re.compile("^Список$", flags=re.IGNORECASE)


if __name__ == "__main__":
    print(fill_string_pattern(PATTERN_REMINDER_PAGE, 999_999_999))
    assert (
        fill_string_pattern(PATTERN_REMINDER_PAGE, 999_999_999)
        == "reminder page=999999999"
    )

    print(fill_string_pattern(PATTERN_SHOW_ORIGINAL_MESSAGE, 999_999_999))
    assert (
        fill_string_pattern(PATTERN_SHOW_ORIGINAL_MESSAGE, 999_999_999)
        == "reminder#999999999-orig-mess"
    )

    print(fill_string_pattern(PATTERN_DELETE, 999_999_999))
    assert (
            fill_string_pattern(PATTERN_DELETE, 999_999_999)
            == "reminder#999999999-delete"
    )
