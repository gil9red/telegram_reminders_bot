# -*- coding: utf-8 -*-

# SOURCE: https://github.com/ksinn/python-telegram-bot-pagination/blob/420d66ad9cc45438c0efc504ed9840bc70ef885d/telegram_bot_pagination/__init__.py

# author: https://github.com/ksinn
# author: https://github.com/gil9red


import enum
import json

from dataclasses import dataclass
from typing import Iterable


@dataclass
class InlineKeyboardButton:
    text: str
    callback_data: str = None
    url: str = None


class PrevNextButtonsEnum(enum.Enum):
    NONE = enum.auto()
    ROW = enum.auto()
    BOTTOM = enum.auto()


def _button_to_dict(button: InlineKeyboardButton) -> dict[str, str]:
    data = dict(text=button.text)
    if button.callback_data:
        data['callback_data'] = button.callback_data

    if button.url:
        data['url'] = button.url

    return data


def _buttons_to_dict(buttons: Iterable[InlineKeyboardButton]) -> list[dict[str, str]]:
    return [
        _button_to_dict(button) for button in buttons
    ]


def calc_pages(page: int, start_page: int, max_page: int) -> tuple[int, int]:
    prev_page = max_page if page <= start_page else page - 1
    next_page = start_page if page >= max_page else page + 1
    return prev_page, next_page


class InlineKeyboardPaginator:
    _keyboard_before: list = None
    _keyboard: list = None
    _keyboard_after: list = None

    first_page_label: str = '« {}'
    previous_page_label: str = '‹ {}'
    next_page_label: str = '{} ›'
    last_page_label: str = '{} »'
    current_page_label: str = '·{}·'

    prev_label: str = '⬅️'
    next_label: str = '➡️'

    def __init__(
            self,
            page_count: int,
            current_page: int = 1,
            data_pattern: str = '{page}',
            prev_next_buttons: PrevNextButtonsEnum = PrevNextButtonsEnum.NONE,
    ):
        self._keyboard_before = list()
        self._keyboard_after = list()

        if not current_page or current_page < 1:
            current_page = 1
        if current_page > page_count:
            current_page = page_count
        self.current_page = current_page

        self.page_count = page_count

        self.data_pattern = data_pattern

        self.prev_next_buttons = prev_next_buttons

    def _build(self):
        keyboard_dict = dict()

        if self.page_count == 1:
            self._keyboard = list()
            return

        elif self.page_count <= 5:
            for page in range(1, self.page_count + 1):
                keyboard_dict[page] = page

        else:
            keyboard_dict = self._build_for_multi_pages()

        keyboard_dict[self.current_page] = self.current_page_label.format(self.current_page)

        self._keyboard = self._to_button_array(keyboard_dict)

        if self.prev_next_buttons != PrevNextButtonsEnum.NONE and self.page_count > 1:
            prev_page, next_page = calc_pages(
                page=self.current_page,
                start_page=1,
                max_page=self.page_count
            )

            prev_button = InlineKeyboardButton(
                text=self.prev_label,
                callback_data=self.data_pattern.format(page=prev_page)
            )
            next_button = InlineKeyboardButton(
                text=self.next_label,
                callback_data=self.data_pattern.format(page=next_page)
            )

            if self.prev_next_buttons == PrevNextButtonsEnum.ROW:
                self._keyboard.insert(0, _button_to_dict(
                    prev_button
                ))
                self._keyboard.append(_button_to_dict(
                    next_button
                ))
            elif self.prev_next_buttons == PrevNextButtonsEnum.BOTTOM:
                self.add_after(prev_button, next_button)

    def _build_for_multi_pages(self):
        if self.current_page <= 3:
            return self._build_start_keyboard()

        elif self.current_page > self.page_count - 3:
            return self._build_finish_keyboard()

        else:
            return self._build_middle_keyboard()

    def _build_start_keyboard(self):
        keyboard_dict = dict()

        for page in range(1, 4):
            keyboard_dict[page] = page

        keyboard_dict[4] = self.next_page_label.format(4)
        keyboard_dict[self.page_count] = self.last_page_label.format(self.page_count)

        return keyboard_dict

    def _build_finish_keyboard(self):
        keyboard_dict = dict()

        keyboard_dict[1] = self.first_page_label.format(1)
        keyboard_dict[self.page_count - 3] = self.previous_page_label.format(self.page_count - 3)

        for page in range(self.page_count - 2, self.page_count + 1):
            keyboard_dict[page] = page

        return keyboard_dict

    def _build_middle_keyboard(self):
        keyboard_dict = dict()

        keyboard_dict[1] = self.first_page_label.format(1)
        keyboard_dict[self.current_page - 1] = self.previous_page_label.format(self.current_page - 1)
        keyboard_dict[self.current_page] = self.current_page
        keyboard_dict[self.current_page + 1] = self.next_page_label.format(self.current_page + 1)
        keyboard_dict[self.page_count] = self.last_page_label.format(self.page_count)

        return keyboard_dict

    def _to_button_array(self, keyboard_dict: dict[int, str | int]) -> list[dict[str, str]]:
        keyboard: list[InlineKeyboardButton] = list()

        keys = list(keyboard_dict.keys())
        keys.sort()

        for key in keys:
            keyboard.append(
                InlineKeyboardButton(
                    text=str(keyboard_dict[key]),
                    callback_data=self.data_pattern.format(page=key),
                )
            )
        return _buttons_to_dict(keyboard)

    @property
    def keyboard(self) -> list[dict[str, str]]:
        if not self._keyboard:
            self._build()

        return self._keyboard

    @property
    def markup(self) -> str | None:
        """InlineKeyboardMarkup"""
        keyboards = list()

        keyboards.extend(self._keyboard_before)
        keyboards.append(self.keyboard)
        keyboards.extend(self._keyboard_after)

        keyboards = list(filter(bool, keyboards))
        if not keyboards:
            return None

        return json.dumps({'inline_keyboard': keyboards})

    def __str__(self):
        if not self._keyboard:
            self._build()

        return ' '.join(
            b['text'] for b in self._keyboard
        )

    def add_before(self, *inline_buttons: InlineKeyboardButton):
        """
        Add buttons as line above pagination buttons.

        Args:
            inline_buttons (:object:`iterable`): List of object with attributes `text` and `callback_data`.

        Returns:
            None
        """
        self._keyboard_before.append(
            _buttons_to_dict(inline_buttons)
        )

    def add_after(self, *inline_buttons: InlineKeyboardButton):
        """
        Add buttons as line under pagination buttons.

        Args:
            inline_buttons (:object:`iterable`): List of object with attributes 'text' and 'callback_data'.

        Returns:
            None
        """
        self._keyboard_after.append(
            _buttons_to_dict(inline_buttons)
        )
