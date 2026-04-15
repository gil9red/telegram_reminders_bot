#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import os
from pathlib import Path


DIR: Path = Path(__file__).resolve().parent
TOKEN_FILE_NAME: Path = DIR / "TOKEN.txt"

try:
    TOKEN: str = os.environ.get("TOKEN") or TOKEN_FILE_NAME.read_text("utf-8").strip()
except:
    raise Exception("TOKEN не задан")

MESS_MAX_LENGTH: int = 4096
