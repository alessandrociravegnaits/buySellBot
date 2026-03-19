"""Tastiere Telegram per il bot."""

from __future__ import annotations

from telegram import ReplyKeyboardMarkup

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
	[
		["Stato Binance", "Aiuto"],
		["Annulla"],
	],
	resize_keyboard=True,
)
