#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import time

from datetime import datetime
from typing import Optional
from pathlib import Path

from peewee import (
    TextField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    BooleanField,
)
from playhouse.sqliteq import SqliteQueueDatabase

import telegram

from third_party.db_peewee_meta_model import MetaModel


DIR = Path(__file__).resolve().parent
DB_DIR_NAME = DIR / "database"
DB_FILE_NAME = str(DB_DIR_NAME / "database.sqlite")

DB_DIR_NAME.mkdir(parents=True, exist_ok=True)


# This working with multithreading
# SOURCE: http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#sqliteq
db = SqliteQueueDatabase(
    DB_FILE_NAME,
    pragmas={
        "foreign_keys": 1,
        "journal_mode": "wal",  # WAL-mode
        "cache_size": -1024 * 64,  # 64MB page-cache
    },
    use_gevent=False,  # Use the standard library "threading" module.
    autostart=True,
    queue_max_size=64,  # Max. # of pending writes that can accumulate.
    results_timeout=5.0,  # Max. time to wait for query to be executed.
)


class BaseModel(MetaModel):
    class Meta:
        database = db


# SOURCE: https://core.telegram.org/bots/api#user
class User(BaseModel):
    first_name = TextField()
    last_name = TextField(null=True)
    username = TextField(null=True)
    language_code = TextField(null=True)
    last_activity = DateTimeField(default=datetime.now)

    def update_last_activity(self):
        self.last_activity = datetime.now()
        self.save()

    @classmethod
    def get_from(cls, user: telegram.User | None) -> Optional["User"]:
        if not user:
            return

        user_db = cls.get_or_none(cls.id == user.id)
        if not user_db:
            user_db = cls.create(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
                language_code=user.language_code,
            )
            user_db.update_last_activity()
        return user_db


# SOURCE: https://core.telegram.org/bots/api#chat
class Chat(BaseModel):
    type = TextField()
    title = TextField(null=True)
    username = TextField(null=True)
    first_name = TextField(null=True)
    last_name = TextField(null=True)
    description = TextField(null=True)
    tz = TextField(default="UTC")
    last_activity = DateTimeField(default=datetime.now)

    def update_last_activity(self):
        self.last_activity = datetime.now()
        self.save()

    @classmethod
    def get_from(cls, chat: telegram.Chat | None) -> Optional["Chat"]:
        if not chat:
            return

        chat_db = cls.get_or_none(cls.id == chat.id)
        if not chat_db:
            chat_db = cls.create(
                id=chat.id,
                type=chat.type,
                title=chat.title,
                username=chat.username,
                first_name=chat.first_name,
                last_name=chat.last_name,
                description=chat.description,
            )
            chat_db.update_last_activity()
        return chat_db


class Reminder(BaseModel):
    create_datetime_utc = DateTimeField(default=datetime.utcnow)
    original_message_text = TextField()
    original_message_id = IntegerField()
    last_send_message_id = IntegerField(null=True)
    last_send_datetime_utc = DateTimeField(null=True)
    target_datetime_utc = DateTimeField(default=datetime.utcnow)
    is_sent = BooleanField(default=False)
    # TODO:
    # is_active = BooleanField(default=True)
    user = ForeignKeyField(User, backref="reminders")
    chat = ForeignKeyField(Chat, backref="reminders")

    # TODO: Проверка существования

    @classmethod
    def add(
        cls,
        original_message_id: int,
        original_message_text: str,
        target_datetime_utc: datetime,
        user: User,
        chat: Chat,
    ) -> "Reminder":
        return cls.create(
            original_message_id=original_message_id,
            original_message_text=original_message_text,
            target_datetime_utc=target_datetime_utc,
            user=user,
            chat=chat,
        )


db.connect()
db.create_tables(BaseModel.get_inherited_models())

# Задержка в 50мс, чтобы дать время на запуск SqliteQueueDatabase и создание таблиц
# Т.к. в SqliteQueueDatabase запросы на чтение выполняются сразу, а на запись попадают в очередь
time.sleep(0.050)


if __name__ == "__main__":
    BaseModel.print_count_of_tables()
    print()

    print("Total users:", User.select().count())
    print("Total chats:", Chat.select().count())

    assert User.get_from(None) is None
    assert Chat.get_from(None) is None

    print()

    first_user = User.select().first()
    print("First user:", first_user)

    first_chat = Chat.select().first()
    print("First chat:", first_chat)
    print()

    print("Total reminders:", Reminder.select().count())
    print()

    print("Last reminder:", Reminder.select().order_by(Reminder.id.desc()).first())
