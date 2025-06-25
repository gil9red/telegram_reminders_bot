#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re

from dataclasses import dataclass, field
from datetime import datetime, timedelta


# TODO:
PATTERN = re.compile(
    r"Напомни через (\d+) (секунд|минут|час|день|дня|дней|неделю|недели|недель)",
    flags=re.IGNORECASE,
)


@dataclass
class ParseResult:
    # TODO: Заполнить инфу по разбору из шаблона
    target_datetime: datetime
    # repeat_every: str
    # reminder_before: list[str] = field(default_factory=list)


def parse_command(command: str) -> ParseResult | None:
    m = PATTERN.search(command)
    if not m:
        return

    value, kind = m.groups()
    kind = kind.lower()
    value = int(value)

    if kind == "секунд":
        data = dict(seconds=value)
    elif kind == "минут":
        data = dict(minutes=value)
    elif kind == "час":
        data = dict(hours=value)
    elif kind in ["день", "дня", "дней"]:
        data = dict(days=value)
    elif kind in ["неделю", "недели", "недель"]:
        data = dict(weeks=value)
    else:
        return

    return ParseResult(
        target_datetime=datetime.now() + timedelta(**data),
    )


def get_pretty_datetime(finish_time: datetime) -> str:
    return finish_time.strftime("%d.%m.%Y %H:%M:%S")


if __name__ == "__main__":
    date_time = datetime.now()
    print("Current datetime:", get_pretty_datetime(date_time))
    print()

    commands = [
        "напомни через 10 секунд",
        "НАПОМНИ ЧЕРЕЗ 1 час",
        "НАпоМНИ ЧЕрез 2 часa",
        "напомни через 5 часов",
        "напомни через 1 день",
    ]
    fmt = "{:%s} -> {}" % len(max(commands, key=len))

    for command in commands:
        parse_result: ParseResult | None = parse_command(command)
        print(fmt.format(command, get_pretty_datetime(parse_result.target_datetime)))
