#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re

from third_party.regexp import fill_string_pattern


PATTERN_REMINDER_PAGE = re.compile(r"^reminder page=(?P<page>\d+)$")
# TODO:
# PATTERN_DELETE_MESSAGE = "delete_message"

COMMAND_START = "start"
COMMAND_HELP = "help"

COMMAND_TZ = "tz"

COMMAND_LIST = "list"
PATTERN_LIST = re.compile("^Список$", flags=re.IGNORECASE)


if __name__ == "__main__":
    print(fill_string_pattern(PATTERN_REMINDER_PAGE, 999_999_999))
    assert (
        fill_string_pattern(PATTERN_REMINDER_PAGE, 999_999_999)
        == "reminder page=999999999"
    )
